// Records a demo video of 小小音樂家 being played: a scripted child (a white
// dot where the finger is) with a caption under the phone screen; the music,
// the band and the sounds the app asked for are written down and mixed in
// afterwards by tools/demo_audio.py.
//
//   flutter test test/demo/demo_video_test.dart --dart-define=DEMO=true
//   python3 ../tools/demo_audio.py
//
// Needs ffmpeg; writes build/demo/demo.mp4, chapters.txt and sounds.txt.
// Skipped in normal test runs.
import 'dart:io';
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:little_musician/app/app.dart';
import 'package:little_musician/core/content.dart';
import 'package:little_musician/core/game.dart';
import 'package:little_musician/core/providers.dart';
import 'package:little_musician/core/sounds.dart';
import 'package:little_musician/core/store.dart';
import 'package:little_musician/core/voice.dart';
import 'package:little_musician/features/parent/parent_gate.dart';

import '../helpers.dart' show loadFonts;

const _phone = Size(390, 844);
const _captionHeight = 84.0;
const _fps = 10;
const _demo = bool.fromEnvironment('DEMO');

void main() {
  testWidgets('demo video', skip: !_demo, (tester) async {
    await tester.runAsync(loadFonts);
    tester.view.physicalSize = Size(_phone.width * 3, (_phone.height + _captionHeight) * 3);
    tester.view.devicePixelRatio = 3;
    addTearDown(tester.view.reset);

    var frameCount = 0;
    var now = DateTime(2026, 11, 15, 10);
    final lines = <String>[];
    final track = RecordingSounds(onChange: (l) => lines.add('$frameCount $l'));
    final finger = ValueNotifier<Offset?>(null);
    final caption = ValueNotifier<String>('');
    final key = GlobalKey();
    final store = MemoryStore();
    await tester.pumpWidget(RepaintBoundary(
      key: key,
      child: Directionality(
        textDirection: TextDirection.ltr,
        child: Column(children: [
          SizedBox.fromSize(
            size: _phone,
            child: MediaQuery(
              data: const MediaQueryData(size: _phone, devicePixelRatio: 3, padding: EdgeInsets.only(top: 24)),
              child: Stack(children: [
                ProviderScope(
                  overrides: [
                    storeProvider.overrideWithValue(store),
                    savedGameProvider.overrideWithValue(const Game()),
                    soundsProvider.overrideWithValue(track),
                    voiceProvider.overrideWithValue(const SilentVoice()),
                    randomProvider.overrideWithValue(math.Random(7)),
                    clockProvider.overrideWithValue(() => now),
                  ],
                  child: const LittleMusicianApp(),
                ),
                IgnorePointer(child: ValueListenableBuilder(valueListenable: finger, builder: (_, at, _) => _Finger(at))),
              ]),
            ),
          ),
          SizedBox(
            width: _phone.width,
            height: _captionHeight,
            child: ColoredBox(
              color: const Color(0xFF3B2F7A),
              child: Center(
                child: ValueListenableBuilder(
                  valueListenable: caption,
                  builder: (_, text, _) => Text(text, textAlign: TextAlign.center, style: const TextStyle(fontFamily: 'Huninn', color: Colors.white, fontSize: 17, height: 1.35)),
                ),
              ),
            ),
          ),
        ]),
      ),
    ));

    final rec = (await tester.runAsync(() => _Recorder.start(key)))!;
    final marks = <String>[];
    void mark(String name) => marks.add('$name $frameCount');
    Future<void> frames(int n) async {
      for (var i = 0; i < n; i++) {
        frameCount++;
        await tester.runAsync(() async {
          await rec.capture();
          await Future<void>.delayed(const Duration(milliseconds: 12));
        });
        await tester.pump(const Duration(milliseconds: 1000 ~/ _fps));
      }
    }

    Future<void> seconds(double s) => frames((s * _fps).round());
    Future<void> touch(Offset at) async {
      finger.value = at;
      await frames(1);
      await tester.tapAt(at);
      await frames(2);
      finger.value = null;
    }

    Offset at(String k) => tester.getCenter(find.byKey(ValueKey(k)).last);
    Future<void> tap(String k) => touch(at(k));
    Future<void> slide(Offset from, Offset to, {int steps = 6}) async {
      finger.value = from;
      final g = await tester.startGesture(from);
      await frames(1);
      for (var i = 1; i <= steps; i++) {
        final p = Offset.lerp(from, to, i / steps)!;
        await g.moveTo(p);
        finger.value = p;
        await frames(1);
      }
      await g.up();
      finger.value = null;
      await frames(2);
    }

    ProviderContainer container() => ProviderScope.containerOf(tester.element(find.byType(LittleMusicianApp)));
    void change(Game Function(Game) f) => container().read(gameProvider.notifier).change(f);

    // The stage.
    mark('stage');
    caption.value = '小小音樂家：給 2～5 歲的音樂玩具\n隨便敲、隨便拖，都好聽';
    await seconds(3);
    caption.value = '一個舞台，六個發光的玩具';
    await seconds(2);

    // 敲敲樂.
    mark('tap');
    await tap('toy-tap');
    caption.value = '敲敲樂：手指一碰就響\n全部是 Do Re Mi Sol La，怎麼敲都好聽';
    await seconds(1);
    for (final k in [0, 2, 4, 3, 2]) {
      await tap('key-$k');
      await frames(2);
    }
    caption.value = '手指滑過去，是一串「刷～」';
    await slide(at('key-0'), at('key-4'), steps: 10);
    await slide(at('key-4'), at('key-0'), steps: 10);
    caption.value = '還有鼓，和家裡的鍋碗瓢盆';
    await tap('instrument-drum');
    for (final k in [0, 3, 0, 3, 4]) {
      await tap('key-$k');
      await frames(2);
    }
    await tap('instrument-pot');
    for (final k in [0, 2, 4, 1]) {
      await tap('key-$k');
      await frames(2);
    }
    await tap('home');
    await seconds(1);

    // 動物樂團.
    mark('band');
    await tap('toy-band');
    caption.value = '動物樂團：把動物拖上舞台\n牠就唱自己的那一小段';
    await seconds(1.5);
    await slide(at('tray-bear'), at('spot-0'));
    await seconds(3);
    caption.value = '新上台的等下一小節才開始\n所以永遠對拍、一定好聽';
    await slide(at('tray-bird'), at('spot-1'));
    await seconds(3);
    caption.value = '台灣黑熊：每小節第一拍「咚」';
    await slide(at('tray-blackbear'), at('spot-2'));
    await seconds(3);
    caption.value = '點一下也會上台；放滿了，觀眾喊「安可」';
    await tap('tray-leopard');
    await seconds(4);
    caption.value = '兔子按鈕：大家一起變快';
    await tap('tempo');
    await seconds(4);
    await tap('home');
    await seconds(1);

    // 音樂木頭人.
    mark('freeze');
    await tap('toy-freeze');
    caption.value = '音樂木頭人：音樂放的時候點一點\n動物跳舞';
    for (var i = 0; i < 6; i++) {
      await touch(const Offset(195, 600));
      await seconds(0.4);
    }
    caption.value = '音樂停了：停！不要動～';
    for (var i = 0; i < 120 && !track.played.contains('freeze_stop'); i++) {
      await frames(1);
    }
    await seconds(1.5);
    caption.value = '點了也沒處罰，只有「噓～」\n忍住不動，動物會歡呼';
    await touch(const Offset(195, 600));
    for (var i = 0; i < 80 && track.musicNow == null; i++) {
      await frames(1);
    }
    await seconds(2.5);
    await tap('home');
    await seconds(1);

    // 大: 高低快慢.
    mark('highlow');
    change((g) => g.copyWith(settings: g.settings.copyWith(level: Level.big)));
    await tap('toy-highlow');
    caption.value = '高低快慢：把小鳥拖上樓梯\n越高叫聲越高';
    await seconds(1);
    await slide(at('step-0'), at('step-4'), steps: 12);
    await slide(at('step-4'), at('step-0'), steps: 12);
    caption.value = '（大）快慢：蝸牛到兔子；大小聲：小象和小老鼠';
    await slide(at('speed-knob'), at('speed-knob') + const Offset(110, 0));
    await seconds(2.5);
    await tap('loud');
    await seconds(1.2);
    await tap('soft');
    await seconds(1.2);
    await tap('home');
    await seconds(1);

    // 錄下來.
    mark('record');
    await tap('toy-record');
    caption.value = '錄下來：不用麥克風，錄的是「敲了哪個鍵」\n（大）照拍子跑，敲的音貼到最近的一格';
    await seconds(1);
    await tap('rec');
    for (final k in [0, 2, 4, 5, 4, 2, 3, 0]) {
      await seconds(0.25);
      await tap('key-$k');
    }
    caption.value = '錄完自動存起來，動物演一次給你聽';
    await seconds(8);
    await tap('home');
    await seconds(1);

    // 聽聽看.
    mark('listen');
    await tap('toy-listen');
    caption.value = '聽聽看：台灣生活的聲音\n垃圾車、機車、捷運、廟裡的鼓……';
    await seconds(2.5);
    final asked = track.played.lastWhere((s) => s.startsWith('ls_'));
    final answer = StreetSound.values.firstWhere((s) => s.sound == asked);
    final wrong = StreetSound.values.firstWhere((s) => s != answer && find.byKey(ValueKey('choice-${s.name}')).evaluate().isNotEmpty);
    caption.value = '點錯沒關係：「這是${wrong.zh}喔」，再聽一次';
    await tap('choice-${wrong.name}');
    await seconds(3);
    caption.value = '點對了，那張圖活起來！';
    await tap('choice-${answer.name}');
    await seconds(3.5);
    await tap('home');
    await seconds(1);

    // Rest.
    mark('rest');
    now = now.add(const Duration(minutes: 15, seconds: 1));
    caption.value = '家長設定的時間到了（預設 15 分鐘）\n霓虹燈一盞一盞暗下來';
    await seconds(6);
    caption.value = '布幕合起來：換你去做了！';
    await seconds(5);

    // Parent mode.
    mark('parent');
    caption.value = '家長答對題目，才能再玩或進家長模式';
    const digits = {'零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9};
    await touch(tester.getCenter(find.bySemanticsLabel('家長').last));
    await seconds(1);
    final parts = (find.textContaining('加').evaluate().first.widget as Text).data!.split(' ');
    for (final d in '${digits[parts[0]]! + digits[parts[2]]!}'.split('')) {
      await touch(tester.getCenter(find.byKey(ValueKey('gate-key-$d'))));
    }
    await seconds(1.5);
    expect(ParentPass.take(), isFalse);
    caption.value = '';
    mark('end');

    await tester.runAsync(() async {
      await rec.finish();
      File('build/demo/chapters.txt').writeAsStringSync('${marks.join('\n')}\n');
      File('build/demo/sounds.txt').writeAsStringSync('fps $_fps\nframes $frameCount\n${lines.join('\n')}\n');
    });
    await tester.pumpWidget(const SizedBox());
    await tester.pump(const Duration(milliseconds: 100));
  }, timeout: const Timeout(Duration(minutes: 40)));
}

class _Finger extends StatelessWidget {
  const _Finger(this.at);

  final Offset? at;

  @override
  Widget build(BuildContext context) {
    final p = at;
    if (p == null) return const SizedBox.expand();
    return Stack(children: [
      Positioned(
        left: p.dx - 22,
        top: p.dy - 22,
        child: Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.white.withValues(alpha: 0.55),
            border: Border.all(color: const Color(0xFF3B2F7A).withValues(alpha: 0.6), width: 3),
          ),
        ),
      ),
    ]);
  }
}

