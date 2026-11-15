import 'package:flutter_test/flutter_test.dart';
import 'package:little_wave/core/content.dart';
import 'package:little_wave/core/game.dart';

import 'helpers.dart';

/// Small things a child does, checked on the real screens.
void main() {
  testWidgets('with both sound switches off, the toys still sound and the freeze game still has its music', (tester) async {
    final app = await TestApp.start(tester, game: const Game(settings: Settings(sounds: false, music: false)));
    expect(app.sounds.musicNow, isNull, reason: 'no background music on the stage');
    await app.tapKey('toy-tap', ms: 600);
    expect(app.sounds.played, isNot(contains('open')), reason: 'the button sound is off');
    await app.tapKey('key-0');
    expect(app.sounds.played, contains('xylo_0'), reason: 'the xylophone is the toy');
    await app.tapKey('home', ms: 600);
    await app.tapKey('toy-freeze', ms: 600);
    expect(app.sounds.musicNow, Music.freeze);
    await app.tapKey('home', ms: 600);
    await app.tapKey('toy-band', ms: 600);
    await app.tapKey('tray-bear', ms: 400);
    expect(app.sounds.singing, {Animal.bear}, reason: 'the band sings');
    await app.end();
  });

  testWidgets('the first touch on the bird\'s own step sings and hops', (tester) async {
    final app = await TestApp.start(tester);
    await app.tapKey('toy-highlow', ms: 600);
    final n = app.sounds.played.length;
    await app.tapKey('step-0');
    expect(app.sounds.played.sublist(n), ['stair_0']);
    await app.tapKey('step-0');
    expect(app.sounds.played.sublist(n), ['stair_0', 'stair_0']);
    await app.end();
  });
}
