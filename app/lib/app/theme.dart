import 'package:flutter/material.dart';

/// The app's colours (docs/design.md 「畫風」: a deep navy-purple stage, soft
/// pastel neon; words in pale lilac-white, without a glow so they read).
abstract final class Neon {
  static const top = Color(0xFF1B1A3A);
  static const bottom = Color(0xFF2A2550);
  static const night = Color(0xFF141331);
  static const ink = Color(0xFFF2EEFF);
  static const inkSoft = Color(0xFFB6AEDC);
  static const glass = Color(0xFF24204A);
  static const pink = Color(0xFFFF8FC8);
  static const coral = Color(0xFFFF8A8A);
  static const orange = Color(0xFFFFA66B);
  static const yellow = Color(0xFFFFE16E);
  static const green = Color(0xFF8EF09A);
  static const mint = Color(0xFF7FF0D2);
  static const cyan = Color(0xFF63DCF5);
  static const sky = Color(0xFF8FB8FF);
  static const lilac = Color(0xFFC7A6FF);
  static const lavender = Color(0xFFDCD3FF);

  /// The parent pages are plain and light (for grown-ups).
  static const parentBg = Color(0xFFF4F2FA);
  static const parentInk = Color(0xFF2E2A4A);
  static const parentSoft = Color(0xFF7A74A0);

  /// The six toys' button colours.
  static const toys = [coral, green, pink, yellow, orange, lilac];
}

abstract final class NeonTheme {
  /// jf open 粉圓 (OFL): a rounded typeface made in Taiwan.
  static const font = 'Huninn';

  static ThemeData dark() {
    final base = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: Neon.lilac, brightness: Brightness.dark, surface: Neon.top),
      scaffoldBackgroundColor: Neon.top,
      fontFamily: font,
      materialTapTargetSize: MaterialTapTargetSize.padded,
    );
    return base.copyWith(textTheme: base.textTheme.apply(bodyColor: Neon.ink, displayColor: Neon.ink, fontFamily: font));
  }

  static ThemeData parent() {
    final base = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF7B61FF), surface: Neon.parentBg),
      scaffoldBackgroundColor: Neon.parentBg,
      fontFamily: font,
    );
    return base.copyWith(textTheme: base.textTheme.apply(bodyColor: Neon.parentInk, displayColor: Neon.parentInk, fontFamily: font));
  }
}
