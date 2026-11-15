import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/providers.dart';

/// The keys of one instrument: a finger touching a key plays it at once, and
/// a finger sliding across plays each key it reaches (「刷～」). Raw pointer
/// events, never a drag gesture (that waits for the finger to move first).
/// Several fingers at once are fine.
class KeysView extends ConsumerStatefulWidget {
  const KeysView({super.key, required this.instrument, required this.count, this.onKey, this.compact = false});

  final Instrument instrument;
  final int count;

  /// Called after the key's sound is played (to record it, or make an animal jump).
  final void Function(int key)? onKey;

  /// One short row (under the band, on the record page).
  final bool compact;

  @override
  ConsumerState<KeysView> createState() => _KeysViewState();
}

class _KeysViewState extends ConsumerState<KeysView> {
  final _keys = <int, GlobalKey>{};
  final _lit = <int, Timer>{};
  final _under = <int, int?>{};

  GlobalKey _keyOf(int i) => _keys.putIfAbsent(i, GlobalKey.new);

  @override
  void dispose() {
    for (final t in _lit.values) {
      t.cancel();
    }
    super.dispose();
  }

  int? _hit(Offset global) {
    for (var i = 0; i < widget.count; i++) {
      final box = _keyOf(i).currentContext?.findRenderObject() as RenderBox?;
      if (box == null || !box.hasSize) continue;
      final local = box.globalToLocal(global);
      if ((Offset.zero & box.size).contains(local)) return i;
    }
    return null;
  }

  void _press(int i) {
    ref.read(soundsProvider).play(widget.instrument.sound(i));
    _lit[i]?.cancel();
    setState(() => _lit[i] = Timer(const Duration(milliseconds: 240), () {
          if (mounted) setState(() => _lit.remove(i));
        }));
    widget.onKey?.call(i);
  }

  void _at(int pointer, Offset global) {
    final i = _hit(global);
    if (i == _under[pointer]) return;
    _under[pointer] = i;
    if (i != null) _press(i);
  }

  Widget _key(int i) {
    final lit = _lit.containsKey(i);
    return Semantics(
      key: ValueKey('key-$i'),
      container: true,
      button: true,
      label: Strings.key(widget.instrument, i),
      excludeSemantics: true,
      onTap: () => _press(i),
      child: KeyedSubtree(
        key: _keyOf(i),
        child: AnimatedScale(
          scale: lit ? 1.06 : 1,
          duration: const Duration(milliseconds: 90),
          child: widget.compact ? _pill(i, lit) : Art(widget.instrument.art(i, lit: lit)),
        ),
      ),
    );
  }

  /// A short glowing pill in the note's colour (the small row under the band).
  Widget _pill(int i, bool lit) {
    final c = Pentatonic.colour(i);
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 3, vertical: 4),
      decoration: BoxDecoration(
        color: Color.alphaBlend(c.withValues(alpha: lit ? 0.6 : 0.15), const Color(0xFF24204A)),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: c, width: 3),
        boxShadow: [BoxShadow(color: c.withValues(alpha: lit ? 0.7 : 0.35), blurRadius: lit ? 18 : 10)],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final n = widget.count;
    final Widget body;
    if (widget.instrument == Instrument.xylo || widget.compact) {
      body = Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        for (var i = 0; i < n; i++) Expanded(child: Padding(padding: const EdgeInsets.symmetric(horizontal: 2), child: _key(i))),
      ]);
    } else {
      // Drums and pots: three over two, big and round.
      body = Column(children: [
        Expanded(child: Row(children: [for (var i = 0; i < 3; i++) Expanded(child: Padding(padding: const EdgeInsets.all(4), child: _key(i)))])),
        Expanded(
          child: Row(children: [
            const Spacer(),
            for (var i = 3; i < n; i++) Expanded(flex: 2, child: Padding(padding: const EdgeInsets.all(4), child: _key(i))),
            const Spacer(),
          ]),
        ),
      ]);
    }
    return Listener(
      behavior: HitTestBehavior.opaque,
      onPointerDown: (e) => _at(e.pointer, e.position),
      onPointerMove: (e) => _at(e.pointer, e.position),
      onPointerUp: (e) => _under.remove(e.pointer),
      onPointerCancel: (e) => _under.remove(e.pointer),
      child: body,
    );
  }
}
