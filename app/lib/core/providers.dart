import 'dart:math' as math;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'content.dart';
import 'game.dart';
import 'sounds.dart';
import 'store.dart';
import 'voice.dart';

/// What time it is (tests and screenshots set it). Used for the play-time
/// limit and today's minutes.
final clockProvider = Provider<DateTime Function()>((ref) => DateTime.now);

/// Dice (tests give a seeded one).
final randomProvider = Provider<math.Random>((ref) => math.Random());

final storeProvider = Provider<GameStore>((ref) => MemoryStore());
final savedGameProvider = Provider<Game>((ref) => const Game());
final soundsProvider = Provider<Sounds>((ref) => const SilentSounds());
final voiceProvider = Provider<Voice>((ref) => const SilentVoice());

/// Everything kept; every change is saved straight away.
final gameProvider = NotifierProvider<GameNotifier, Game>(GameNotifier.new);

class GameNotifier extends Notifier<Game> {
  @override
  Game build() => ref.read(savedGameProvider);

  void change(Game Function(Game g) f) {
    final next = f(state);
    if (identical(next, state)) return;
    state = next;
    ref.read(storeProvider).write(next.toJson());
  }

  void settings(Settings Function(Settings s) f) => change((g) => g.copyWith(settings: f(g.settings)));
}

/// When this sitting started (reset when a parent lets play go on).
final sessionStartProvider = NotifierProvider<SessionStart, DateTime>(SessionStart.new);

class SessionStart extends Notifier<DateTime> {
  @override
  DateTime build() => ref.read(clockProvider)();

  void restart() => state = ref.read(clockProvider)();
}

/// Who is on the band's stage, in which spot (kept while the app is open, so
/// the band is still there when the child comes back to it), and how fast.
final bandProvider = NotifierProvider<BandNotifier, BandState>(BandNotifier.new);

class BandState {
  const BandState({this.spots = const {}, this.shushed = const {}, this.tempo = Tempo.normal});

  /// Spot number → the animal standing there.
  final Map<int, Animal> spots;

  /// Animals told 「噓」 (大): on stage, not singing.
  final Set<Animal> shushed;
  final Tempo tempo;

  Set<Animal> get onStage => spots.values.toSet();
  Set<Animal> get singing => onStage.difference(shushed);

  BandState copyWith({Map<int, Animal>? spots, Set<Animal>? shushed, Tempo? tempo}) =>
      BandState(spots: spots ?? this.spots, shushed: shushed ?? this.shushed, tempo: tempo ?? this.tempo);
}

class BandNotifier extends Notifier<BandState> {
  @override
  BandState build() => const BandState();

  /// [a] goes to [spot] (from wherever it was; whoever stood there steps off).
  void put(Animal a, int spot) {
    final spots = {...state.spots}..removeWhere((_, x) => x == a);
    spots[spot] = a;
    state = state.copyWith(spots: spots);
  }

  void remove(Animal a) => state = state.copyWith(spots: {...state.spots}..removeWhere((_, x) => x == a), shushed: {...state.shushed}..remove(a));

  void shush(Animal a) => state = state.copyWith(shushed: state.shushed.contains(a) ? ({...state.shushed}..remove(a)) : {...state.shushed, a});

  void tempo(Tempo t) => state = state.copyWith(tempo: t);

  /// Only [spots] spots now (the level changed); and only animals that may play.
  void fit(int spots, List<Animal> available) => state = state.copyWith(
        spots: {for (final e in state.spots.entries) if (e.key < spots && available.contains(e.value)) e.key: e.value},
        shushed: state.shushed.where(available.contains).toSet(),
      );
}

/// Things said once per app start (the welcome).
final onceProvider = Provider<Set<String>>((ref) => <String>{});
