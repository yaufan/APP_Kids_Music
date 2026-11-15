import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:little_musician/core/content.dart';
import 'package:little_musician/core/game.dart';
import 'package:little_musician/core/providers.dart';
import 'package:little_musician/features/parent/parent_gate.dart';

import 'helpers.dart';

/// Every toy as a child would play it, on a phone and a tablet, at both
/// levels, with screenshots in `build/screenshots/<device>/` (docs/design.md).
void main() {
  setUpAll(loadFonts);

  for (final MapEntry(key: device, value: (size, ratio)) in {'phone': (const Size(1080, 2340), 2.75), 'tablet': (const Size(1620, 2160), 2.0)}.entries) {
    testWidgets('a child plays with every toy ($device)', (tester) async {
      final app = await TestApp.start(tester, size: size, ratio: ratio, seed: 3);
      Future<void> shot(String name) => shoot(tester, device, name);
      List<String> since(int n) => app.sounds.played.sublist(n);

      // The stage.
      expect(app.location, '/');
      expect(app.sounds.musicNow, Music.stage);
      expect(app.voice.said.first, contains('歡迎'));
      await app.settle(800);
      await shot('01_stage');

      // 敲敲樂: tap a key, slide across the keys, change instruments.
      await app.tapKey('toy-tap', ms: 800);
      expect(app.location, '/toy/tap');
      expect(app.sounds.musicNow, isNull, reason: 'the child makes the music here');
      var n = app.sounds.played.length;
      await app.tapKey('key-2');
      expect(since(n), ['xylo_2']);
      n = app.sounds.played.length;
      await app.drag(app.centre('key-0'), app.centre('key-4'), steps: 12);
      expect(since(n), ['xylo_0', 'xylo_1', 'xylo_2', 'xylo_3', 'xylo_4'], reason: 'a slide plays every key on the way: 「刷～」');
      expect(find.byKey(const ValueKey('key-5')), findsNothing, reason: '小小 has five keys');
      await shot('02_tap_xylo');
      await app.tapKey('instrument-drum', ms: 600);
      n = app.sounds.played.length;
      await app.tapKey('key-0');
      expect(since(n), ['drum_0']);
      await shot('03_tap_drum');
      await app.tapKey('instrument-pot', ms: 600);
      n = app.sounds.played.length;
      await app.tapKey('key-4');
      expect(since(n), ['pot_4']);
      expect(app.voice.said, contains('鍋碗瓢盆'));
      await shot('04_tap_pot');
      await app.tapKey('home', ms: 800);
      expect(app.location, '/');

      // 動物樂團: tap one up, drag two up, they sing together on the beat.
      await app.tapKey('toy-band', ms: 900);
      expect(app.location, '/toy/band');
      expect(app.sounds.bandTempo, Tempo.normal);
      expect(app.sounds.bandAvailable.length, 10);
      await app.tapKey('tray-bear', ms: 500);
      expect(app.sounds.singing, {Animal.bear}, reason: 'a tap sends it to the first free spot');
      await app.drag(app.centre('tray-frog'), app.centre('spot-1'));
      await app.drag(app.centre('tray-blackbear'), app.centre('spot-2'));
      expect(app.sounds.singing, {Animal.bear, Animal.frog, Animal.blackbear});
      expect(app.voice.said, contains('台灣黑熊來唱歌了！'));
      await app.settle(600);
      await shot('05_band');
      n = app.sounds.played.length;
      await app.drag(app.centre('tray-leopard'), app.centre('spot-3'));
      expect(since(n), containsAll(['join', 'applause']), reason: 'a full band: the audience claps');
      await app.settle(500);
      await shot('06_band_full');
      await app.tapKey('tempo', ms: 500);
      expect(app.sounds.bandTempo, Tempo.fast);
      expect(app.sounds.singing.length, 4, reason: 'a new speed keeps everyone singing');
      // Off the stage again: drag the frog down to the row.
      await app.drag(app.centre('spot-1'), app.centre('tray-duck'));
      expect(app.sounds.singing, {Animal.bear, Animal.blackbear, Animal.leopard});
      // Tap an animal on the stage: it calls.
      n = app.sounds.played.length;
      await app.tapKey('spot-0');
      expect(since(n), ['call_bear']);
      await app.tapKey('home', ms: 800);
      expect(app.sounds.bandOn, isFalse, reason: 'the band stops off its page');
      expect(app.container.read(bandProvider).onStage.length, 3, reason: 'and is still on the stage when the child comes back');
      await shot('07_stage_band');

      // 音樂木頭人: dance, then the music stops; a tap only gets a 「噓」.
      await app.tapKey('toy-freeze', ms: 800);
      expect(app.sounds.musicNow, Music.freeze);
      n = app.sounds.played.length;
      await tester.tap(find.byKey(const ValueKey('freeze-area')));
      await app.settle(300);
      expect(since(n), ['sparkle']);
      await shot('08_freeze_dance');
      // 小小: the music plays 6 to 10 s, a warning, then the stop.
      for (var i = 0; i < 24 && !app.sounds.played.contains('freeze_stop'); i++) {
        await app.settle(500);
      }
      expect(app.sounds.played, contains('freeze_stop'));
      expect(app.voice.said, contains('要停囉……'), reason: '小小 is told the stop is coming');
      expect(app.sounds.musicNow, isNull);
      await app.settle(300);
      await shot('09_freeze_stop');
      n = app.sounds.played.length;
      await tester.tap(find.byKey(const ValueKey('freeze-area')));
      await app.settle(300);
      expect(since(n), ['shh'], reason: 'no penalty, only 噓');
      for (var i = 0; i < 14 && app.sounds.musicNow == null; i++) {
        await app.settle(500);
      }
      expect(app.sounds.musicNow, Music.freeze, reason: 'the music comes back');
      await app.tapKey('home', ms: 800);

      // 高低快慢: the bird up the stairs.
      await app.tapKey('toy-highlow', ms: 800);
      n = app.sounds.played.length;
      await app.drag(app.centre('step-0'), app.centre('step-4'), steps: 10);
      expect(since(n), ['stair_0', 'stair_1', 'stair_2', 'stair_3', 'stair_4'], reason: 'the first touch sings the bird\'s own step');
      expect(app.voice.said, contains('高～'));
      expect(find.byKey(const ValueKey('loud')), findsNothing, reason: '小小 only has high and low');
      await app.settle(400);
      await shot('10_highlow');
      await app.drag(app.centre('step-4'), app.centre('step-1'), steps: 8);
      expect(app.voice.said.last, '低～');
      await app.tapKey('home', ms: 800);

      // 錄下來 (小小): four taps fill the tape; it is kept and played back.
      await app.tapKey('toy-record', ms: 800);
      await app.tapKey('rec', ms: 300);
      for (final k in [0, 2, 4, 3]) {
        await app.tapKey('key-$k', ms: 200);
      }
      expect(app.game.songs.length, 1);
      expect(app.game.songs.first.notes, [0, 2, 4, 3]);
      expect(app.sounds.song.map((s) => s.$1), ['xylo_0', 'xylo_2', 'xylo_4', 'xylo_3']);
      expect(app.sounds.song.map((s) => s.$2.inMilliseconds), [0, 600, 1200, 1800], reason: 'on the beat');
      await app.settle(1000);
      await shot('11_record');
      await app.settle(2500);
      expect(app.sounds.played, contains('applause'));
      await app.tapKey('home', ms: 800);
      expect(find.byKey(const ValueKey('stage-tape-0')), findsOneWidget, reason: 'the song is on the stage');

      // 聽聽看 (小小): two pictures; the right one comes alive.
      await app.tapKey('toy-listen', ms: 800);
      await app.settle(1600);
      final asked = app.sounds.played.lastWhere((s) => s.startsWith('ls_'));
      final answer = StreetSound.values.firstWhere((s) => s.sound == asked);
      expect(find.byWidgetPredicate((w) => w.key is ValueKey<String> && (w.key! as ValueKey<String>).value.startsWith('choice-')), findsNWidgets(2));
      await shot('12_listen');
      final wrong = StreetSound.values.firstWhere((s) => s != answer && find.byKey(ValueKey('choice-${s.name}')).evaluate().isNotEmpty);
      await app.tapKey('choice-${wrong.name}', ms: 300);
      expect(app.voice.said.last, contains('這是${wrong.zh}喔'));
      await app.tapKey('choice-${answer.name}', ms: 600);
      expect(app.sounds.played.last, anyOf('right', asked));
      expect(app.voice.said.last, contains('對！是${answer.zh}'));
      await shot('13_listen_right');
      await app.settle(4500);
      await app.tapKey('home', ms: 800);

      // Parent mode: 大.
      ParentPass.grant();
      app.go('/parent');
      await app.settle(800);
      await shot('14_parent');
      await tester.tap(find.byKey(const ValueKey('level-big')));
      await app.settle();
      expect(app.game.settings.level, Level.big);
      app.go('/');
      await app.settle(600);

      // 大: eight xylophone keys.
      await app.tapKey('toy-tap', ms: 800);
      expect(find.byKey(const ValueKey('key-7')), findsOneWidget);
      await shot('15_tap_big');
      await app.tapKey('home', ms: 800);

      // 大: six spots and 噓 (hold an animal).
      await app.tapKey('toy-band', ms: 900);
      await app.drag(app.centre('tray-cat'), app.centre('spot-5'));
      await app.drag(app.centre('tray-magpie'), app.centre('spot-4'));
      expect(app.sounds.singing, containsAll([Animal.cat, Animal.magpie]));
      final g = await tester.startGesture(app.centre('spot-0'));
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(milliseconds: 400));
      await g.up();
      await app.settle(400);
      expect(app.sounds.singing.contains(Animal.bear), isFalse, reason: 'the bear is told 噓');
      expect(app.container.read(bandProvider).onStage, contains(Animal.bear), reason: 'but stays on the stage');
      await shot('16_band_big');
      await app.tapKey('home', ms: 800);

      // 大: 快慢 and 大小聲.
      await app.tapKey('toy-highlow', ms: 800);
      n = app.sounds.played.length;
      await app.tapKey('loud');
      await app.tapKey('soft');
      expect(since(n), ['loud', 'soft']);
      await app.drag(app.centre('speed-knob'), app.centre('speed-knob') + const Offset(200, 0));
      expect(app.sounds.played.last, 'band_bird_fast');
      expect(app.voice.said, contains('快！'));
      await shot('17_highlow_big');
      await app.tapKey('home', ms: 800);

      // 大: the tape runs on the beat; taps land in the nearest cell.
      await app.tapKey('toy-record', ms: 800);
      await app.tapKey('rec', ms: 100);
      for (final k in [7, 5, 3]) {
        await app.tapKey('key-$k', ms: 600);
      }
      await app.settle(4000);
      expect(app.game.songs.length, 2);
      expect(app.game.songs.first.notes.length, 8);
      expect(app.game.songs.first.count, 3);
      await shot('18_record_big');
      await app.settle(5000);
      await app.tapKey('home', ms: 800);

      // 大: four pictures.
      await app.tapKey('toy-listen', ms: 800);
      await app.settle(1600);
      expect(find.byWidgetPredicate((w) => w.key is ValueKey<String> && (w.key! as ValueKey<String>).value.startsWith('choice-')), findsNWidgets(4));
      await shot('19_listen_big');
      await app.tapKey('home', ms: 800);

      // The free version: 錄下來 and 聽聽看 are locked; four animals too.
      app.change((g) => g.copyWith(settings: g.settings.copyWith(full: false)));
      await app.settle(600);
      n = app.sounds.played.length;
      await app.tapKey('toy-record', ms: 600);
      expect(app.location, '/');
      expect(since(n), ['lock']);
      expect(app.voice.said.last, contains('爸爸媽媽'));
      await shot('20_stage_free');
      app.go('/toy/listen');
      await app.settle();
      expect(app.location, '/', reason: 'a locked toy does not open from a link either');
      await app.tapKey('toy-band', ms: 900);
      expect(app.sounds.bandAvailable.length, 6);
      expect(app.container.read(bandProvider).onStage.any((a) => !a.free), isFalse, reason: 'the full version\'s animals step off');
      app.change((g) => g.copyWith(settings: g.settings.copyWith(full: true)));
      await app.tapKey('home', ms: 800);

      // The play time runs out: the lights go out one by one.
      app.now = app.now.add(const Duration(minutes: 16));
      await app.settle(2600);
      expect(app.location, '/rest');
      expect(app.sounds.musicNow, Music.rest);
      await app.settle(3000);
      expect(app.sounds.played, contains('lights_off'));
      await shot('21_rest_lights');
      await app.settle(7000);
      expect(app.sounds.played.last, 'night');
      expect(app.voice.said.any((s) => s.contains('換你去做了')), isTrue);
      await shot('22_rest');
      expect(app.game.today!.seconds, greaterThan(15 * 60), reason: 'today\'s minutes are counted for the parent');
      expect(app.game.today!.opens[Toy.band], 3);
      await app.end();
    }, timeout: const Timeout(Duration(minutes: 12)));
  }

  testWidgets('a song recorded when the time runs out is kept', (tester) async {
    final app = await TestApp.start(tester, game: const Game(settings: Settings(minutes: 5)));
    await app.tapKey('toy-record', ms: 600);
    await app.tapKey('rec', ms: 200);
    await app.tapKey('key-1', ms: 200);
    app.now = app.now.add(const Duration(minutes: 6));
    await app.settle(2600);
    expect(app.location, '/rest');
    expect(app.game.songs.single.notes, [1, null, null, null]);
    await app.end();
  });
}
