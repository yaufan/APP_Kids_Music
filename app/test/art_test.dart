import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:little_wave/core/content.dart';

/// Every picture the program asks for exists (docs/art.md), flutter_svg can
/// draw it, and every sound it plays is there (design/sounds/README.md).
void main() {
  bool has(String path) => File(path).existsSync();

  test('every picture the program asks for is drawn', () {
    final want = <String>[
      for (final t in Toy.values) t.art,
      for (final a in Animal.values)
        for (final p in Pose.values) a.art(p),
      for (final i in Instrument.values)
        for (var k = 0; k < i.count(Level.big); k++) ...[i.art(k), i.art(k, lit: true)],
      for (var i = 0; i < 5; i++) ...[ArtPath.step(i), ArtPath.step(i, lit: true), ArtPath.note(i)],
      for (final s in StreetSound.values) s.art,
      for (var i = 0; i < 8; i++) ArtPath.tape(i),
      for (var i = 0; i < 3; i++) ArtPath.balloon(i),
      for (final n in ['bg', 'curtain_left', 'curtain_right', 'valance', 'floor', 'spot', 'audience']) ArtPath.stage(n),
      for (final n in ['home', 'lock', 'sun', 'moon', 'snail', 'rabbit', 'play', 'stop', 'rec', 'replay', 'mute', 'plus', 'star', 'mouse', 'slot', 'hand']) ArtPath.ui(n),
    ];
    expect([for (final p in want) if (!has(p)) p], isEmpty, reason: 'draw these in design/art/');
    final pubspec = File('pubspec.yaml').readAsStringSync();
    for (final dir in want.map((p) => p.substring(0, p.lastIndexOf('/') + 1)).toSet()) {
      expect(pubspec, contains('- $dir'), reason: 'pubspec.yaml lists each picture folder ($dir)');
    }
  });

  test('every sound the program plays is there', () {
    final want = <String>[
      for (final i in Instrument.values)
        for (var k = 0; k < i.count(Level.big); k++) i.sound(k),
      for (final a in Animal.values) ...[a.call, for (final t in Tempo.values) a.loop(t)],
      for (final s in StreetSound.values) s.sound,
      for (final m in Music.values) m.file,
      for (var i = 0; i < 5; i++) 'stair_$i',
      ...['tap', 'back', 'open', 'lock', 'pop', 'applause', 'sparkle', 'join', 'leave', 'right', 'rec_start', 'rec_stop', 'tick', 'light',
        'lights_off', 'night', 'loud', 'soft', 'freeze_stop', 'freeze_go', 'shh', 'cheer'],
    ];
    expect([for (final s in want) if (!has('assets/sounds/$s.wav')) s], isEmpty, reason: 'make these in design/sounds/make_sounds.py');
    final total = Directory('assets/sounds').listSync().whereType<File>().fold<int>(0, (n, f) => n + f.lengthSync());
    expect(total, lessThan(15 * 1000 * 1000), reason: 'the sounds stay under 15 MB');
  });

  test('no picture uses what flutter_svg cannot draw, and none is too big', () {
    final bad = <String>[];
    for (final f in Directory('assets/art').listSync(recursive: true).whereType<File>()) {
      if (!f.path.endsWith('.svg')) {
        bad.add('${f.path} is not an SVG');
        continue;
      }
      final text = f.readAsStringSync();
      if (f.lengthSync() > 70 * 1024) bad.add('${f.path} too big');
      for (final no in ['<filter', '<mask', '<style', 'style=', '<text', '<image', '<pattern', 'mix-blend', '<clipPath', 'clip-path=']) {
        if (text.contains(no)) bad.add('${f.path} uses $no');
      }
      if (!text.trimRight().endsWith('</svg>')) bad.add('${f.path} is cut off');
    }
    expect(bad, isEmpty);
  });
}
