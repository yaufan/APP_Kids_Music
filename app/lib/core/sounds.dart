import 'dart:async';

import 'package:flutter/widgets.dart';
import 'package:flutter_soloud/flutter_soloud.dart';

import 'content.dart';
import 'music.dart';

/// Everything the app plays goes through here (docs/design.md 「技術」). The
/// app uses [EngineSounds] (flutter_soloud, which mixes every sound itself and
/// starts and fades them at exact engine times); tests use [RecordingSounds],
/// which writes down what was asked.
abstract interface class Sounds {
  set music(bool on);
  set effects(bool on);

  /// The parent's loudest (0.3 to 1).
  set volume(double v);

  /// A short sound by its file name in assets/sounds/ (`xylo_0`, `tap`, `call_bear`…).
  void play(String sfx, {double volume = 1});

  /// [owner] (a screen) wants [music]; the one asked for last plays.
  void hold(Object owner, Music? music);
  void release(Object owner);

  /// The band starts at [tempo]: every loop of [available] starts at the same
  /// moment, the [singing] ones heard straight away.
  void bandStart(Tempo tempo, List<Animal> available, Set<Animal> singing);

  /// From the next bar line on, only [singing] are heard.
  void bandSing(Set<Animal> singing);
  void bandStop();

  /// Time since the band started (for moving on the beat), or null.
  Duration? get bandTime;

  /// A song: [notes] (sound, when after now), all scheduled at once.
  void playSong(List<(String, Duration)> notes);
  void stopSong();
}

/// Who wants which music: the one asked for last plays.
class MusicHolders {
  final _holders = <Object, Music?>{};

  void hold(Object owner, Music? music) {
    _holders.remove(owner);
    _holders[owner] = music;
  }

  void release(Object owner) => _holders.remove(owner);

  Music? get current => _holders.isEmpty ? null : _holders.values.last;
}

class SilentSounds implements Sounds {
  const SilentSounds();

  @override
  set music(bool on) {}
  @override
  set effects(bool on) {}
  @override
  set volume(double v) {}
  @override
  void play(String sfx, {double volume = 1}) {}
  @override
  void hold(Object owner, Music? music) {}
  @override
  void release(Object owner) {}
  @override
  void bandStart(Tempo tempo, List<Animal> available, Set<Animal> singing) {}
  @override
  void bandSing(Set<Animal> singing) {}
  @override
  void bandStop() {}
  @override
  Duration? get bandTime => null;
  @override
  void playSong(List<(String, Duration)> notes) {}
  @override
  void stopSong() {}
}

/// Remembers what was asked (tests, and the demo video's sound track).
class RecordingSounds implements Sounds {
  RecordingSounds({this.onChange});

  /// Called with a line for each thing asked (the demo writes them down with the frame).
  final void Function(String line)? onChange;

  final played = <String>[];
  final _holders = MusicHolders();
  Tempo? bandTempo;
  Set<Animal> singing = {};
  List<Animal> bandAvailable = [];
  List<(String, Duration)> song = [];
  Music? _playing;

  Music? get musicNow => _holders.current;
  bool get bandOn => bandTempo != null;

  @override
  set music(bool on) {}
  @override
  set effects(bool on) {}
  @override
  set volume(double v) {}

  @override
  void play(String sfx, {double volume = 1}) {
    played.add(sfx);
    onChange?.call('sfx $sfx');
  }

  @override
  void hold(Object owner, Music? music) {
    _holders.hold(owner, music);
    _changed();
  }

  @override
  void release(Object owner) {
    _holders.release(owner);
    _changed();
  }

  void _changed() {
    if (_holders.current == _playing) return;
    _playing = _holders.current;
    onChange?.call('music ${_playing?.file ?? '-'}');
  }

  @override
  void bandStart(Tempo tempo, List<Animal> available, Set<Animal> singing) {
    bandTempo = tempo;
    bandAvailable = available;
    this.singing = {...singing};
    onChange?.call('band ${tempo.name} ${[for (final a in singing) a.name].join(',')}');
  }

  @override
  void bandSing(Set<Animal> singing) {
    this.singing = {...singing};
    onChange?.call('band ${bandTempo?.name} ${[for (final a in singing) a.name].join(',')}');
  }

  @override
  void bandStop() {
    bandTempo = null;
    singing = {};
    onChange?.call('band -');
  }

  @override
  Duration? get bandTime => null;

  @override
  void playSong(List<(String, Duration)> notes) {
    song = notes;
    for (final (s, at) in notes) {
      onChange?.call('song $s ${at.inMilliseconds}');
    }
  }

  @override
  void stopSong() => song = [];
}

/// The real sounds, through flutter_soloud: one engine mixes everything.
/// - Short sounds play at once (the engine's low-latency output).
/// - The band: every animal's loop at the tempo is scheduled at one engine
///   time T0, looping, silent unless singing; joining and leaving are volume
///   fades scheduled on the engine clock at the next bar line. The loops are
///   all exactly as long, so they can never drift apart.
/// - A song is scheduled note by note against the engine clock in one go.
/// - Quiet while the app is in the background (the band keeps time silently).
class EngineSounds implements Sounds {
  EngineSounds() {
    _life = AppLifecycleListener(onHide: () => _setAway(true), onShow: () => _setAway(false));
  }

  static const bandVolume = 0.7, musicVolume = 0.45;

  /// A fade starts this much before the bar line, so the first note is whole.
  static const fade = Duration(milliseconds: 12);

  late final AppLifecycleListener _life;
  final _sources = <String, Future<AudioSource?>>{};
  final _holders = MusicHolders();
  Future<bool>? _ready;
  var _music = true, _effects = true, _away = false;
  double _volume = 0.7;

