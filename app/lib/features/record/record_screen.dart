import 'package:flutter/material.dart';
import 'package:flutter/scheduler.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/widgets.dart';
import '../../core/content.dart';
import '../../core/game.dart';
import '../../core/music.dart';
import '../../core/providers.dart';
import '../../core/sounds.dart';
import '../tap/keys_view.dart';

/// A song's notes for the sound engine: each cell one beat apart.
List<(String, Duration)> songNotes(Song s) => [
      for (var i = 0; i < s.notes.length; i++)
        if (s.notes[i] case final k?) (s.instrument.sound(k), Tape.cell * i),
    ];

/// 錄下來 (docs/design.md): no microphone, it records which keys were hit.
/// The red button starts the tape; 小小 fills one cell per tap, 大 has the
/// tape run on the beat and each tap lands in the nearest cell. When the tape
/// is done the song is kept (at most eight; the oldest goes) and the animals
/// play it back. The tapes below play any kept song again.
class RecordScreen extends ConsumerStatefulWidget {
  const RecordScreen({super.key});

  @override
  ConsumerState<RecordScreen> createState() => _RecordScreenState();
}

enum _Mode { idle, recording, playing }

class _RecordScreenState extends ConsumerState<RecordScreen> with SingleTickerProviderStateMixin {
  late final Sounds _sounds;
  late final GameNotifier _game;
  late final DateTime Function() _clock;
  late final Ticker _ticker;
  Duration _now = Duration.zero;
  Duration _from = Duration.zero;
  var _mode = _Mode.idle;
  Tape? _tape;
  Song? _song;
  int? _cursor;
  var _hops = [0, 0, 0];
  var _say = Strings.recordHint;

  static const _players = [Animal.bird, Animal.frog, Animal.cat];

  bool get _big => ref.read(gameProvider).settings.level == Level.big;

