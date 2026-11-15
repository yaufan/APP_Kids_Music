import 'dart:math' as math;

import 'content.dart';

/// The band's clock (docs/design.md 「技術」): the beat, the bar and the loop
/// at one tempo, counted from the moment every loop started together. All
/// times are durations since that moment; the sound engine schedules on its
/// own clock with these numbers, so nothing here depends on how fast the
/// phone is.
class MusicClock {
  const MusicClock(this.bpm, {this.beatsPerBar = 4, this.bars = 2});

  factory MusicClock.of(Tempo t) => MusicClock(t.bpm);

  final int bpm;
  final int beatsPerBar;

  /// Bars in one loop.
  final int bars;

  /// One beat, exact to the microsecond (80, 100 and 120 beats a minute divide a minute evenly).
  Duration get beat => Duration(microseconds: 60000000 ~/ bpm);
  Duration get bar => beat * beatsPerBar;
  Duration get loop => bar * bars;

  /// Samples in one loop at [rate] (the sound files are exactly this long).
  int loopSamples(int rate) => rate * 60 * beatsPerBar * bars ~/ bpm;

  /// Beats since the start (with the fraction), for moving on the beat.
  double beatsAt(Duration t) => t.inMicroseconds / beat.inMicroseconds;

  /// Which bar of the loop [t] falls in (0 or 1).
  int barInLoop(Duration t) => (t.inMicroseconds ~/ bar.inMicroseconds) % bars;

  /// The first bar line at or after [t] + [lead] (an animal joining waits for
  /// it; [lead] leaves the engine time to schedule the fade).
  Duration nextBar(Duration t, {Duration lead = Duration.zero}) {
    final at = t + lead;
    if (at <= Duration.zero) return Duration.zero;
    final b = bar.inMicroseconds;
    final k = (at.inMicroseconds + b - 1) ~/ b;
    return Duration(microseconds: k * b);
  }

  /// How long until the next bar line.
  Duration untilNextBar(Duration t, {Duration lead = Duration.zero}) => nextBar(t, lead: lead) - t;
}

/// A recording on the tape (錄下來): which key was hit in each cell. Nothing is
/// recorded but the keys (no microphone).
class Tape {
  Tape(this.length) : cells = List<int?>.filled(length, null);

  /// 小小 gets 4 cells, 大 8.
  static int lengthFor(Level level) => level == Level.small ? 4 : 8;

  /// One cell is one beat at 100 beats a minute.
  static const cell = Duration(milliseconds: 600);

  final int length;
  final List<int?> cells;

  bool get full => cells.every((c) => c != null);
  bool get empty => cells.every((c) => c == null);
  int get filled => cells.where((c) => c != null).length;

  /// 小小: every tap goes in the next empty cell (no timing to get right).
  /// Returns the cell, or null when the tape is full.
  int? step(int key) {
    final i = cells.indexOf(null);
    if (i < 0) return null;
    cells[i] = key;
    return i;
  }

  /// 大: the tap goes in the cell nearest to when it came, [elapsed] after
  /// recording started (so playback is always on the beat). A later tap in
  /// the same cell takes its place. Null once the tape has run out.
  int? timed(int key, Duration elapsed) {
    final i = cellAt(elapsed);
    if (i == null) return null;
    cells[i] = key;
    return i;
  }

  /// The nearest cell to [elapsed], or null past the end.
  int? cellAt(Duration elapsed) {
    if (elapsed.isNegative) return 0;
    final i = (elapsed.inMicroseconds / cell.inMicroseconds).round();
    return i < length ? i : null;
  }

  /// How long a timed recording runs (the last cell, and half a cell for a late tap).
  Duration get runs => cell * length + cell * 0.5;
}

/// One part of 音樂木頭人.
enum FreezeKind {
  /// The music plays: dance, tap anywhere.
  play,

  /// 小小 only: 「要停囉……」 the stop is coming.
  warn,

  /// The music has stopped: do not move.
  stop,

  /// 大 only: a pretend stop, half a beat, then the music goes on.
  fake,
}

class FreezePhase {
  const FreezePhase(this.kind, this.length);

  final FreezeKind kind;
  final Duration length;

  @override
  String toString() => '${kind.name} ${length.inMilliseconds} ms';
}

/// When the music stops in 音樂木頭人 (docs/design.md): 小小 gets a warning and
/// long stops (3 to 5 s); 大 gets quick, random stops (1 to 4 s) and now and
/// then a pretend one. There is no score and no penalty: a tap during a stop
/// only gets a 「噓～」, and staying still gets a cheer.
class FreezePlan {
  FreezePlan(this.level, this.random);

  final Level level;
  final math.Random random;

  Duration _between(double lo, double hi) => Duration(milliseconds: (1000 * (lo + random.nextDouble() * (hi - lo))).round());

  /// The music, then a stop (and for 小小 the warning between).
  List<FreezePhase> round() {
    if (level == Level.small) {
      return [
        FreezePhase(FreezeKind.play, _between(6, 10)),
        const FreezePhase(FreezeKind.warn, Duration(milliseconds: 1500)),
        FreezePhase(FreezeKind.stop, _between(3, 5)),
      ];
    }
    final out = [FreezePhase(FreezeKind.play, _between(3, 8))];
    if (random.nextDouble() < 0.25) {
      out
        ..add(const FreezePhase(FreezeKind.fake, Duration(milliseconds: 300)))
        ..add(FreezePhase(FreezeKind.play, _between(2, 4)));
    }
    out.add(FreezePhase(FreezeKind.stop, _between(1, 4)));
    return out;
  }
}

/// What happens to a tap in 音樂木頭人: never a penalty.
enum FreezeTap {
  /// While the music plays: the animals jump higher, streamers.
  dance,

  /// During a stop: 「噓～」, the red light shakes, an animal peeks.
  shh,
}

FreezeTap freezeTap(FreezeKind now) => now == FreezeKind.stop ? FreezeTap.shh : FreezeTap.dance;

/// One question of 聽聽看: a sound, and the pictures to choose from.
class ListenRound {
  const ListenRound(this.answer, this.options);

  final StreetSound answer;
  final List<StreetSound> options;

  /// 小小: two pictures, from different families (rain and a dog, never a
  /// scooter and the MRT). 大: four pictures. [last] is not asked twice in a row.
  factory ListenRound.make(Level level, math.Random r, {required List<StreetSound> pool, StreetSound? last}) {
    final choices = [for (final s in pool) if (s != last || pool.length == 1) s];
    final answer = choices[r.nextInt(choices.length)];
    final others = [for (final s in pool) if (s != answer && (level == Level.big || s.family != answer.family)) s]..shuffle(r);
    final n = level == Level.small ? 2 : 4;
    final options = [answer, ...others.take(n - 1)]..shuffle(r);
    return ListenRound(answer, options);
  }
}
