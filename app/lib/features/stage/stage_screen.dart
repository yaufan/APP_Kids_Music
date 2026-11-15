import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';
import '../parent/parent_gate.dart';
import '../record/record_screen.dart' show songNotes;

/// The stage (home): the night stage with the band on it, six big glowing
/// buttons (one per toy), the parent's lock at the top left and the little
/// sun at the top right that turns into a moon as the play time runs out.
/// Now and then a balloon floats by (tap: 「啵」) or the spotlight changes
/// colour. The tapes of the child's songs play them again.
class StageScreen extends ConsumerStatefulWidget {
  const StageScreen({super.key});

  static const balloonEvery = Duration(seconds: 25);
  static const lightEvery = Duration(seconds: 30);

  @override
  ConsumerState<StageScreen> createState() => _StageScreenState();
}

class _StageScreenState extends ConsumerState<StageScreen> with SingleTickerProviderStateMixin {
  late final Sounds _sounds;
  late final AnimationController _balloon = AnimationController(vsync: this, duration: const Duration(seconds: 9));
  Timer? _happen;
  Timer? _tick;
  var _balloonColour = 0;
  var _popped = 0;
  var _hops = 0;
  var _tint = 0;
  String? _say;

  static const _tints = [Color(0xFFFFF4C8), Color(0xFFFFC2E2), Color(0xFFC2F0FF), Color(0xFFD2FFC8)];

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, Music.stage);
    _happen = Timer.periodic(StageScreen.balloonEvery, (t) => _happening(t.tick));
    _tick = Timer.periodic(const Duration(seconds: 5), (_) {
      if (mounted) setState(() {});
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final once = ref.read(onceProvider);
      if (once.add('welcome')) speak(ref, Strings.welcome);
    });
  }

  @override
  void dispose() {
    _happen?.cancel();
    _tick?.cancel();
    _balloon.dispose();
    _sounds.release(this);
    super.dispose();
  }

  /// Something small happens now and then: a balloon, or a new light.
  void _happening(int n) {
    if (!mounted) return;
    if (n.isOdd) {
      setState(() => _balloonColour = ref.read(randomProvider).nextInt(3));
      _balloon.forward(from: 0);
    } else {
      _sounds.play('light');
      setState(() => _tint = (_tint + 1) % _tints.length);
    }
  }

  void _pop() {
    _sounds.play('pop');
    _balloon.stop();
    _balloon.value = 0;
    speak(ref, '啵！');
    setState(() => _popped++);
  }

  Future<void> _parent() async {
    if (!await showParentGate(context) || !mounted) return;
    context.go('/parent');
  }

  void _open(Toy t) {
    final s = ref.read(gameProvider).settings;
    if (!s.opens(t)) {
      _sounds.play('lock');
      speak(ref, Strings.locked);
      setState(() => _say = Strings.locked);
      return;
    }
    _sounds.play('open');
    ref.read(gameProvider.notifier).change((g) => g.opened(t, ref.read(clockProvider)()));
    context.go('/toy/${t.name}');
  }

  Widget _top() {
    final g = ref.watch(gameProvider);
    final start = ref.watch(sessionStartProvider);
    final used = ref.read(clockProvider)().difference(start).inSeconds / 60;
    final left = math.max(0, g.settings.minutes - used.floor());
    final frac = (used / g.settings.minutes).clamp(0.0, 1.0);
    return Padding(
      padding: const EdgeInsets.fromLTRB(14, 8, 14, 0),
      child: Row(children: [
        Semantics(
          container: true,
          button: true,
          label: Strings.parent,
          excludeSemantics: true,
          onTap: _parent,
          child: Pressable(
            onTap: _parent,
            child: Container(
              padding: const EdgeInsets.fromLTRB(8, 6, 14, 6),
              decoration: BoxDecoration(borderRadius: BorderRadius.circular(22), border: Border.all(color: Neon.lavender.withValues(alpha: 0.7), width: 2)),
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                SizedBox(width: 24, height: 24, child: Art(ArtPath.ui('lock'))),
                const SizedBox(width: 4),
                const Text(Strings.parent, style: TextStyle(fontSize: 15, color: Neon.inkSoft)),
              ]),
            ),
          ),
        ),
        const Spacer(),
        Semantics(
          label: Strings.timeLeft(left),
          child: Container(
            width: 108,
            height: 38,
            padding: const EdgeInsets.symmetric(horizontal: 6),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(20), border: Border.all(color: Neon.lavender.withValues(alpha: 0.7), width: 2)),
            child: LayoutBuilder(builder: (_, box) {
              final x = frac * (box.maxWidth - 28);
              return Stack(alignment: Alignment.centerLeft, children: [
                Positioned(right: 0, width: 26, height: 26, child: Opacity(opacity: 0.35 + 0.65 * frac, child: Art(ArtPath.ui('moon')))),
                Positioned(left: x, width: 28, height: 28, child: Opacity(opacity: 1 - 0.6 * frac, child: Art(ArtPath.ui('sun')))),
              ]);
            }),
          ),
        ),
      ]),
    );
  }

  Widget _band(double h, double w) {
    final on = ref.watch(bandProvider).onStage.toList();
    final show = on.isEmpty ? const [Animal.bear, Animal.frog, Animal.bird] : on.take(4).toList();
    final size = math.min(h * 0.62, (w - 40) / show.length);
    return SizedBox(
      height: h,
      child: Stack(children: [
        Positioned(left: 8, right: 8, bottom: 0, height: h * 0.55, child: Art(ArtPath.stage('floor'), fit: BoxFit.fill)),
        Positioned.fill(
          bottom: h * 0.22,
          child: Row(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
            for (var i = 0; i < show.length; i++)
              Semantics(
                label: show[i].zh,
                button: true,
                onTap: () => _hop(show[i]),
                child: GestureDetector(
                  onTap: () => _hop(show[i]),
                  child: Bob(phase: i * 0.3, amount: 5, child: Hop(trigger: _hops, height: 10, child: SizedBox(width: size, height: size, child: Art(show[i].art(Pose.sing))))),
                ),
              ),
          ]),
        ),
      ]),
    );
  }

  void _hop(Animal a) {
    _sounds.play(a.call);
    speak(ref, a.zh, en: a.en);
    setState(() => _hops++);
  }

  @override
  Widget build(BuildContext context) {
    final g = ref.watch(gameProvider);
    final s = g.settings;
    final toys = [for (final t in Toy.values) if (s.shows(t)) t];
    return Scaffold(
      backgroundColor: Neon.top,
      body: StageBackdrop(
        spot: true,
        tint: _tints[_tint],
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 560),
              child: LayoutBuilder(builder: (_, box) {
                final h = box.maxHeight;
                final button = math.min(84.0, math.min(box.maxWidth / 4.8, h * 0.11));
                return Stack(children: [
                  Column(children: [
                    _top(),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 26, vertical: 6),
                      decoration: BoxDecoration(
                        color: Neon.glass.withValues(alpha: 0.6),
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(color: Neon.pink, width: 3),
                        boxShadow: [BoxShadow(color: Neon.pink.withValues(alpha: 0.4), blurRadius: 18, spreadRadius: 1)],
                      ),
                      child: const Text(Strings.appName, style: TextStyle(fontSize: 34, color: Neon.ink, fontWeight: FontWeight.w700, letterSpacing: 4)),
                    ),
                    Expanded(child: Align(alignment: Alignment.bottomCenter, child: _band(math.min(h * 0.3, 220), box.maxWidth))),
                    if (_say != null) Padding(padding: const EdgeInsets.only(top: 6), child: SayBubble(text: _say!, size: 16)),
                    if (g.songs.isNotEmpty && s.opens(Toy.record))
                      SizedBox(
                        height: 46,
                        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                          for (var i = 0; i < math.min(4, g.songs.length); i++)
                            Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 4),
                              child: Semantics(
                                key: ValueKey('stage-tape-$i'),
                                button: true,
                                label: Strings.songN(i + 1),
                                excludeSemantics: true,
                                onTap: () => _sounds.playSong(songNotes(g.songs[i])),
                                child: Pressable(onTap: () => _sounds.playSong(songNotes(g.songs[i])), sound: null, child: SizedBox(width: 60, height: 40, child: Art(ArtPath.tape(g.songs[i].colour)))),
                              ),
                            ),
                        ]),
                      ),
                    const SizedBox(height: 12),
                    Wrap(alignment: WrapAlignment.center, spacing: button * 0.2, runSpacing: 10, children: [
                      for (final t in toys)
                        SizedBox(
                          width: button * 1.35,
                          child: NeonButton(
                            key: ValueKey('toy-${t.name}'),
                            label: t.zh,
                            caption: t.zh,
                            art: t.art,
                            colour: Neon.toys[t.index],
                            size: button,
                            sound: null,
                            locked: !s.opens(t),
                            onTap: () => _open(t),
                          ),
                        ),
                    ]),
                    const SizedBox(height: 18),
                  ]),
                  AnimatedBuilder(
                    animation: _balloon,
                    builder: (_, _) {
                      final v = _balloon.value;
                      if (v == 0 || v == 1) return const SizedBox.shrink();
                      return Positioned(
                        left: -80 + v * (box.maxWidth + 160),
                        top: h * 0.32 - math.sin(v * math.pi * 3) * 20,
                        width: 70,
                        height: 98,
                        child: Semantics(
                          key: const ValueKey('balloon'),
                          button: true,
                          label: Strings.balloon,
                          onTap: _pop,
                          child: GestureDetector(onTap: _pop, child: Art(ArtPath.balloon(_balloonColour))),
                        ),
                      );
                    },
                  ),
                  Positioned(left: box.maxWidth / 2, top: h * 0.3, child: NoteBurst(trigger: _popped, colour: _balloonColour, size: 30)),
                ]);
              }),
            ),
          ),
        ),
      ),
    );
  }
}
