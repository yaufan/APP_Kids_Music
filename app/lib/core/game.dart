import 'content.dart';

/// What the parent set (docs/design.md 「家長模式」).
class Settings {
  const Settings({
    this.level = Level.small,
    this.minutes = 15,
    this.off = const {},
    this.music = true,
    this.sounds = true,
    this.voice = true,
    this.english = false,
    this.volume = 0.7,
    this.full = true,
  });

  final Level level;

  /// How long one sitting may be before a rest.
  final int minutes;

  /// Toys the parent turned off (the drums at night…).
  final Set<Toy> off;
  final bool music;
  final bool sounds;
  final bool voice;
  final bool english;

  /// The loudest the app plays (for small ears), 0.3 to 1.
  final double volume;

  /// The full version (all ten animals, 錄下來, 聽聽看); on while testing.
  final bool full;

  static const minuteChoices = [5, 10, 15, 20, 30];
  static const volumeChoices = [0.3, 0.5, 0.7, 0.85, 1.0];

  /// Whether [t] shows on the stage, and whether it opens.
  bool shows(Toy t) => !off.contains(t);
  bool opens(Toy t) => shows(t) && (full || t.free);

  Settings copyWith({Level? level, int? minutes, Set<Toy>? off, bool? music, bool? sounds, bool? voice, bool? english, double? volume, bool? full}) => Settings(
        level: level ?? this.level,
        minutes: minutes ?? this.minutes,
        off: off ?? this.off,
        music: music ?? this.music,
        sounds: sounds ?? this.sounds,
        voice: voice ?? this.voice,
        english: english ?? this.english,
        volume: volume ?? this.volume,
        full: full ?? this.full,
      );

  Map<String, dynamic> toJson() => {
        'level': level.name,
        'minutes': minutes,
        'off': [for (final t in off) t.name],
        'music': music,
        'sounds': sounds,
        'voice': voice,
        'english': english,
        'volume': volume,
        'full': full,
      };

  factory Settings.fromJson(Map<String, dynamic> j) {
    final m = j['minutes'], off = j['off'], v = j['volume'];
    bool flag(String k, bool d) => j[k] is bool ? j[k] as bool : d;
    return Settings(
      level: Level.values.asNameMap()[j['level']] ?? Level.small,
      minutes: m is int && minuteChoices.contains(m) ? m : 15,
      off: {
        if (off is List)
          for (final n in off) ?Toy.values.asNameMap()[n],
      },
      music: flag('music', true),
      sounds: flag('sounds', true),
      voice: flag('voice', true),
      english: flag('english', false),
      volume: v is num && v >= 0.3 && v <= 1 ? v.toDouble() : 0.7,
      full: flag('full', true),
    );
  }
}

/// A little song the child recorded (錄下來): the keys hit, cell by cell, on
/// one instrument. Kept on the phone only.
class Song {
  const Song({required this.instrument, required this.notes, required this.colour, required this.made});

  final Instrument instrument;

  /// One entry per cell: the key, or null for a rest.
  final List<int?> notes;

  /// Which of the eight tape colours.
  final int colour;
  final DateTime made;

  static const maxCells = 16;

  int get count => notes.where((n) => n != null).length;

  Map<String, dynamic> toJson() => {
        'instrument': instrument.name,
        'notes': notes,
        'colour': colour,
        'made': made.toIso8601String(),
      };

  /// Null for anything that is not a sound song.
  static Song? fromJson(Object? j) {
    if (j is! Map) return null;
    final ins = Instrument.values.asNameMap()[j['instrument']];
    final notes = j['notes'], made = j['made'] is String ? DateTime.tryParse(j['made'] as String) : null;
    if (ins == null || notes is! List || notes.isEmpty || notes.length > maxCells || made == null) return null;
    final keys = <int?>[];
    for (final n in notes) {
      if (n == null) {
        keys.add(null);
      } else if (n is int && n >= 0 && n < ins.keys.length) {
        keys.add(n);
      } else {
        return null;
      }
    }
    final c = j['colour'];
    return Song(instrument: ins, notes: keys, colour: c is int && c >= 0 ? c % 8 : 0, made: made);
  }
}

