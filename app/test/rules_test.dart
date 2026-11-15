import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:little_wave/core/content.dart';
import 'package:little_wave/core/game.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:little_wave/core/music.dart';
import 'package:little_wave/core/providers.dart';
import 'package:little_wave/core/store.dart';

/// The rules of the toys (docs/design.md): the band's clock, the one key,
/// the freeze game, the tape, 聽聽看, and what is kept.
void main() {
  group('the band clock', () {
    test('a beat, a bar and a loop are exact at every tempo', () {
      expect(MusicClock.of(Tempo.slow).beat, const Duration(milliseconds: 750));
      expect(MusicClock.of(Tempo.normal).beat, const Duration(milliseconds: 600));
      expect(MusicClock.of(Tempo.fast).beat, const Duration(milliseconds: 500));
      expect(MusicClock.of(Tempo.normal).bar, const Duration(milliseconds: 2400));
      expect(MusicClock.of(Tempo.normal).loop, const Duration(milliseconds: 4800));
      expect([for (final t in Tempo.values) MusicClock.of(t).loopSamples(16000)], [96000, 76800, 64000]);
    });

    test('an animal joins at the next bar line, never in the middle of a bar', () {
      const c = MusicClock(100);
      expect(c.nextBar(Duration.zero), Duration.zero);
      expect(c.nextBar(const Duration(milliseconds: 1)), const Duration(milliseconds: 2400));
      expect(c.nextBar(const Duration(milliseconds: 2400)), const Duration(milliseconds: 2400));
      expect(c.nextBar(const Duration(milliseconds: 2399), lead: const Duration(milliseconds: 30)), const Duration(milliseconds: 4800));
      expect(c.nextBar(const Duration(milliseconds: 5000)), const Duration(milliseconds: 7200));
      expect(c.untilNextBar(const Duration(milliseconds: 5000)), const Duration(milliseconds: 2200));
      for (var ms = 0; ms < 20000; ms += 37) {
        final next = c.nextBar(Duration(milliseconds: ms));
        expect(next.inMicroseconds % c.bar.inMicroseconds, 0);
        expect(next >= Duration(milliseconds: ms), isTrue);
        expect(next - Duration(milliseconds: ms) < c.bar, isTrue);
      }
    });

    test('which bar and beat we are in', () {
      const c = MusicClock(120);
      expect(c.barInLoop(Duration.zero), 0);
      expect(c.barInLoop(const Duration(milliseconds: 2100)), 1);
      expect(c.barInLoop(const Duration(milliseconds: 4100)), 0);
      expect(c.beatsAt(const Duration(milliseconds: 1250)), closeTo(2.5, 1e-9));
    });

    test('every band loop file is exactly one loop long at its tempo, so loops started together stay together', () {
      for (final t in Tempo.values) {
        final want = MusicClock.of(t).loopSamples(16000);
        for (final a in Animal.values) {
          final f = File('assets/sounds/${a.loop(t)}.wav');
          expect(f.existsSync(), isTrue, reason: f.path);
          final (rate, samples) = _wav(f.readAsBytesSync());
          expect(rate, 16000, reason: f.path);
          expect(samples, want, reason: f.path);
        }
      }
    });
  });

  group('one key: C major pentatonic', () {
    test('no two keys are ever a half step apart', () {
      for (var a = 0; a < 8; a++) {
        for (var b = 0; b < 8; b++) {
          expect(Pentatonic.clash(a, b), isFalse, reason: '$a $b');
        }
      }
      expect(Pentatonic.semitones.map((s) => s % 12).toSet(), {0, 2, 4, 7, 9});
    });

    test('a note has one colour everywhere: Do red, Re orange, Mi yellow, Sol green, La blue', () {
      expect(Pentatonic.colour(0), Pentatonic.colour(5), reason: 'both Do');
      expect(Pentatonic.colour(2), Pentatonic.colour(7), reason: 'both Mi');
      expect(Pentatonic.colours.toSet().length, 5);
      expect(Pentatonic.hz(0), closeTo(523.25, 0.01));
      expect(Pentatonic.hz(5), closeTo(1046.5, 0.02));
    });

    test('小小 gets five keys, 大 eight on the xylophone; drums and pots have five; every key has its sound', () {
      expect(Instrument.xylo.count(Level.small), 5);
      expect(Instrument.xylo.count(Level.big), 8);
      expect(Instrument.drum.count(Level.big), 5);
      expect(Instrument.pot.count(Level.big), 5);
      for (final i in Instrument.values) {
        expect(i.keys.length, i.count(Level.big));
        for (var k = 0; k < i.count(Level.big); k++) {
          expect(File('assets/sounds/${i.sound(k)}.wav').existsSync(), isTrue, reason: i.sound(k));
        }
      }
    });
  });

  group('the band on the stage', () {
    test('an animal pushed off its spot is not 噓\'d any more when it comes back', () {
      final c = ProviderContainer();
      addTearDown(c.dispose);
      final band = c.read(bandProvider.notifier);
      band.put(Animal.bear, 0);
      band.shush(Animal.bear);
      expect(c.read(bandProvider).singing, isEmpty);
      band.put(Animal.frog, 0);
      expect(c.read(bandProvider).onStage, {Animal.frog});
      expect(c.read(bandProvider).shushed, isEmpty);
      band.put(Animal.bear, 1);
      expect(c.read(bandProvider).singing, {Animal.frog, Animal.bear}, reason: 'the bear sings again');
    });

    test('a 噓\'d animal moved to another spot stays 噓\'d; one dragged off is not', () {
      final c = ProviderContainer();
      addTearDown(c.dispose);
      final band = c.read(bandProvider.notifier)
        ..put(Animal.cat, 0)
        ..shush(Animal.cat)
        ..put(Animal.cat, 2);
      expect(c.read(bandProvider).shushed, {Animal.cat});
      band.remove(Animal.cat);
      band.put(Animal.cat, 1);
      expect(c.read(bandProvider).singing, {Animal.cat});
    });
  });

  group('what the parent\'s sound switches turn off', () {
    test('按鈕音效 only turns off the buttons and cues; every toy keeps its sound', () {
      final toys = [
        for (final i in Instrument.values)
          for (var k = 0; k < i.count(Level.big); k++) i.sound(k),
        for (final a in Animal.values) ...[a.call, for (final t in Tempo.values) a.loop(t)],
        for (final s in StreetSound.values) s.sound,
        for (var i = 0; i < 5; i++) 'stair_$i',
        'loud', 'soft', 'freeze_stop', 'freeze_go', 'shh', 'cheer', 'tick',
      ];
      for (final s in toys) {
        expect(SoundKind.plays(s, effects: false), isTrue, reason: s);
      }
      for (final s in ['tap', 'back', 'open', 'lock', 'pop', 'applause', 'join']) {
        expect(SoundKind.plays(s, effects: false), isFalse, reason: s);
        expect(SoundKind.plays(s, effects: true), isTrue, reason: s);
      }
      for (final s in SoundKind.ui) {
        expect(File('assets/sounds/$s.wav').existsSync(), isTrue, reason: s);
      }
    });

    test('背景音樂 only turns off the stage\'s and the rest\'s music, not the freeze game\'s', () {
      expect(SoundKind.music(Music.stage, music: false), isNull);
      expect(SoundKind.music(Music.rest, music: false), isNull);
      expect(SoundKind.music(Music.freeze, music: false), Music.freeze);
      expect(SoundKind.music(Music.stage, music: true), Music.stage);
      expect(SoundKind.music(null, music: true), isNull);
    });
  });

  group('音樂木頭人', () {
    test('小小: a warning, then a long stop of 3 to 5 seconds', () {
      final plan = FreezePlan(Level.small, math.Random(1));
      for (var i = 0; i < 200; i++) {
        final r = plan.round();
        expect(r.map((p) => p.kind), [FreezeKind.play, FreezeKind.warn, FreezeKind.stop]);
        expect(r.last.length.inMilliseconds, inInclusiveRange(3000, 5000));
        expect(r.first.length.inMilliseconds, inInclusiveRange(6000, 10000));
      }
    });

    test('大: quick, random stops of 1 to 4 seconds, no warning, now and then a pretend stop', () {
      final plan = FreezePlan(Level.big, math.Random(2));
      var fakes = 0;
      final stops = <int>{};
      for (var i = 0; i < 400; i++) {
        final r = plan.round();
        expect(r.where((p) => p.kind == FreezeKind.warn), isEmpty);
        expect(r.last.kind, FreezeKind.stop);
        expect(r.last.length.inMilliseconds, inInclusiveRange(1000, 4000));
        stops.add(r.last.length.inMilliseconds ~/ 500);
        if (r.any((p) => p.kind == FreezeKind.fake)) fakes++;
      }
      expect(fakes, inInclusiveRange(40, 180), reason: 'about one round in four');
      expect(stops.length, greaterThan(4), reason: 'the stops are random');
      expect(FreezePlan(Level.small, math.Random(3)).round().any((p) => p.kind == FreezeKind.fake), isFalse);
    });

    test('there is no penalty: a tap during a stop is only a 「噓」, while the music plays it is dancing', () {
      expect(freezeTap(FreezeKind.stop), FreezeTap.shh);
      expect(freezeTap(FreezeKind.play), FreezeTap.dance);
      expect(freezeTap(FreezeKind.fake), FreezeTap.dance);
      expect(freezeTap(FreezeKind.warn), FreezeTap.dance);
    });
  });

  group('錄下來', () {
    test('小小: each tap fills the next cell', () {
      final t = Tape(Tape.lengthFor(Level.small));
      expect(t.length, 4);
      expect([t.step(2), t.step(0), t.step(4), t.step(1)], [0, 1, 2, 3]);
      expect(t.full, isTrue);
      expect(t.step(3), isNull);
      expect(t.cells, [2, 0, 4, 1]);
    });

    test('大: a tap goes in the nearest beat, so playback is on the beat', () {
      final t = Tape(Tape.lengthFor(Level.big));
      expect(t.length, 8);
      expect(t.timed(1, const Duration(milliseconds: 40)), 0);
      expect(t.timed(2, const Duration(milliseconds: 650)), 1);
      expect(t.timed(3, const Duration(milliseconds: 1450)), 2, reason: '1.45 s is nearer 1.2 than 1.8');
      expect(t.timed(4, const Duration(milliseconds: 1520)), 3);
      expect(t.timed(0, const Duration(milliseconds: 1790)), 3, reason: 'a later tap in the same cell wins');
      expect(t.cells.take(4), [1, 2, 3, 0]);
      expect(t.timed(0, const Duration(milliseconds: 4500)), isNull, reason: 'past the end');
      expect(t.cellAt(const Duration(milliseconds: 4400)), 7);
      expect(t.cellAt(const Duration(milliseconds: -10)), 0);
      expect(t.runs, const Duration(milliseconds: 5100));
    });

    test('songs are kept newest first, eight at most; an empty tape is not kept', () {
      var g = const Game();
      for (var i = 0; i < 10; i++) {
        g = g.keep(Song(instrument: Instrument.xylo, notes: [i % 5, null], colour: g.nextColour, made: DateTime(2026, 11, 15, 10, i)));
      }
      expect(g.songs.length, Game.maxSongs);
      expect(g.songs.first.made.minute, 9);
      expect(g.songs.first.colour, 1, reason: 'the tape colours go round the eight');
      expect(g.keep(Song(instrument: Instrument.drum, notes: [null, null], colour: 0, made: DateTime(2026))).songs.length, 8);
      expect(g.forget(0).songs.length, 7);
      expect(g.forget(42).songs.length, 8);
    });
  });

  group('聽聽看', () {
    test('小小: two pictures, never two alike; 大: four; the sound is always one of them', () {
      final r = math.Random(4);
      StreetSound? last;
      for (var i = 0; i < 300; i++) {
        final small = ListenRound.make(Level.small, r, pool: StreetSound.values, last: last);
        expect(small.options.length, 2);
        expect(small.options, contains(small.answer));
        expect(small.options.map((s) => s.family).toSet().length, 2, reason: '${small.options}');
        expect(small.answer, isNot(last));
        last = small.answer;
        final big = ListenRound.make(Level.big, r, pool: StreetSound.values);
        expect(big.options.length, 4);
        expect(big.options.toSet().length, 4);
        expect(big.options, contains(big.answer));
      }
    });

    test('every sound has its file and its picture; no thunder, no ambulance', () {
      expect(StreetSound.values.length, 12);
      for (final s in StreetSound.values) {
        expect(File('assets/sounds/${s.sound}.wav').existsSync(), isTrue, reason: s.sound);
        expect(File(s.art).existsSync(), isTrue, reason: s.art);
      }
      final files = Directory('assets/sounds').listSync().map((f) => f.path).join(' ');
      expect(files, isNot(contains('thunder')));
      expect(files, isNot(contains('ambulance')));
    });
  });

  group('what is kept', () {
    test('a game goes to the file and comes back the same', () {
      final g = Game(
        settings: const Settings(level: Level.big, minutes: 20, off: {Toy.tap}, music: false, voice: false, english: true, volume: 0.5, full: false),
        songs: [
          Song(instrument: Instrument.pot, notes: const [0, null, 4, 2], colour: 3, made: DateTime(2026, 11, 15, 9)),
          Song(instrument: Instrument.xylo, notes: const [7, 6, 5, 4, 3, 2, 1, 0], colour: 2, made: DateTime(2026, 11, 14, 9)),
        ],
        today: const Today(day: '2026-11-15', seconds: 300, opens: {Toy.band: 3, Toy.tap: 1}),
        restSince: DateTime(2026, 11, 15, 10),
      );
      final back = Game.fromJson(jsonDecode(jsonEncode(g.toJson())) as Map<String, dynamic>);
      expect(jsonEncode(back.toJson()), jsonEncode(g.toJson()));
      expect(back.settings.level, Level.big);
      expect(back.settings.opens(Toy.record), isFalse, reason: 'not in the free version');
      expect(back.settings.opens(Toy.tap), isFalse, reason: 'turned off');
      expect(back.settings.opens(Toy.band), isTrue);
      expect(back.songs[1].notes.length, 8);
      expect(back.today!.favourite, Toy.band);
    });

    test('a broken or strange file never breaks the app', () {
      expect(Game.fromJson(null).settings.minutes, 15);
      final odd = Game.fromJson({
        'settings': {'level': 'giant', 'minutes': 999, 'off': ['nothing', 'band', 3], 'volume': 7, 'music': 'yes'},
        'songs': [
          'not a song',
          {'instrument': 'kazoo', 'notes': [1], 'made': '2026-11-15T09:00:00'},
          {'instrument': 'xylo', 'notes': [1, 99], 'made': '2026-11-15T09:00:00'},
          {'instrument': 'drum', 'notes': [], 'made': '2026-11-15T09:00:00'},
          {'instrument': 'drum', 'notes': [1, null, 2], 'colour': 13, 'made': '2026-11-15T09:00:00'},
        ],
        'today': 'yesterday',
        'restSince': 'soon',
      });
      expect(odd.settings.level, Level.small);
      expect(odd.settings.minutes, 15);
      expect(odd.settings.off, {Toy.band});
      expect(odd.settings.volume, 0.7);
      expect(odd.settings.music, isTrue);
      expect(odd.songs.length, 1);
      expect(odd.songs.single.colour, 5);
      expect(odd.today, isNull);
      expect(odd.restSince, isNull);
    });

    test('the file store keeps the last save and falls back to the copy before a broken one', () async {
      final dir = Directory.systemTemp.createTempSync('wave_store_');
      addTearDown(() => dir.deleteSync(recursive: true));
      final store = FileStore(dir);
      expect(await store.read(), isNull);
      store.write(const Game(settings: Settings(minutes: 5)).toJson());
      store.write(const Game(settings: Settings(minutes: 10)).toJson());
      await store.flush();
      expect(Game.fromJson(await store.read()).settings.minutes, 10);
      File('${dir.path}/little_wave.json').writeAsStringSync('{"settings": {"minu');
      expect(Game.fromJson(await store.read()).settings.minutes, 5, reason: 'the copy from the save before');
    });

    test('play time: an hour of rest, and today counts minutes and the favourite toy', () {
      final now = DateTime(2026, 11, 15, 10);
      var g = const Game().rest(now);
      expect(g.resting(now.add(const Duration(minutes: 59))), isTrue);
      expect(g.resting(now.add(const Duration(minutes: 61))), isFalse);
      g = g.playOn();
      expect(g.restSince, isNull);
      g = g.opened(Toy.band, now).opened(Toy.band, now).opened(Toy.listen, now).played(const Duration(minutes: 3), now);
      expect(g.today!.favourite, Toy.band);
      expect(g.today!.seconds, 180);
      g = g.opened(Toy.tap, now.add(const Duration(days: 1)));
      expect(g.today!.opens, {Toy.tap: 1}, reason: 'a new day starts over');
    });

    test('a phone clock moved back to before the rest does not keep the child waiting', () {
      final now = DateTime(2026, 11, 15, 10);
      final g = const Game().rest(now);
      expect(g.resting(now), isTrue);
      expect(g.resting(now.subtract(const Duration(minutes: 5))), isFalse);
      expect(g.resting(now.subtract(const Duration(days: 1))), isFalse);
    });

    test('free version: the first six animals, and 錄下來 and 聽聽看 are locked', () {
      expect(Animal.available(full: false).length, 6);
      expect(Animal.available(full: true).length, 10);
      expect(Animal.available(full: false), isNot(contains(Animal.blackbear)));
      expect([for (final t in Toy.values) if (!t.free) t], [Toy.record, Toy.listen]);
    });
  });
}

/// (sample rate, samples) of a mono 16-bit WAV.
(int, int) _wav(Uint8List bytes) {
  final d = ByteData.sublistView(bytes);
  var at = 12;
  int? rate;
  while (at + 8 <= bytes.length) {
    final id = String.fromCharCodes(bytes.sublist(at, at + 4));
    final size = d.getUint32(at + 4, Endian.little);
    if (id == 'fmt ') rate = d.getUint32(at + 12, Endian.little);
    if (id == 'data') return (rate!, size ~/ 2);
    at += 8 + size;
  }
  throw StateError('no data');
}
