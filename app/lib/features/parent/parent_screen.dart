import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../../app/theme.dart';
import '../../app/version.dart';
import '../../core/content.dart';
import '../../core/game.dart';
import '../../core/providers.dart';
import '../record/record_screen.dart' show songNotes;

/// Parent mode (after the gate): the age, the play time, which toys, sounds
/// and the loudest, the child's songs, today, and the full version.
class ParentScreen extends ConsumerWidget {
  const ParentScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final g = ref.watch(gameProvider);
    final s = g.settings;
    final game = ref.read(gameProvider.notifier);
    final now = ref.read(clockProvider)();

    Widget section(String title, List<Widget> children) => Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Material(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(title, style: const TextStyle(fontSize: 15, color: Neon.parentSoft, fontWeight: FontWeight.w700)),
                const SizedBox(height: 8),
                ...children,
              ]),
            ),
          ),
        );

    Widget toggle(String label, bool value, void Function(bool)? set, {Key? key, String? note}) => SwitchListTile(
          key: key,
          contentPadding: EdgeInsets.zero,
          title: Text(label, style: const TextStyle(fontSize: 17)),
          subtitle: note == null ? null : Text(note, style: const TextStyle(fontSize: 13, color: Neon.parentSoft)),
          value: value,
          onChanged: set,
        );

    Widget chips<T>(List<T> values, T selected, String Function(T) label, void Function(T) pick, String keyOf) => Wrap(spacing: 8, runSpacing: 8, children: [
          for (final v in values)
            ChoiceChip(
              key: ValueKey('$keyOf-${v is Enum ? v.name : v}'),
              label: Text(label(v), style: const TextStyle(fontSize: 16)),
              selected: v == selected,
              onSelected: (_) => pick(v),
              selectedColor: const Color(0xFFE2DAFF),
              showCheckmark: false,
            ),
        ]);

    const note = TextStyle(fontSize: 14, height: 1.5, color: Neon.parentSoft);
    final today = g.today != null && g.today!.day == Today.key(now) ? g.today : null;

    return Theme(
      data: NeonTheme.parent(),
      child: Scaffold(
        backgroundColor: Neon.parentBg,
        appBar: AppBar(
          backgroundColor: Neon.parentBg,
          title: const Text(Strings.parentTitle),
          leading: IconButton(icon: const Icon(Icons.close_rounded), tooltip: Strings.back, onPressed: () => context.go('/')),
        ),
        body: ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 32), children: [
          section(Strings.age, [
            chips(Level.values, s.level, (l) => l.zh, (v) => game.settings((x) => x.copyWith(level: v)), 'level'),
            const SizedBox(height: 10),
            const Text(Strings.ageNote, style: note),
          ]),
          section(Strings.playTime, [
            chips(Settings.minuteChoices, s.minutes, Strings.minutes, (v) => game.settings((x) => x.copyWith(minutes: v)), 'minutes'),
            const SizedBox(height: 10),
            const Text(Strings.playTimeNote, style: note),
            if (g.resting(now)) ...[
              const SizedBox(height: 10),
              const Text(Strings.resting, style: TextStyle(fontSize: 16)),
              const SizedBox(height: 6),
              FilledButton(
                key: const ValueKey('play-on'),
                onPressed: () {
                  game.change((g) => g.playOn());
                  ref.read(sessionStartProvider.notifier).restart();
                  context.go('/');
                },
                child: const Text(Strings.playOn),
              ),
            ],
          ]),
          section(Strings.toys, [
            for (final t in Toy.values)
              toggle(t.zh, !s.off.contains(t), (on) => game.settings((x) => x.copyWith(off: on ? ({...x.off}..remove(t)) : {...x.off, t})), key: ValueKey('toy-${t.name}')),
            const SizedBox(height: 4),
            const Text(Strings.toysNote, style: note),
          ]),
          section(Strings.sound, [
            toggle(Strings.music, s.music, (v) => game.settings((x) => x.copyWith(music: v)), key: const ValueKey('music'), note: Strings.musicNote),
            toggle(Strings.effects, s.sounds, (v) => game.settings((x) => x.copyWith(sounds: v)), key: const ValueKey('effects'), note: Strings.effectsNote),
            toggle(Strings.voice, s.voice, (v) => game.settings((x) => x.copyWith(voice: v)), key: const ValueKey('voice')),
            toggle(Strings.english, s.english, (v) => game.settings((x) => x.copyWith(english: v)), key: const ValueKey('english')),
            const SizedBox(height: 6),
            const Text(Strings.maxVolume, style: TextStyle(fontSize: 17)),
            const SizedBox(height: 8),
            chips(Settings.volumeChoices, s.volume, Strings.percent, (v) => game.settings((x) => x.copyWith(volume: v)), 'volume'),
          ]),
          section(Strings.songs, [
            if (g.songs.isEmpty) const Text(Strings.songsNone, style: note),
            for (var i = 0; i < g.songs.length; i++)
              ListTile(
                key: ValueKey('song-$i'),
                contentPadding: EdgeInsets.zero,
                leading: CircleAvatar(backgroundColor: Pentatonic.colours[g.songs[i].colour % 5], child: Text('${i + 1}', style: const TextStyle(color: Neon.parentInk))),
                title: Text(Strings.songLine(g.songs[i])),
                subtitle: Text('${g.songs[i].made.month}/${g.songs[i].made.day} ${g.songs[i].made.hour}:${g.songs[i].made.minute.toString().padLeft(2, '0')}'),
                trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                  IconButton(tooltip: Strings.playSong, icon: const Icon(Icons.play_arrow_rounded), onPressed: () => ref.read(soundsProvider).playSong(songNotes(g.songs[i]))),
                  IconButton(key: ValueKey('delete-$i'), tooltip: Strings.delete, icon: const Icon(Icons.delete_outline_rounded), onPressed: () => game.change((g) => g.forget(i))),
                ]),
              ),
          ]),
          section(Strings.today, [
            Text(Strings.todayLine((today?.seconds ?? 0) ~/ 60, today?.favourite), style: const TextStyle(fontSize: 16)),
          ]),
          section(Strings.together, [
            for (final t in Strings.tips)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Padding(padding: EdgeInsets.only(top: 3), child: Icon(Icons.music_note_rounded, size: 16, color: Color(0xFF7B61FF))),
                  const SizedBox(width: 8),
                  Expanded(child: Text(t, style: const TextStyle(fontSize: 16, height: 1.45))),
                ]),
              ),
          ]),
          section(Strings.fullVersion, [
            const Text(Strings.fullNote, style: note),
            toggle(Strings.fullSwitch, s.full, (v) => game.settings((x) => x.copyWith(full: v)), key: const ValueKey('full')),
          ]),
          section(Strings.about, [
            const Text(Strings.privacy, style: TextStyle(fontSize: 15, height: 1.5)),
            const SizedBox(height: 6),
            Text(Strings.version(appVersion), style: note),
          ]),
        ]),
      ),
    );
  }
}