/// What was played on one day (for the parent: how long, which toy most).
class Today {
  const Today({required this.day, this.seconds = 0, this.opens = const {}});

  /// yyyy-mm-dd.
  final String day;
  final int seconds;
  final Map<Toy, int> opens;

  static String key(DateTime t) => '${t.year}-${t.month.toString().padLeft(2, '0')}-${t.day.toString().padLeft(2, '0')}';

  Toy? get favourite {
    Toy? best;
    for (final e in opens.entries) {
      if (best == null || e.value > opens[best]!) best = e.key;
    }
    return best;
  }

  Map<String, dynamic> toJson() => {'day': day, 'seconds': seconds, 'opens': {for (final e in opens.entries) e.key.name: e.value}};

  static Today? fromJson(Object? j) {
    if (j is! Map || j['day'] is! String) return null;
    final o = j['opens'];
    return Today(
      day: j['day'] as String,
      seconds: j['seconds'] is int ? j['seconds'] as int : 0,
      opens: {
        if (o is Map)
          for (final e in o.entries)
            if (Toy.values.asNameMap()[e.key] case final t? when e.value is int) t: e.value as int,
      },
    );
  }
}

/// Everything kept: the settings, the songs (newest first, at most 8), today,
/// and when the rest began. One small file (store.dart).
class Game {
  const Game({this.settings = const Settings(), this.songs = const [], this.today, this.restSince});

  final Settings settings;
  final List<Song> songs;
  final Today? today;
  final DateTime? restSince;

  static const maxSongs = 8;
  static const restLength = Duration(hours: 1);

  bool resting(DateTime now) => restSince != null && now.difference(restSince!) < restLength;

  Game copyWith({Settings? settings, List<Song>? songs, Today? today, DateTime? restSince, bool clearRest = false}) => Game(
        settings: settings ?? this.settings,
        songs: songs ?? this.songs,
        today: today ?? this.today,
        restSince: clearRest ? null : (restSince ?? this.restSince),
      );

  Game rest(DateTime now) => copyWith(restSince: now);
  Game playOn() => copyWith(clearRest: true);

  /// A new song goes first; the oldest drops off past [maxSongs]. An empty one is not kept.
  Game keep(Song s) {
    if (s.count == 0) return this;
    return copyWith(songs: [s, ...songs].take(maxSongs).toList());
  }

  Game forget(int i) => i < 0 || i >= songs.length ? this : copyWith(songs: [...songs]..removeAt(i));

  /// The next tape colour (round the eight).
  int get nextColour => songs.isEmpty ? 0 : (songs.first.colour + 1) % 8;

  Today _today(DateTime now) {
    final k = Today.key(now);
    final t = today;
    return t != null && t.day == k ? t : Today(day: k);
  }

  Game opened(Toy toy, DateTime now) {
    final t = _today(now);
    return copyWith(today: Today(day: t.day, seconds: t.seconds, opens: {...t.opens, toy: (t.opens[toy] ?? 0) + 1}));
  }

  Game played(Duration d, DateTime now) {
    final t = _today(now);
    return copyWith(today: Today(day: t.day, seconds: t.seconds + d.inSeconds, opens: t.opens));
  }

  Map<String, dynamic> toJson() => {
        'version': 1,
        'settings': settings.toJson(),
        'songs': [for (final s in songs) s.toJson()],
        if (today != null) 'today': today!.toJson(),
        if (restSince != null) 'restSince': restSince!.toIso8601String(),
      };

  /// Whatever the file holds, a game comes out (a broken part is left out).
  factory Game.fromJson(Map<String, dynamic>? j) {
    if (j == null) return const Game();
    final s = j['settings'], songs = j['songs'], rest = j['restSince'];
    return Game(
      settings: s is Map<String, dynamic> ? Settings.fromJson(s) : const Settings(),
      songs: [
        if (songs is List)
          for (final x in songs) ?Song.fromJson(x),
      ].take(maxSongs).toList(),
      today: Today.fromJson(j['today']),
      restSince: rest is String ? DateTime.tryParse(rest) : null,
    );
  }
}
