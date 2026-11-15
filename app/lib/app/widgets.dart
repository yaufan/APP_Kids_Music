import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'package:go_router/go_router.dart';

import '../core/content.dart';
import '../core/providers.dart';
import 'strings.dart';
import 'theme.dart';

/// A drawing from assets/art/ (nothing at all if it is missing).
class Art extends StatelessWidget {
  const Art(this.path, {super.key, this.fit = BoxFit.contain, this.alignment = Alignment.center});

  final String path;
  final BoxFit fit;
  final Alignment alignment;

  @override
  Widget build(BuildContext context) =>
      SvgPicture.asset(path, fit: fit, alignment: alignment, excludeFromSemantics: true, errorBuilder: (_, _, _) => const SizedBox.expand());
}

/// Says a line out loud (if the parent left the voice on), with the English
/// after it when that is on.
void speak(WidgetRef ref, String zh, {String? en}) {
  final s = ref.read(gameProvider).settings;
  if (!s.voice) return;
  ref.read(voiceProvider).say(zh, en: s.english ? en : null);
}

/// Shrinks a little while pressed and plays [sound].
class Pressable extends ConsumerStatefulWidget {
  const Pressable({super.key, required this.child, this.onTap, this.sound = 'tap'});

  final Widget child;
  final VoidCallback? onTap;
  final String? sound;

  @override
  ConsumerState<Pressable> createState() => _PressableState();
}

class _PressableState extends ConsumerState<Pressable> {
  var _down = false;

  @override
  Widget build(BuildContext context) {
    final enabled = widget.onTap != null;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      excludeFromSemantics: true,
      onTapDown: enabled ? (_) => setState(() => _down = true) : null,
      onTapCancel: enabled ? () => setState(() => _down = false) : null,
      onTapUp: enabled ? (_) => setState(() => _down = false) : null,
      onTap: enabled
          ? () {
              final s = widget.sound;
              if (s != null) ref.read(soundsProvider).play(s);
              widget.onTap!();
            }
          : null,
      child: AnimatedScale(scale: _down ? 0.92 : 1, duration: const Duration(milliseconds: 90), child: widget.child),
    );
  }
}

/// A glowing neon ring with a picture in it, and (if given) a word under it.
class NeonButton extends StatelessWidget {
  const NeonButton({
    super.key,
    required this.label,
    required this.art,
    required this.colour,
    this.onTap,
    this.size = 72,
    this.caption,
    this.sound = 'tap',
    this.lit = false,
    this.locked = false,
    this.padding = 0.2,
  });

  final String label;
  final String art;
  final Color colour;
  final VoidCallback? onTap;
  final double size;

  /// A word under the ring (the six toys on the stage).
  final String? caption;
  final String? sound;

  /// Chosen (glows brighter).
  final bool lit;

  /// Shows a small lock (the full version is off).
  final bool locked;
  final double padding;

  @override
  Widget build(BuildContext context) {
    final ring = Container(
      width: size,
      height: size,
      padding: EdgeInsets.all(size * padding),
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: Color.alphaBlend(colour.withValues(alpha: lit ? 0.3 : 0.1), Neon.glass),
        border: Border.all(color: colour.withValues(alpha: locked ? 0.45 : 1), width: math.max(2.5, size * 0.045)),
        boxShadow: [
          BoxShadow(color: colour.withValues(alpha: lit ? 0.55 : 0.32), blurRadius: lit ? 22 : 14, spreadRadius: lit ? 3 : 1),
        ],
      ),
      child: Opacity(opacity: locked ? 0.45 : 1, child: Art(art)),
    );
    return Semantics(
      container: true,
      button: true,
      label: label,
      excludeSemantics: true,
      onTap: onTap,
      child: Pressable(
        onTap: onTap,
        sound: sound,
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Stack(clipBehavior: Clip.none, children: [
            ring,
            if (locked)
              Positioned(right: -2, bottom: -2, width: size * 0.38, height: size * 0.38, child: Art(ArtPath.ui('lock'))),
          ]),
          if (caption != null) ...[
            SizedBox(height: size * 0.1),
            Text(caption!, maxLines: 1, style: TextStyle(fontSize: math.max(14, size * 0.2), color: Neon.ink, fontWeight: FontWeight.w700)),
          ],
        ]),
      ),
    );
  }
}