/// Streams frames of [key]'s boundary into ffmpeg.
class _Recorder {
  _Recorder(this._key, this._ffmpeg);

  final GlobalKey _key;
  final Process _ffmpeg;

  static Future<_Recorder> start(GlobalKey key) async {
    Directory('build/demo').createSync(recursive: true);
    final size = Size(_phone.width * 2, (_phone.height + _captionHeight) * 2);
    final ffmpeg = await Process.start('ffmpeg', [
      '-y', '-loglevel', 'error',
      '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '${size.width.toInt()}x${size.height.toInt()}', '-r', '$_fps', '-i', '-',
      '-vf', 'fps=30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '24', '-movflags', '+faststart', 'build/demo/demo_silent.mp4',
    ]);
    ffmpeg.stderr.listen(stderr.add);
    return _Recorder(key, ffmpeg);
  }

  Future<void> capture() async {
    final boundary = _key.currentContext!.findRenderObject()! as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 2);
    final bytes = await image.toByteData(format: ui.ImageByteFormat.rawRgba);
    image.dispose();
    _ffmpeg.stdin.add(bytes!.buffer.asUint8List());
    await _ffmpeg.stdin.flush();
  }

  Future<void> finish() async {
    await _ffmpeg.stdin.flush();
    await _ffmpeg.stdin.close();
    final code = await _ffmpeg.exitCode;
    if (code != 0) throw StateError('ffmpeg failed ($code)');
  }
}
