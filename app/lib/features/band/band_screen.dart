import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/game.dart';
import '../../core/music.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';
import '../tap/keys_view.dart';

/// 動物樂團 (docs/design.md): drag a glowing animal onto a spot on the stage and
/// it sings its two bars over and over, on the beat with the others (it
/// joins at the next bar line). Drag it off and it stops. Tap an animal on
/// the stage and it jumps; 大 can hold one to 「噓」 it. A tap on an animal
/// in the row below also sends it up (for little ones who cannot drag yet).
/// The snail/rabbit button changes the speed for everyone; the xylophone
/// row at the bottom plays along.
class BandScreen extends ConsumerStatefulWidget {
  const BandScreen({super.key});

  static int spotsFor(Level l) => l == Level.small ? 4 : 6;

  @override
  ConsumerState<BandScreen> createState() => _BandScreenState();
}

class _Drag {
  _Drag(this.animal, this.fromSpot, this.pointer, this.start) : at = start;

  final Animal animal;

  /// The spot it was lifted from, or null from the row below.
  final int? fromSpot;
  final int pointer;
  final Offset start;
  Offset at;
  bool moved = false;
  bool held = false;
}

class _BandScreenState extends ConsumerState<BandScreen> with SingleTickerProviderStateMixin {
  late final Sounds _sounds;
  final _stageKey = GlobalKey();
  final _bodyKey = GlobalKey();
  final _trayKeys = <Animal, GlobalKey>{};
  final _hops = <Animal, int>{};
  late final Ticker _ticker;
  Duration _elapsed = Duration.zero;
  _Drag? _drag;
  Timer? _hold;
  Timer? _cheer;
  var _cheering = false;
  String _say = '';

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, null);
    _ticker = createTicker((d) => setState(() => _elapsed = d))..start();
    final s = ref.read(gameProvider).settings;
    _say = s.level == Level.small ? Strings.bandHint : Strings.bandHintBig;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      // Only as many spots as the level has, only animals that may play.
      ref.read(bandProvider.notifier).fit(BandScreen.spotsFor(s.level), Animal.available(full: s.full));
      final band = ref.read(bandProvider);
      _sounds.bandStart(band.tempo, Animal.available(full: s.full), band.singing);
      speak(ref, '${Toy.band.zh}！$_say');
    });
  }

  @override
  void dispose() {
    _ticker.dispose();
    _hold?.cancel();
    _cheer?.cancel();
    _sounds.bandStop();
    _sounds.release(this);
    super.dispose();
  }

  // ---- the music
  void _sing() {
    final band = ref.read(bandProvider);
    _sounds.bandSing(band.singing);
    final spots = BandScreen.spotsFor(ref.read(gameProvider).settings.level);
    if (band.spots.length == spots && !_cheering) {
      _sounds.play('applause');
      speak(ref, Strings.encore);
      setState(() {
        _cheering = true;
        _say = Strings.full;
      });
      _cheer?.cancel();
      _cheer = Timer(const Duration(milliseconds: 2600), () {
        if (mounted) setState(() => _cheering = false);
      });
    }
  }

  void _put(Animal a, int spot) {
    final was = ref.read(bandProvider).onStage.contains(a);
    ref.read(bandProvider.notifier).put(a, spot);
    _sounds.play('join');
    if (!was) {
      speak(ref, Strings.joins(a), en: a.en);
      setState(() => _say = Strings.joins(a));
    }
    _hop(a);
    _sing();
  }

  void _remove(Animal a) {
    ref.read(bandProvider.notifier).remove(a);
    _sounds.play('leave');
    _sing();
  }

  void _hop(Animal a) => setState(() => _hops[a] = (_hops[a] ?? 0) + 1);

  void _tempo() {
    final band = ref.read(bandProvider);
    final t = band.tempo.next;
    ref.read(bandProvider.notifier).tempo(t);
    final s = ref.read(gameProvider).settings;
    _sounds.bandStart(t, Animal.available(full: s.full), ref.read(bandProvider).singing);
    speak(ref, Strings.tempoIs(t));
    setState(() => _say = Strings.tempoIs(t));
  }

  void _shush(Animal a) {
    ref.read(bandProvider.notifier).shush(a);
    final now = ref.read(bandProvider).shushed.contains(a);
    _sounds.play(now ? 'shh' : 'join');
    final line = now ? Strings.shushed(a) : Strings.sings(a);
    speak(ref, line);
    setState(() => _say = line);
    _sounds.bandSing(ref.read(bandProvider).singing);
  }

  // ---- where things are
  ({Offset centre, double size}) _spot(int i, Size box, int count) {
    final cols = count ~/ 2;
    final row = i ~/ cols, col = i % cols;
    final size = math.min(box.width / cols * 0.92, box.height * 0.44);
    final x = (col + 0.5) / cols * box.width + (row == 0 ? 0 : 0);
    final y = row == 0 ? box.height * 0.3 : box.height * 0.72;
    return (centre: Offset(x, y), size: size);
  }

  int? _spotAt(Offset global) {
    final box = _stageKey.currentContext?.findRenderObject() as RenderBox?;
    if (box == null) return null;
    final local = box.globalToLocal(global);
    final count = BandScreen.spotsFor(ref.read(gameProvider).settings.level);
    int? best;
    var bestD = double.infinity;
    for (var i = 0; i < count; i++) {
      final s = _spot(i, box.size, count);
      final d = (s.centre - local).distance;
      if (d < s.size * 0.62 && d < bestD) {
        best = i;
        bestD = d;
      }
    }
    return best;
  }

  Animal? _trayAt(Offset global) {
    for (final e in _trayKeys.entries) {
      final box = e.value.currentContext?.findRenderObject() as RenderBox?;
      if (box == null || !box.hasSize) continue;
      if ((Offset.zero & box.size).contains(box.globalToLocal(global))) return e.key;
    }
    return null;
  }

  // ---- fingers
  void _down(PointerDownEvent e) {
    if (_drag != null) return;
    final s = ref.read(gameProvider).settings;
    final band = ref.read(bandProvider);
    final spot = _spotAt(e.position);
    if (spot != null && band.spots[spot] != null) {
      final a = band.spots[spot]!;
      final d = _drag = _Drag(a, spot, e.pointer, e.position);
      _hold?.cancel();
      if (s.level == Level.big) {
        _hold = Timer(const Duration(milliseconds: 550), () {
          if (_drag == d && !d.moved && mounted) {
            d.held = true;
            _shush(a);
          }
        });
      }
      return;
    }
    final a = _trayAt(e.position);
    if (a == null) return;
    if (!Animal.available(full: s.full).contains(a)) {
      _sounds.play('lock');
      speak(ref, Strings.lockedAnimal);
      setState(() => _say = Strings.lockedAnimal);
      return;
    }
    setState(() => _drag = _Drag(a, null, e.pointer, e.position));
  }

  void _move(PointerMoveEvent e) {
    final d = _drag;
    if (d == null || d.pointer != e.pointer) return;
    setState(() {
      d.at = e.position;
      if ((d.at - d.start).distance > 12) d.moved = true;
    });
  }

  void _up(PointerEvent e, {bool cancel = false}) {
    final d = _drag;
    if (d == null || d.pointer != e.pointer) return;
    _hold?.cancel();
    setState(() => _drag = null);
    if (cancel || d.held) return;
    final band = ref.read(bandProvider);
    if (!d.moved) {
      if (d.fromSpot != null) {
        _sounds.play(d.animal.call);
        speak(ref, d.animal.zh, en: d.animal.en);
        _hop(d.animal);
      } else if (!band.onStage.contains(d.animal)) {
        // A tap on the row below: up to the first free spot.
        final count = BandScreen.spotsFor(ref.read(gameProvider).settings.level);
        final free = [for (var i = 0; i < count; i++) if (band.spots[i] == null) i];
        if (free.isEmpty) {
          _sounds.play(d.animal.call);
        } else {
          _put(d.animal, free.first);
        }
      } else {
        _sounds.play(d.animal.call);
        _hop(d.animal);
      }
      return;
    }
    final spot = _spotAt(e.position);
    if (spot != null) {
      _put(d.animal, spot);
    } else if (d.fromSpot != null) {
      _remove(d.animal);
    }
  }

  // ---- drawing
  Widget _animal(Animal a, double size, {required bool singing, required bool shushed}) {
    final clock = MusicClock.of(ref.read(bandProvider).tempo);
    final t = _sounds.bandTime ?? _elapsed;
    final beats = clock.beatsAt(t);
    final bob = singing ? (math.sin(beats * math.pi).abs() * size * 0.06) : 0.0;
    final pose = shushed ? Pose.frozen : (singing ? Pose.sing : Pose.idle);
    return Transform.translate(
      offset: Offset(0, -bob),
      child: Opacity(
        opacity: shushed ? 0.55 : 1,
        child: Hop(trigger: _hops[a] ?? 0, height: size * 0.2, child: SizedBox(width: size, height: size, child: Art(a.art(pose)))),
      ),
    );
  }

  Widget _stage(int count) => LayoutBuilder(builder: (_, box) {
        final size = box.biggest;
        final band = ref.watch(bandProvider);
        return Stack(key: _stageKey, clipBehavior: Clip.none, children: [
          Positioned(left: 0, right: 0, bottom: size.height * 0.02, height: size.height * 0.62, child: Art(ArtPath.stage('floor'), fit: BoxFit.fill)),
          for (var i = 0; i < count; i++) ...[
            () {
              final s = _spot(i, size, count);
              final a = band.spots[i];
              final lifted = _drag?.fromSpot == i && (_drag!.moved);
              return Positioned(
                left: s.centre.dx - s.size / 2,
                top: s.centre.dy - s.size / 2,
                width: s.size,
                height: s.size,
                child: Semantics(
                  key: ValueKey('spot-$i'),
                  container: true,
                  label: a == null ? Strings.spot(i) : Strings.onStage(a),
                  child: Stack(clipBehavior: Clip.none, children: [
                    Positioned(left: 0, right: 0, bottom: -s.size * 0.06, height: s.size * 0.3, child: Art(ArtPath.ui('slot'), fit: BoxFit.fill)),
                    if (a != null && !lifted)
                      Positioned.fill(
                        child: _animal(a, s.size, singing: !band.shushed.contains(a), shushed: band.shushed.contains(a)),
                      ),
                    if (a != null && band.shushed.contains(a))
                      Positioned(right: 0, top: 0, width: s.size * 0.3, height: s.size * 0.3, child: Art(ArtPath.ui('mute'))),
                  ]),
                ),
              );
            }(),
          ],
        ]);
      });

  Widget _tray(Settings s) {
    final band = ref.watch(bandProvider);
    final all = Animal.values;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: Neon.glass.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: Neon.lavender.withValues(alpha: 0.8), width: 2.2),
        boxShadow: [BoxShadow(color: Neon.lavender.withValues(alpha: 0.2), blurRadius: 14)],
      ),
      child: LayoutBuilder(builder: (_, box) {
        final cell = math.min(box.maxWidth / 5, 74.0);
        Widget one(Animal a) {
          final ok = Animal.available(full: s.full).contains(a);
          final up = band.onStage.contains(a);
          return Semantics(
            key: ValueKey('tray-${a.name}'),
            container: true,
            button: true,
            label: Strings.tray(a),
            excludeSemantics: true,
            child: KeyedSubtree(
              key: _trayKeys.putIfAbsent(a, GlobalKey.new),
              child: SizedBox(
                width: cell,
                height: cell,
                child: Stack(children: [
                  Positioned.fill(child: Opacity(opacity: !ok ? 0.3 : (up ? 0.35 : 1), child: Art(a.art(Pose.idle)))),
                  if (!ok) Positioned(right: 2, bottom: 2, width: cell * 0.36, height: cell * 0.36, child: Art(ArtPath.ui('lock'))),
                ]),
              ),
            ),
          );
        }

        return Column(mainAxisSize: MainAxisSize.min, children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [for (final a in all.take(5)) one(a)]),
          Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [for (final a in all.skip(5)) one(a)]),
        ]);
      }),
    );
  }

  @override
  Widget build(BuildContext context) {
    final s = ref.watch(gameProvider.select((g) => g.settings));
    final band = ref.watch(bandProvider);
    final count = BandScreen.spotsFor(s.level);
    final d = _drag;
    final tempoArt = band.tempo == Tempo.slow ? 'snail' : 'rabbit';
    return ToyPage(
      title: Toy.band.zh,
      action: NeonButton(
        key: const ValueKey('tempo'),
        label: '${Strings.tempo} ${band.tempo.zh}',
        caption: band.tempo.zh,
        art: ArtPath.ui(tempoArt),
        colour: band.tempo == Tempo.slow ? Neon.green : (band.tempo == Tempo.fast ? Neon.pink : Neon.lavender),
        size: 50,
        sound: null,
        onTap: _tempo,
      ),
      child: Listener(
        key: _bodyKey,
        behavior: HitTestBehavior.translucent,
        onPointerDown: _down,
        onPointerMove: _move,
        onPointerUp: _up,
        onPointerCancel: (e) => _up(e, cancel: true),
        child: Stack(clipBehavior: Clip.none, children: [
          Column(children: [
            Expanded(flex: 10, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: _stage(count))),
            Padding(padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6), child: SayBubble(text: _say, size: 16)),
            Padding(padding: const EdgeInsets.symmetric(horizontal: 12), child: _tray(s)),
            const SizedBox(height: 8),
            SizedBox(height: 74, child: Padding(padding: const EdgeInsets.symmetric(horizontal: 40), child: KeysView(instrument: Instrument.xylo, count: 5, compact: true))),
          ]),
          if (_cheering)
            Positioned(left: 0, right: 0, top: 0, height: 60, child: IgnorePointer(child: Bob(amount: 6, period: const Duration(milliseconds: 500), child: Art(ArtPath.stage('audience'))))),
          if (d != null && d.moved)
            Builder(builder: (context) {
              final box = _bodyKey.currentContext?.findRenderObject() as RenderBox?;
              if (box == null) return const SizedBox.shrink();
              final p = box.globalToLocal(d.at);
              return Positioned(left: p.dx - 50, top: p.dy - 70, width: 100, height: 100, child: IgnorePointer(child: Art(d.animal.art(Pose.cheer))));
            }),
        ]),
      ),
    );
  }
}
