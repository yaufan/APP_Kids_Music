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

/// The play time is up (docs/design.md 「每次玩多久」): the music goes soft,
/// the neon lights go out one by one (the animals wave good night), the
/// curtains close, and the child is sent to do it for real: 「換你去做了！」
/// Only a parent (through the gate) or an hour's wait lets play go on.
class RestScreen extends ConsumerStatefulWidget {
  const RestScreen({super.key});

  /// How many lights go out, one after another.
  static const lights = 7;

  @override
  ConsumerState<RestScreen> createState() => _RestScreenState();
}

class _RestScreenState extends ConsumerState<RestScreen> with SingleTickerProviderStateMixin {
  late final Sounds _sounds;
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(seconds: 9))..addListener(_onTick);
  var _out = 0;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, Music.rest);
    _c.forward();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      speak(ref, '${Strings.goodnight}${Strings.restTitle}${Strings.restLine.replaceAll('\n', '')}');
    });
  }

  @override
  void dispose() {
    _c.dispose();
    _sounds.release(this);
    super.dispose();
  }

  /// The first 70 % of the time: one light after another goes out.
  double _light(int i) => (1 - ((_c.value / 0.7) * RestScreen.lights - i)).clamp(0.0, 1.0);

  void _onTick() {
    final out = ((_c.value / 0.7) * RestScreen.lights).floor().clamp(0, RestScreen.lights);
    if (out != _out) {
      _out = out;
      _sounds.play(out == RestScreen.lights ? 'night' : 'lights_off');
    }
  }

  Future<void> _parent() async {
    if (!await showParentGate(context) || !mounted) return;
    ParentPass.take(); // play goes on; the pass to parent mode is not needed
    ref.read(gameProvider.notifier).change((g) => g.playOn());
    ref.read(sessionStartProvider.notifier).restart();
    context.go('/');
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Neon.night,
        body: AnimatedBuilder(
          animation: _c,
          builder: (_, _) {
            final closed = ((_c.value - 0.7) / 0.3).clamp(0.0, 1.0);
            return LayoutBuilder(builder: (_, box) {
              final w = box.maxWidth;
              return Stack(children: [
                Positioned.fill(child: Art(ArtPath.stage('bg'), fit: BoxFit.cover)),
                Positioned.fill(child: ColoredBox(color: Neon.night.withValues(alpha: 0.35 + 0.4 * (1 - _light(RestScreen.lights - 1))))),
                Positioned(left: 0, right: 0, top: 0, height: 64, child: Opacity(opacity: _light(0), child: Art(ArtPath.stage('valance'), fit: BoxFit.fill))),
                Positioned(left: 0, right: 0, bottom: box.maxHeight * 0.18, height: 130, child: Opacity(opacity: 0.2 + 0.8 * _light(1), child: Art(ArtPath.stage('floor'), fit: BoxFit.fill))),
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: box.maxHeight * 0.18 + 50,
                  height: 140,
                  child: Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                    for (final (i, a) in [(2, Animal.bear), (3, Animal.frog), (4, Animal.bird)])
                      Opacity(opacity: 0.25 + 0.75 * _light(i), child: SizedBox(width: 120, height: 120, child: Art(a.art(_light(i) > 0.5 ? Pose.idle : Pose.sing)))),
                  ]),
                ),
                // The curtains close.
                Positioned(left: -w * 0.5 + closed * w * 0.5, top: 0, bottom: 0, width: w * 0.52, child: ColoredBox(color: const Color(0xFF3A1E4E).withValues(alpha: 0.85 * closed))),
                Positioned(right: -w * 0.5 + closed * w * 0.5, top: 0, bottom: 0, width: w * 0.52, child: ColoredBox(color: const Color(0xFF3A1E4E).withValues(alpha: 0.85 * closed))),
                Positioned(left: -w * 0.5 + closed * w * 0.5, top: 0, bottom: 0, width: w * 0.56, child: Opacity(opacity: 0.25 + 0.75 * _light(5), child: Art(ArtPath.stage('curtain_left'), fit: BoxFit.fill))),
                Positioned(right: -w * 0.5 + closed * w * 0.5, top: 0, bottom: 0, width: w * 0.56, child: Opacity(opacity: 0.25 + 0.75 * _light(6), child: Art(ArtPath.stage('curtain_right'), fit: BoxFit.fill))),
                SafeArea(
                  child: Column(children: [
                    const SizedBox(height: 70),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 28),
                      child: Container(
                        padding: const EdgeInsets.fromLTRB(22, 18, 22, 18),
                        decoration: BoxDecoration(
                          color: Neon.glass.withValues(alpha: 0.85),
                          borderRadius: BorderRadius.circular(28),
                          border: Border.all(color: Neon.yellow.withValues(alpha: 0.8), width: 2.4),
                          boxShadow: [BoxShadow(color: Neon.yellow.withValues(alpha: 0.2), blurRadius: 20)],
                        ),
                        child: const Column(mainAxisSize: MainAxisSize.min, children: [
                          Text(Strings.restTitle, style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700, color: Neon.ink)),
                          SizedBox(height: 10),
                          Text(Strings.restLine, textAlign: TextAlign.center, style: TextStyle(fontSize: 21, height: 1.5, color: Neon.ink)),
                        ]),
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(width: 64, height: 64, child: Art(ArtPath.ui('moon'))),
                    const Spacer(),
                    Align(
                      alignment: Alignment.bottomRight,
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(0, 0, 18, 16),
                        child: Semantics(
                          container: true,
                          button: true,
                          label: Strings.parent,
                          excludeSemantics: true,
                          onTap: _parent,
                          child: GestureDetector(
                            behavior: HitTestBehavior.opaque,
                            onTap: _parent,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                              decoration: BoxDecoration(borderRadius: BorderRadius.circular(22), border: Border.all(color: Neon.lavender.withValues(alpha: 0.6), width: 2)),
                              child: Row(mainAxisSize: MainAxisSize.min, children: [
                                SizedBox(width: 22, height: 22, child: Art(ArtPath.ui('lock'))),
                                const SizedBox(width: 6),
                                const Text(Strings.parent, style: TextStyle(fontSize: 16, color: Neon.inkSoft)),
                              ]),
                            ),
                          ),
                        ),
                      ),
                    ),
                  ]),
                ),
              ]);
            });
          },
        ),
      );
}
