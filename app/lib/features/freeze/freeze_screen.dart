import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/music.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';

/// 音樂木頭人 (docs/design.md): the music plays and the animals dance; a tap
/// anywhere makes them jump higher. The music stops: the big red 「停！」 light
/// and a hand, everyone freezes. A tap now only gets a 「噓～」 (the light
/// shakes, an animal peeks); staying still until the music comes back gets a
/// cheer. No score, no penalty.
class FreezeScreen extends ConsumerStatefulWidget {
  const FreezeScreen({super.key});

  static const dancers = [Animal.bear, Animal.frog, Animal.bird, Animal.cat];

  @override
  ConsumerState<FreezeScreen> createState() => _FreezeScreenState();
}

class _FreezeScreenState extends ConsumerState<FreezeScreen> {
  late final Sounds _sounds;
  late final FreezePlan _plan;
  List<FreezePhase> _round = [];
  var _at = 0;
  FreezeKind _now = FreezeKind.play;
  Timer? _timer;
  Timer? _cheerTimer;
  var _jumps = 0;
  var _shakes = 0;
  var _tapsInStop = 0;
  var _cheer = false;
  int? _peek;
  String _say = Strings.freezeHint;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _plan = FreezePlan(ref.read(gameProvider).settings.level, ref.read(randomProvider));
    _sounds.hold(this, Music.freeze);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) speak(ref, '${Toy.freeze.zh}！${Strings.freezeHint}');
    });
    _newRound();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _cheerTimer?.cancel();
    _sounds.release(this);
    super.dispose();
  }

  void _newRound() {
    _round = _plan.round();
    _at = 0;
    _enter();
  }

  void _enter() {
    final p = _round[_at];
    final was = _now;
    setState(() => _now = p.kind);
    switch (p.kind) {
      case FreezeKind.play:
        if (was == FreezeKind.stop || was == FreezeKind.fake) {
          _sounds.hold(this, Music.freeze);
          _sounds.play('freeze_go');
        }
        if (was == FreezeKind.stop) {
          if (_tapsInStop == 0) {
            _sounds.play('cheer');
            speak(ref, Strings.still);
            setState(() {
              _cheer = true;
              _say = Strings.still;
            });
          } else {
            speak(ref, Strings.go);
            setState(() => _say = Strings.go);
          }
        }
      case FreezeKind.warn:
        speak(ref, Strings.stopSoon);
        setState(() => _say = Strings.stopSoon);
      case FreezeKind.stop:
        _sounds.hold(this, null);
        _sounds.play('freeze_stop');
        speak(ref, Strings.stop);
        setState(() {
          _tapsInStop = 0;
          _cheer = false;
          _peek = null;
          _say = Strings.stop;
        });
      case FreezeKind.fake:
        _sounds.hold(this, null);
    }
    _timer?.cancel();
    _timer = Timer(p.length, () {
      if (!mounted) return;
      if (++_at >= _round.length) {
        _round = _plan.round();
        _at = 0;
      }
      _enter();
    });
    if (p.kind == FreezeKind.play && _cheer) {
      _cheerTimer?.cancel();
      _cheerTimer = Timer(const Duration(milliseconds: 1600), () {
        if (mounted && _now == FreezeKind.play) setState(() => _cheer = false);
      });
    }
  }

  void _tap() {
    switch (freezeTap(_now)) {
      case FreezeTap.dance:
        _sounds.play('sparkle');
        setState(() => _jumps++);
      case FreezeTap.shh:
        _sounds.play('shh');
        setState(() {
          _tapsInStop++;
          _shakes++;
          _peek = _shakes % FreezeScreen.dancers.length;
          _say = Strings.shh;
        });
    }
  }

  Pose _pose(int i) {
    if (_now == FreezeKind.stop) return _peek == i ? Pose.idle : Pose.frozen;
    if (_cheer) return Pose.cheer;
    return Pose.sing;
  }

  @override
  Widget build(BuildContext context) {
    final stopped = _now == FreezeKind.stop;
    final warn = _now == FreezeKind.warn;
    return ToyPage(
      title: Toy.freeze.zh,
      tint: stopped ? const Color(0xFFFF9A9A) : null,
      child: Listener(
        key: const ValueKey('freeze-area'),
        behavior: HitTestBehavior.opaque,
        onPointerDown: (_) => _tap(),
        child: Column(children: [
          const SizedBox(height: 6),
          SayBubble(text: _say, size: 17, colour: stopped ? Neon.coral : Neon.lavender),
          Expanded(
            flex: 5,
            child: Center(
              child: AnimatedOpacity(
                duration: const Duration(milliseconds: 150),
                opacity: stopped ? 1 : (warn ? 0.6 : 0.12),
                child: Wiggle(
                  trigger: _shakes,
                  amount: 0.12,
                  child: Semantics(
                    label: stopped ? Strings.stop : Strings.stopLight,
                    child: AspectRatio(aspectRatio: 1, child: Padding(padding: const EdgeInsets.all(12), child: Art(ArtPath.ui('hand'), key: const ValueKey('stop-light')))),
                  ),
                ),
              ),
            ),
          ),
          Expanded(
            flex: 4,
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Stack(children: [
                Positioned(left: 0, right: 0, bottom: 0, height: 120, child: Art(ArtPath.stage('floor'), fit: BoxFit.fill)),
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 46,
                  child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
                    for (var i = 0; i < FreezeScreen.dancers.length; i++)
                      Expanded(child: _Dancer(animal: FreezeScreen.dancers[i], pose: _pose(i), dancing: !stopped, jumps: _jumps, phase: i * 0.25)),
                  ]),
                ),
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}

class _Dancer extends StatelessWidget {
  const _Dancer({required this.animal, required this.pose, required this.dancing, required this.jumps, required this.phase});

  final Animal animal;
  final Pose pose;
  final bool dancing;
  final int jumps;
  final double phase;

  @override
  Widget build(BuildContext context) {
    final body = AspectRatio(aspectRatio: 1, child: Art(animal.art(pose)));
    final hop = Hop(trigger: jumps, height: 40, child: body);
    if (!dancing) return hop;
    return Bob(phase: phase, amount: 10, period: const Duration(milliseconds: 600), child: Stack(clipBehavior: Clip.none, alignment: Alignment.topCenter, children: [
      hop,
      Positioned(top: 0, child: NoteBurst(trigger: jumps, colour: animal.index, size: 20)),
    ]));
  }
}