/// The night stage behind every toy: the background, the swags across the
/// top and the curtains at the sides.
class StageBackdrop extends StatelessWidget {
  const StageBackdrop({super.key, required this.child, this.curtains = true, this.spot = false, this.tint});

  final Widget child;
  final bool curtains;

  /// A soft spotlight down the middle.
  final bool spot;

  /// The spotlight's colour (it changes now and then on the stage).
  final Color? tint;

  @override
  Widget build(BuildContext context) => Stack(children: [
        Positioned.fill(child: Art(ArtPath.stage('bg'), fit: BoxFit.cover)),
        if (spot)
          Positioned.fill(
            child: Align(
              alignment: Alignment.topCenter,
              child: FractionallySizedBox(
                widthFactor: 0.7,
                heightFactor: 0.75,
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 600),
                  child: ColorFiltered(
                    key: ValueKey(tint),
                    colorFilter: ColorFilter.mode(tint ?? const Color(0xFFFFF4C8), BlendMode.modulate),
                    child: Art(ArtPath.stage('spot'), fit: BoxFit.fill),
                  ),
                ),
              ),
            ),
          ),
        if (curtains) ...[
          Positioned(left: -14, top: 0, bottom: 60, width: 92, child: Art(ArtPath.stage('curtain_left'), fit: BoxFit.fill)),
          Positioned(right: -14, top: 0, bottom: 60, width: 92, child: Art(ArtPath.stage('curtain_right'), fit: BoxFit.fill)),
          Positioned(left: 0, right: 0, top: 0, height: 64, child: Art(ArtPath.stage('valance'), fit: BoxFit.fill)),
        ],
        Positioned.fill(child: child),
      ]);
}

/// A toy's page: the stage, the toy's name at the top, the toy, and the
/// round 「回舞台」 button at the bottom left.
class ToyPage extends ConsumerWidget {
  const ToyPage({super.key, required this.title, required this.child, this.action, this.curtains = true, this.spot = true, this.tint});

  final String title;
  final Widget child;

  /// Something at the top right (the band's speed).
  final Widget? action;
  final bool curtains;
  final bool spot;
  final Color? tint;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        backgroundColor: Neon.top,
        body: StageBackdrop(
          curtains: curtains,
          spot: spot,
          tint: tint,
          child: SafeArea(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 560),
                child: Column(children: [
                  SizedBox(
                    height: 64,
                    child: Stack(children: [
                      Center(
                        child: Padding(
                          padding: const EdgeInsets.only(top: 14),
                          child: Text(title, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w700, color: Neon.ink, letterSpacing: 2)),
                        ),
                      ),
                      if (action != null) Positioned(right: 12, top: 4, child: action!),
                    ]),
                  ),
                  Expanded(child: child),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(14, 4, 14, 10),
                    child: Row(children: [
                      NeonButton(
                        key: const ValueKey('home'),
                        label: Strings.backToStage,
                        art: ArtPath.ui('home'),
                        colour: Neon.pink,
                        size: 62,
                        sound: 'back',
                        onTap: () => context.go('/'),
                      ),
                    ]),
                  ),
                ]),
              ),
            ),
          ),
        ),
      );
}

/// A soft rounded bubble with words (tap to hear them again).
class SayBubble extends StatelessWidget {
  const SayBubble({super.key, required this.text, this.onTap, this.size = 18, this.colour = Neon.lavender});

  final String text;
  final VoidCallback? onTap;
  final double size;
  final Color colour;