  @override
  void initState() {
    super.initState();
    _sounds = ref.read(soundsProvider);
    _game = ref.read(gameProvider.notifier);
    _clock = ref.read(clockProvider);
    _sounds.hold(this, null);
    _ticker = createTicker(_tick)..start();
    final songs = ref.read(gameProvider).songs;
    if (songs.isNotEmpty) _song = songs.first;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) speak(ref, '${Toy.record.zh}！${Strings.recordHint}');
    });
  }

  @override
  void dispose() {
    // Time up halfway through: what was recorded is kept (just after this
    // page is gone: providers cannot change while the tree is being torn down).
    final tape = _tape;
    if (_mode == _Mode.recording && tape != null && !tape.empty) {
      final game = _game, made = _clock();
      Future(() {
        try {
          game.change((g) => g.keep(Song(instrument: Instrument.xylo, notes: [...tape.cells], colour: g.nextColour, made: made)));
        } catch (_) {}
      });
    }
    _ticker.dispose();
    _sounds.stopSong();
    _sounds.release(this);
    super.dispose();
  }

  void _tick(Duration t) {
    _now = t;
    final e = t - _from;
    switch (_mode) {
      case _Mode.recording:
        final tape = _tape!;
        if (!_big) return;
        final c = (e.inMicroseconds ~/ Tape.cell.inMicroseconds);
        if (c != _cursor && c < tape.length) {
          _sounds.play('tick', volume: 0.6);
          setState(() => _cursor = c);
        }
        if (e >= tape.runs) _finish();
      case _Mode.playing:
        final song = _song!;
        final c = e.inMicroseconds ~/ Tape.cell.inMicroseconds;
        if (c != _cursor) {
          setState(() {
            _cursor = c < song.notes.length ? c : null;
            if (c < song.notes.length && song.notes[c] != null) {
              final who = song.notes[c]! % 3;
              _hops = [for (var i = 0; i < 3; i++) i == who ? _hops[i] + 1 : _hops[i]];
            }
          });
        }
        if (c >= song.notes.length + 1) {
          _sounds.play('applause', volume: 0.7);
          setState(() {
            _mode = _Mode.idle;
            _cursor = null;
          });
        }
      case _Mode.idle:
        break;
    }
  }

  void _record() {
    if (_mode == _Mode.recording) {
      _finish();
      return;
    }
    _sounds.stopSong();
    _sounds.play('rec_start');
    speak(ref, Strings.recording);
    setState(() {
      _tape = Tape(Tape.lengthFor(ref.read(gameProvider).settings.level));
      _mode = _Mode.recording;
      _from = _now;
      _cursor = _big ? 0 : null;
      _say = Strings.recording;
    });
  }

  void _key(int k) {
    if (_mode != _Mode.recording) return;
    final tape = _tape!;
    setState(() {
      if (_big) {
        tape.timed(k, _now - _from);
      } else {
        tape.step(k);
      }
    });
    if (!_big && tape.full) _finish();
  }

  void _keep() {
    final tape = _tape;
    if (tape == null || tape.empty) return;
    Song? song;
    _game.change((g) => g.keep(song = Song(instrument: Instrument.xylo, notes: [...tape.cells], colour: g.nextColour, made: _clock())));
    _song = song;
  }

  void _finish() {
    _sounds.play('rec_stop');
    final had = !(_tape?.empty ?? true);
    _keep();
    setState(() {
      _mode = _Mode.idle;
      _cursor = null;
      _say = had ? Strings.saved : Strings.recordHint;
    });
    if (had) {
      speak(ref, Strings.saved);
      _play();
    }
  }

  void _play([Song? s]) {
    final song = s ?? _song;
    if (song == null || _mode == _Mode.recording) return;
    _sounds.playSong(songNotes(song));
    speak(ref, Strings.playing);
    setState(() {
      _song = song;
      _tape = null;
      _mode = _Mode.playing;
      _from = _now;
      _cursor = null;
      _say = Strings.playing;
    });
  }

  Widget _cells() {
    final len = _tape?.length ?? _song?.notes.length ?? Tape.lengthFor(ref.read(gameProvider).settings.level);
    final notes = _tape?.cells ?? _song?.notes ?? List<int?>.filled(len, null);
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Neon.glass.withValues(alpha: 0.75),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: _mode == _Mode.recording ? Neon.coral : Neon.lavender, width: 2.4),
        boxShadow: [BoxShadow(color: (_mode == _Mode.recording ? Neon.coral : Neon.lavender).withValues(alpha: 0.25), blurRadius: 14)],
      ),
      child: Row(children: [
        for (var i = 0; i < len; i++)
          Expanded(
            child: Semantics(
              key: ValueKey('cell-$i'),
              label: Strings.cell(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 120),
                height: 46,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: i == _cursor ? 0.28 : 0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: i == _cursor ? Neon.yellow : Neon.inkSoft.withValues(alpha: 0.4), width: i == _cursor ? 3 : 1.5),
                ),
                child: Center(
                  child: notes[i] == null
                      ? null
                      : Container(
                          width: 26,
                          height: 26,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Pentatonic.colour(notes[i]!),
                            boxShadow: [BoxShadow(color: Pentatonic.colour(notes[i]!).withValues(alpha: 0.6), blurRadius: 10)],
                          ),
                        ),
                ),
              ),
            ),
          ),
      ]),
    );
  }

  @override
  Widget build(BuildContext context) {
    final level = ref.watch(gameProvider.select((g) => g.settings.level));
    final songs = ref.watch(gameProvider.select((g) => g.songs));
    final recording = _mode == _Mode.recording;
    return ToyPage(
      title: Toy.record.zh,
      child: Column(children: [
        const SizedBox(height: 2),
        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          NeonButton(key: const ValueKey('rec'), label: Strings.rec, caption: Strings.rec, art: ArtPath.ui(recording ? 'stop' : 'rec'), colour: Neon.coral, size: 70, lit: recording, sound: null, onTap: _record),
          const SizedBox(width: 40),
          NeonButton(key: const ValueKey('play'), label: Strings.play, caption: Strings.play, art: ArtPath.ui('play'), colour: Neon.green, size: 70, lit: _mode == _Mode.playing, onTap: _song == null || recording ? null : _play),
        ]),
        const SizedBox(height: 8),
        Padding(padding: const EdgeInsets.symmetric(horizontal: 16), child: _cells()),
        const SizedBox(height: 6),
        SayBubble(text: _say, size: 16),
        SizedBox(
          height: 96,
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
            for (var i = 0; i < 3; i++)
              Hop(trigger: _hops[i], height: 26, child: SizedBox(width: 86, height: 86, child: Art(_players[i].art(_mode == _Mode.playing ? Pose.sing : Pose.idle)))),
          ]),
        ),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 6),
            child: KeysView(instrument: Instrument.xylo, count: Instrument.xylo.count(level), onKey: _key),
          ),
        ),
        if (songs.isNotEmpty)
          SizedBox(
            height: 56,
            child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.symmetric(horizontal: 16), children: [
              for (var i = 0; i < songs.length; i++)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: Semantics(
                    key: ValueKey('tape-$i'),
                    button: true,
                    label: Strings.songN(i + 1),
                    excludeSemantics: true,
                    onTap: () => _play(songs[i]),
                    child: Pressable(onTap: () => _play(songs[i]), child: SizedBox(width: 74, height: 50, child: Art(ArtPath.tape(songs[i].colour)))),
                  ),
                ),
            ]),
          ),
      ]),
    );
  }
}
