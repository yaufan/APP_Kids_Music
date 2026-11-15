import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:little_wave/core/content.dart';
import 'package:little_wave/core/game.dart';
import 'package:little_wave/features/parent/parent_gate.dart';

import 'helpers.dart';

/// Privacy and the parent gate (docs/design.md: no network, no microphone,
/// nothing leaves the phone, parent mode only through the gate).
void main() {
  test('the app asks for no permissions and takes no links from other apps', () {
    final manifest = File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    expect(manifest, isNot(contains('uses-permission')), reason: 'no internet, microphone, location…');
    expect(manifest, contains('android:name="flutter_deeplinking_enabled" android:value="false"'));
    expect(manifest, contains('android:label="小小音波"'));
    final plist = File('ios/Runner/Info.plist').readAsStringSync();
    expect(plist, contains('<key>FlutterDeepLinkingEnabled</key>\n\t<false/>'));
    expect(plist, isNot(contains('NSMicrophoneUsageDescription')));
    expect(File('pubspec.yaml').readAsStringSync(), isNot(contains('source: system')));
    expect(File('android/app/build.gradle.kts').readAsStringSync(), contains('applicationId = "com.yaufan.littlewave"'));
  });

  testWidgets('parent mode and unknown pages cannot be opened without the gate', (tester) async {
    final app = await TestApp.start(tester);
    app.go('/parent');
    await app.settle();
    expect(app.location, '/', reason: 'no pass from the gate');
    ParentPass.grant();
    app.go('/parent');
    await app.settle();
    expect(app.location, '/parent', reason: 'right after the gate');
    app.go('/');
    await app.settle();
    app.go('/parent');
    await app.settle();
    expect(app.location, '/', reason: 'the pass is used up');
    for (final bad in ['/toy/nothing', '/toy/', '/somewhere']) {
      app.go(bad);
      await app.settle();
      expect(app.location, '/', reason: bad);
    }
    await app.end();
  });

  testWidgets('a toy the parent turned off is not on the stage and does not open', (tester) async {
    final app = await TestApp.start(tester, game: const Game(settings: Settings(off: {Toy.tap})));
    expect(find.bySemanticsLabel(Toy.tap.zh), findsNothing);
    app.go('/toy/tap');
    await app.settle();
    expect(app.location, '/');
    app.go('/toy/band');
    await app.settle();
    expect(app.location, '/toy/band');
    await app.end();
  });

  testWidgets('the gate opens for the right answer only', (tester) async {
    final app = await TestApp.start(tester);
    final c = ParentGateChallenge(4, 5);
    expect(c.question, contains('四 加 五'));
    expect(c.check('9'), isTrue);
    expect(c.check('8'), isFalse);
    await app.tapLabel('家長', ms: 600);
    expect(find.byType(ParentGatePage), findsOneWidget);
    await app.end();
  });
}