  Music? _playing;
  SoundHandle? _musicHandle;
  int _musicTurn = 0;

  final _band = <Animal, SoundHandle>{};
  Set<Animal> _singing = {};
  Duration? _t0;
  MusicClock? _clock;
  int _bandTurn = 0;

  final _song = <SoundHandle>[];

  SoLoud get _s => SoLoud.instance;

  Future<bool> _init() => _ready ??= () async {
        try {
          if (!_s.isInitialized) await _s.init(bufferSize: 1024);
          _s.setMaxActiveVoiceCount(40);
          _s.setGlobalVolume(_away ? 0 : _volume);
          return true;
        } catch (_) {
          return false;
        }
      }();

  Future<AudioSource?> _load(String name) => _sources[name] ??= () async {
        try {
          return await _s.loadAsset('assets/sounds/$name.wav');
        } catch (_) {
          return null;
        }
      }();

  void _setAway(bool away) {
    _away = away;
    if (_s.isInitialized) _s.setGlobalVolume(away ? 0 : _volume);
    _updateMusic();
  }

  @override
  set music(bool on) {
    _music = on;
    _updateMusic();
  }

  @override
  set effects(bool on) => _effects = on;

  @override
  set volume(double v) {
    _volume = v.clamp(0.3, 1.0);
    if (_s.isInitialized && !_away) _s.setGlobalVolume(_volume);
  }

  @override
  void play(String sfx, {double volume = 1}) {
    if (!_effects || _away || sfx.isEmpty) return;
    unawaited(() async {
      if (!await _init()) return;
      final src = await _load(sfx);
      if (src == null) return;
      try {
        _s.play(src, volume: volume);
      } catch (_) {}
    }());
  }

  @override
  void hold(Object owner, Music? music) {
    _holders.hold(owner, music);
    _updateMusic();
  }

  @override
  void release(Object owner) {
    _holders.release(owner);
    _updateMusic();
  }

  void _updateMusic() {
    final wanted = !_music ? null : _holders.current;
    if (wanted == _playing) return;
    _playing = wanted;
    final turn = ++_musicTurn;
    unawaited(() async {
      if (!await _init()) return;
      final old = _musicHandle;
      _musicHandle = null;
      if (old != null) {
        try {
          await _s.stop(old);
        } catch (_) {}
      }
      if (wanted == null || turn != _musicTurn) return;
      final src = await _load(wanted.file);
      if (src == null || turn != _musicTurn) return;
      try {
        _musicHandle = _s.play(src, volume: musicVolume, looping: true);
      } catch (_) {}
    }());
  }

  @override
  void bandStart(Tempo tempo, List<Animal> available, Set<Animal> singing) {
    final turn = ++_bandTurn;
    _singing = {...singing};
    unawaited(() async {
      await _stopBand();
      if (!await _init() || turn != _bandTurn) return;
      final sources = <Animal, AudioSource>{};
      for (final a in available) {
        final src = await _load(a.loop(tempo));
        if (src != null) sources[a] = src;
      }
      if (turn != _bandTurn) return;
      try {
        // Every loop starts at the same engine time, a moment from now.
        final t0 = _s.getEngineTime() + const Duration(milliseconds: 120);
        for (final e in sources.entries) {
          _band[e.key] = _s.playScheduled(e.value, t0, looping: true, volume: _singing.contains(e.key) ? bandVolume : 0);
        }
        _t0 = t0;
        _clock = MusicClock.of(tempo);
      } catch (_) {}
    }());
  }

  @override
  void bandSing(Set<Animal> singing) {
    final changed = {..._singing.difference(singing), ...singing.difference(_singing)};
    _singing = {...singing};
    final t0 = _t0, clock = _clock;
    if (t0 == null || clock == null) return;
    try {
      final now = _s.getEngineTime();
      final at = t0 + clock.nextBar(now - t0, lead: const Duration(milliseconds: 30)) - fade;
      for (final a in changed) {
        final h = _band[a];
        if (h == null) continue;
        _s.fadeScheduled(h, at, singing.contains(a) ? bandVolume : 0, fade);
      }
    } catch (_) {}
  }

  Future<void> _stopBand() async {
    final handles = [..._band.values];
    _band.clear();
    _t0 = null;
    _clock = null;
    for (final h in handles) {
      try {
        await _s.stop(h);
      } catch (_) {}
    }
  }

  @override
  void bandStop() {
    _bandTurn++;
    _singing = {};
    unawaited(_stopBand());
  }

  @override
  Duration? get bandTime {
    final t0 = _t0;
    if (t0 == null) return null;
    try {
      final t = _s.getEngineTime() - t0;
      return t.isNegative ? Duration.zero : t;
    } catch (_) {
      return null;
    }
  }

  @override
  void playSong(List<(String, Duration)> notes) {
    stopSong();
    if (!_effects) return;
    unawaited(() async {
      if (!await _init()) return;
      final loaded = <(AudioSource, Duration)>[];
      for (final (s, at) in notes) {
        final src = await _load(s);
        if (src != null) loaded.add((src, at));
      }
      try {
        final t0 = _s.getEngineTime() + const Duration(milliseconds: 80);
        for (final (src, at) in loaded) {
          _song.add(_s.playScheduled(src, t0 + at));
        }
      } catch (_) {}
    }());
  }

  @override
  void stopSong() {
    final handles = [..._song];
    _song.clear();
    for (final h in handles) {
      unawaited(() async {
        try {
          await _s.stop(h);
        } catch (_) {}
      }());
    }
  }

  void dispose() => _life.dispose();
}