  @override
  Widget build(BuildContext context) => Semantics(
        container: true,
        button: onTap != null,
        label: text,
        excludeSemantics: true,
        onTap: onTap,
        child: GestureDetector(
          onTap: onTap,
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 250),
            child: Container(
              key: ValueKey(text),
              padding: EdgeInsets.symmetric(horizontal: size * 1.0, vertical: size * 0.5),
              decoration: BoxDecoration(
                color: Neon.glass.withValues(alpha: 0.85),
                borderRadius: BorderRadius.circular(size * 2),
                border: Border.all(color: colour, width: 2.4),
                boxShadow: [BoxShadow(color: colour.withValues(alpha: 0.3), blurRadius: 12)],
              ),
              child: Text(text, textAlign: TextAlign.center, style: TextStyle(fontSize: size, color: Neon.ink, height: 1.35, fontWeight: FontWeight.w700)),
            ),
          ),
        ),
      );
}

/// A gentle bob up and down (the band, the stage).
class Bob extends StatefulWidget {
  const Bob({super.key, required this.child, this.phase = 0, this.amount = 4, this.period = const Duration(milliseconds: 1200)});

  final Widget child;
  final double phase;
  final double amount;
  final Duration period;

  @override
  State<Bob> createState() => _BobState();
}

class _BobState extends State<Bob> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: widget.period)..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (_, child) => Transform.translate(offset: Offset(0, -math.sin((_c.value + widget.phase) * 2 * math.pi).abs() * widget.amount), child: child),
        child: widget.child,
      );
}

/// Jumps once each time [trigger] changes.
class Hop extends StatefulWidget {
  const Hop({super.key, required this.trigger, required this.child, this.height = 18});

  final int trigger;
  final Widget child;
  final double height;

  @override
  State<Hop> createState() => _HopState();
}

class _HopState extends State<Hop> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 380));

  @override
  void didUpdateWidget(Hop old) {
    super.didUpdateWidget(old);
    if (old.trigger != widget.trigger) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (_, child) => Transform.translate(offset: Offset(0, -math.sin(_c.value * math.pi) * widget.height), child: child),
        child: widget.child,
      );
}

/// Shakes side to side once each time [trigger] changes.
class Wiggle extends StatefulWidget {
  const Wiggle({super.key, required this.trigger, required this.child, this.amount = 0.08});

  final int trigger;
  final Widget child;
  final double amount;

  @override
  State<Wiggle> createState() => _WiggleState();
}

class _WiggleState extends State<Wiggle> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 500));

  @override
  void didUpdateWidget(Wiggle old) {
    super.didUpdateWidget(old);
    if (old.trigger != widget.trigger) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
        animation: _c,
        builder: (_, child) {
          final t = _c.value;
          return Transform.rotate(angle: math.sin(t * math.pi * 4) * (1 - t) * widget.amount, child: child);
        },
        child: widget.child,
      );
}

/// Little notes that float up and fade each time [trigger] changes.
class NoteBurst extends StatefulWidget {
  const NoteBurst({super.key, required this.trigger, this.colour = 0, this.size = 26});

  final int trigger;
  final int colour;
  final double size;

  @override
  State<NoteBurst> createState() => _NoteBurstState();
}

class _NoteBurstState extends State<NoteBurst> with SingleTickerProviderStateMixin {
  late final _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 900));

  @override
  void didUpdateWidget(NoteBurst old) {
    super.didUpdateWidget(old);
    if (old.trigger != widget.trigger) _c.forward(from: 0);
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => IgnorePointer(
        child: AnimatedBuilder(
          animation: _c,
          builder: (_, _) {
            final t = _c.value;
            if (t == 0 || t == 1) return SizedBox(width: widget.size, height: widget.size);
            return SizedBox(width: widget.size, height: widget.size, child: Stack(clipBehavior: Clip.none, children: [
              for (var i = 0; i < 3; i++)
                Positioned(
                  left: (i - 1) * widget.size * 0.9 + math.sin(t * 6 + i) * 6,
                  top: -t * widget.size * (2.2 + i * 0.4),
                  width: widget.size,
                  height: widget.size,
                  child: Opacity(opacity: (1 - t).clamp(0, 1), child: Art(ArtPath.note(widget.colour + i))),
                ),
            ]));
          },
        ),
      );
}
