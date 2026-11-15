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

/// 聽聽看 (docs/design.md): a sound of everyday Taiwan plays from the big
/// speaker; tap the picture it belongs to. Right: the picture comes alive.
/// Not right: no matter, 「這是機車喔」, and the sound plays again. 小小 picks
/// from two very different pictures, 大 from four.
class ListenScreen extends ConsumerStatefulWidget {
  const ListenScreen({super.key});

  @override
  ConsumerState<ListenScreen> createState() => _ListenScreenState();
}

class _ListenScreenState extends ConsumerState<ListenScreen> {
  late final Sounds _sounds;
  late ListenRound _round;
  StreetSound? _right;
  StreetSound? _wrong;
  var _wiggle = 0;
  var _say = Strings.listenAsk;
  Timer? _next;
  Timer? _replay;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _sounds.hold(this, null);
    _round = _make(null);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      speak(ref, Strings.listenAsk);
      _replay = Timer(const Duration(milliseconds: 1400), _ask);
    });
  }

  @override
  void dispose() {
    _next?.cancel();
    _replay?.cancel();
    _sounds.release(this);
    super.dispose();
  }

  ListenRound _make(StreetSound? last) =>
      ListenRound.make(ref.read(gameProvider).settings.level, ref.read(randomProvider), pool: StreetSound.values, last: last);

  void _ask() {
    if (!mounted) return;
    _sounds.play(_round.answer.sound);
  }

  void _pick(StreetSound s) {
    if (_right != null) return;
    if (s == _round.answer) {
      _sounds.play('right');
      final find = Strings.goFind(s);
      final line = '${Strings.right(s)}$find';
      speak(ref, line, en: s.en);
      setState(() {
        _right = s;
        _wrong = null;
        _say = Strings.right(s);
      });
      _replay?.cancel();
      _replay = Timer(const Duration(milliseconds: 900), _ask);
      _next?.cancel();
      _next = Timer(const Duration(milliseconds: 4200), () {
        if (!mounted) return;
        setState(() {
          _round = _make(_round.answer);
          _right = null;
          _say = Strings.listenAsk;
        });
        speak(ref, Strings.listenAsk);
        _replay = Timer(const Duration(milliseconds: 1400), _ask);
      });
    } else {
      speak(ref, Strings.thisIs(s), en: s.en);
      setState(() {
        _wrong = s;
        _wiggle++;
        _say = Strings.thisIs(s);
      });
      _replay?.cancel();
      _replay = Timer(const Duration(milliseconds: 1500), _ask);
    }
  }

  Widget _card(StreetSound s, int i, double size) {
    final right = _right == s;
    final colour = right ? Neon.yellow : (_wrong == s ? Neon.lavender : Neon.toys[(i + 2) % Neon.toys.length]);
    final picture = Container(
      width: size,
      height: size,
      padding: EdgeInsets.all(size * 0.08),
      decoration: BoxDecoration(
        color: Color.alphaBlend(colour.withValues(alpha: right ? 0.25 : 0.08), Neon.glass),
        borderRadius: BorderRadius.circular(size * 0.16),
        border: Border.all(color: colour, width: right ? 5 : 3),
        boxShadow: [BoxShadow(color: colour.withValues(alpha: right ? 0.6 : 0.25), blurRadius: right ? 24 : 12)],
      ),
      child: Art(s.art),
    );
    return Semantics(
      key: ValueKey('choice-${s.name}'),
      container: true,
      button: true,
      label: s.zh,
      excludeSemantics: true,
      onTap: () => _pick(s),
      child: Pressable(
        sound: null,
        onTap: () => _pick(s),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Wiggle(trigger: _wrong == s ? _wiggle : 0, child: right ? Bob(amount: 8, period: const Duration(milliseconds: 500), child: picture) : picture),
          const SizedBox(height: 4),
          AnimatedOpacity(
            duration: const Duration(milliseconds: 200),
            opacity: right || _wrong == s ? 1 : 0,
            child: Text(s.zh, style: const TextStyle(fontSize: 18, color: Neon.ink, fontWeight: FontWeight.w700)),
          ),
        ]),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final options = _round.options;
    return ToyPage(
      title: Toy.listen.zh,
      child: Column(children: [
        const SizedBox(height: 6),
        NeonButton(key: const ValueKey('speaker'), label: Strings.again, art: ArtPath.ui('replay'), colour: Neon.lilac, size: 104, sound: null, onTap: _ask),
        const SizedBox(height: 10),
        SayBubble(text: _say, size: 19, onTap: _ask),
        const SizedBox(height: 10),
        Expanded(
          child: LayoutBuilder(builder: (_, box) {
            final two = options.length == 2;
            final size = two ? (box.maxWidth / 2 - 36).clamp(80.0, box.maxHeight * 0.8) : (box.maxWidth / 2 - 40).clamp(70.0, box.maxHeight / 2 - 40);
            final cards = [for (var i = 0; i < options.length; i++) _card(options[i], i, size)];
            if (two) return Center(child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: cards));
            return Column(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: cards.take(2).toList()),
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: cards.skip(2).toList()),
            ]);
          }),
        ),
      ]),
    );
  }
}
