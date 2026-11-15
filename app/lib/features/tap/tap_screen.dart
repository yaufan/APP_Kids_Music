import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';
import 'keys_view.dart';

/// 敲敲樂: a xylophone, drums, or pots and pans; whatever is hit sounds good
/// (all one key). The frog above jumps and sings out a note each time.
class TapScreen extends ConsumerStatefulWidget {
  const TapScreen({super.key});

  @override
  ConsumerState<TapScreen> createState() => _TapScreenState();
}

class _TapScreenState extends ConsumerState<TapScreen> {
  late final Sounds _sounds;
  var _instrument = Instrument.xylo;
  var _hits = 0;
  var _last = 0;

  static String _pick(Instrument i) => switch (i) {
        Instrument.xylo => 'assets/art/toys/xylo.svg',
        Instrument.drum => 'assets/art/keys/drum_0_idle.svg',
        Instrument.pot => 'assets/art/keys/pot_0_idle.svg',
      };

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, null);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) speak(ref, '${Toy.tap.zh}！${Strings.tapHint}');
    });
  }

  @override
  void dispose() {
    _sounds.release(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final level = ref.watch(gameProvider.select((g) => g.settings.level));
    final colours = [Neon.coral, Neon.orange, Neon.mint];
    return ToyPage(
      title: Toy.tap.zh,
      child: Column(children: [
        const SizedBox(height: 6),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          for (final i in Instrument.values)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10),
              child: NeonButton(
                key: ValueKey('instrument-${i.name}'),
                label: i.zh,
                caption: i.zh,
                art: _pick(i),
                colour: colours[i.index],
                size: 64,
                lit: i == _instrument,
                padding: 0.16,
                onTap: () {
                  setState(() => _instrument = i);
                  speak(ref, i.zh);
                },
              ),
            ),
        ]),
        const SizedBox(height: 8),
        SizedBox(
          height: 110,
          child: Stack(clipBehavior: Clip.none, alignment: Alignment.center, children: [
            Hop(trigger: _hits, height: 22, child: SizedBox(width: 110, height: 110, child: Art(Animal.frog.art(_hits == 0 ? Pose.idle : Pose.sing)))),
            Positioned(top: 10, child: NoteBurst(trigger: _hits, colour: _last)),
          ]),
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 8),
            child: KeysView(
              key: ValueKey(_instrument),
              instrument: _instrument,
              count: _instrument.count(level),
              onKey: (k) => setState(() {
                _hits++;
                _last = k;
              }),
            ),
          ),
        ),
      ]),
    );
  }
}
