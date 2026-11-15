import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';

/// 高低快慢 (docs/design.md, the curriculum's three pairs):
/// - 高低: drag the bird up and down a glowing staircase; each step is one
///   note of the scale, higher up the stairs, higher the tweet.
/// - 快慢 (大): a snail-to-rabbit slider; the bird sings its song slow or fast.
/// - 大小聲 (大): the elephant is loud, the mouse is soft.
/// Every move is said out loud: 「高～」「低～」「快！」「慢～～」.
class HighLowScreen extends ConsumerStatefulWidget {
  const HighLowScreen({super.key});

  @override
  ConsumerState<HighLowScreen> createState() => _HighLowScreenState();
}

class _HighLowScreenState extends ConsumerState<HighLowScreen> {
  late final Sounds _sounds;
  final _stairsKey = GlobalKey();
  final _speedKey = GlobalKey();
  var _step = 0;
  var _tempo = Tempo.normal;
  var _hops = 0;
  var _say = Strings.highlowHint;
  bool? _wentUp;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, null);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) speak(ref, '${Toy.highlow.zh}！${Strings.highlowHint}');
    });
  }

  @override
  void dispose() {
    _sounds.release(this);
    super.dispose();
  }

  int? _stepAt(Offset global) {
    final box = _stairsKey.currentContext?.findRenderObject() as RenderBox?;
    if (box == null) return null;
    final p = box.globalToLocal(global);
    if (p.dy < -40 || p.dy > box.size.height + 20) return null;
    return (p.dx / box.size.width * 5).floor().clamp(0, 4);
  }

  void _to(int step) {
    if (step == _step) return;
    final up = step > _step;
    _sounds.play('stair_$step');
    final say = up ? Strings.high : Strings.low;
    setState(() {
      _step = step;
      _hops++;
      _say = say;
    });
    // Said when the bird turns round (not on every step of one climb).
    if (_wentUp != up) {
      _wentUp = up;
      speak(ref, say);
    }
  }

  void _stairs(Offset global) {
    final s = _stepAt(global);
    if (s != null) _to(s);
  }

  void _speed(Offset global) {
    final box = _speedKey.currentContext?.findRenderObject() as RenderBox?;
    if (box == null) return;
    final x = box.globalToLocal(global).dx / box.size.width;
    final t = Tempo.values[(x * 3).floor().clamp(0, 2)];
    if (t == _tempo) return;
    _setTempo(t);
  }

  void _setTempo(Tempo t) {
    final say = t.index > _tempo.index ? Strings.fast : Strings.slow;
    setState(() {
      _tempo = t;
      _say = say;
    });
    _sounds.play(Animal.bird.loop(t), volume: 0.8);
    speak(ref, say);
  }

  void _volume(bool loud) {
    _sounds.play(loud ? 'loud' : 'soft');
    final say = loud ? Strings.loud : Strings.soft;
    setState(() => _say = say);
    speak(ref, say);
  }

  Widget _stairsView() => Listener(
        behavior: HitTestBehavior.opaque,
        onPointerDown: (e) => _stairs(e.position),
        onPointerMove: (e) => _stairs(e.position),
        child: LayoutBuilder(builder: (_, box) {
          final w = box.maxWidth / 5;
          final h = box.maxHeight;
          // The bar art is 80 x 400; a step's top is 300 - 70 i of 400 from the top.
          final barH = h - w * 0.75;
          final barW = barH * 80 / 400;
          final top = h - barH + barH * (300 - _step * 70) / 400;
          return Stack(key: _stairsKey, clipBehavior: Clip.none, children: [
            Positioned.fill(child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
              for (var i = 0; i < 5; i++)
                Expanded(
                  child: Semantics(
                    key: ValueKey('step-$i'),
                    container: true,
                    button: true,
                    label: Strings.stepN(i),
                    excludeSemantics: true,
                    onTap: () => _to(i),
                    child: SizedBox(height: barH, child: Center(child: SizedBox(width: barW * 1.6, child: Art(ArtPath.step(i, lit: i == _step), fit: BoxFit.fill)))),
                  ),
                ),
            ])),
            AnimatedPositioned(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              left: w * _step + w / 2 - w * 0.5,
              top: top - w * 0.95,
              width: w,
              height: w,
              child: IgnorePointer(child: Hop(trigger: _hops, height: 12, child: Art(Animal.bird.art(_hops == 0 ? Pose.idle : Pose.sing), key: const ValueKey('stair-bird')))),
            ),
          ]);
        }),
      );

  Widget _panel(String title, Widget child) => Container(
        margin: const EdgeInsets.fromLTRB(16, 6, 16, 0),
        padding: const EdgeInsets.fromLTRB(14, 6, 14, 8),
        decoration: BoxDecoration(
          color: Neon.glass.withValues(alpha: 0.7),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Neon.lavender.withValues(alpha: 0.7), width: 2),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 15, color: Neon.inkSoft, fontWeight: FontWeight.w700)),
          child,
        ]),
      );

  Widget _speedView() => Row(children: [
        SizedBox(width: 44, height: 44, child: Semantics(label: Strings.snail, button: true, onTap: () => _setTempo(Tempo.slow), child: Art(ArtPath.ui('snail')))),
        Expanded(
          child: Listener(
            behavior: HitTestBehavior.opaque,
            onPointerDown: (e) => _speed(e.position),
            onPointerMove: (e) => _speed(e.position),
            child: SizedBox(
              key: _speedKey,
              height: 44,
              child: LayoutBuilder(builder: (_, box) {
                final x = (_tempo.index + 0.5) / 3 * box.maxWidth;
                return Stack(clipBehavior: Clip.none, alignment: Alignment.centerLeft, children: [
                  Container(
                    height: 10,
                    margin: const EdgeInsets.symmetric(horizontal: 8),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [Neon.green, Neon.yellow, Neon.pink]),
                      borderRadius: BorderRadius.circular(5),
                      boxShadow: [BoxShadow(color: Neon.yellow.withValues(alpha: 0.3), blurRadius: 8)],
                    ),
                  ),
                  AnimatedPositioned(
                    duration: const Duration(milliseconds: 150),
                    left: x - 17,
                    child: Container(
                      key: const ValueKey('speed-knob'),
                      width: 34,
                      height: 34,
                      decoration: BoxDecoration(shape: BoxShape.circle, color: Neon.glass, border: Border.all(color: Neon.ink, width: 3), boxShadow: [BoxShadow(color: Neon.ink.withValues(alpha: 0.4), blurRadius: 10)]),
                    ),
                  ),
                ]);
              }),
            ),
          ),
        ),
        SizedBox(width: 44, height: 44, child: Semantics(label: Strings.rabbit, button: true, onTap: () => _setTempo(Tempo.fast), child: Art(ArtPath.ui('rabbit')))),
      ]);

  @override
  Widget build(BuildContext context) {
    final big = ref.watch(gameProvider.select((g) => g.settings.level)) == Level.big;
    return ToyPage(
      title: Toy.highlow.zh,
      child: Column(children: [
        const SizedBox(height: 4),
        SayBubble(text: _say, size: 17, onTap: () => speak(ref, _say)),
        Expanded(child: Padding(padding: const EdgeInsets.fromLTRB(24, 70, 24, 6), child: _stairsView())),
        if (big) ...[
          _panel(Strings.speed, _speedView()),
          _panel(
            Strings.volume,
            Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
              NeonButton(key: const ValueKey('loud'), label: Strings.elephant, art: Animal.elephant.art(Pose.sing), colour: Neon.sky, size: 66, sound: null, padding: 0.06, onTap: () => _volume(true)),
              NeonButton(key: const ValueKey('soft'), label: Strings.mouse, art: ArtPath.ui('mouse'), colour: Neon.lavender, size: 50, sound: null, padding: 0.1, onTap: () => _volume(false)),
            ]),
          ),
        ],
      ]),
    );
  }
}
