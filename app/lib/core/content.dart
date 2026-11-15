import 'dart:math' as math;
import 'dart:ui' show Color;

/// What is in the app: the toys, the instruments, the animals, the tempos,
/// the sounds of 聽聽看 and the five notes (docs/design.md; the sound files
/// are design/sounds/README.md's, the pictures docs/art.md's).

/// The age the parent set: 小小 (2 to 3) or 大 (4 to 5).
enum Level {
  small('小小（2～3 歲）'),
  big('大（4～5 歲）');

  const Level(this.zh);

  final String zh;
}

/// The six toys on the stage.
enum Toy {
  tap('敲敲樂'),
  band('動物樂團'),
  freeze('音樂木頭人'),
  highlow('高低快慢'),
  record('錄下來'),
  listen('聽聽看');

  const Toy(this.zh);

  final String zh;

  /// In the free version (the rest come with the full version).
  bool get free => this != record && this != listen;

  String get art => 'assets/art/toys/${name == 'tap' ? 'xylo' : name}.svg';
}

/// C major pentatonic: the only notes in the app (docs/design.md 「怎麼敲都好聽」).
abstract final class Pentatonic {
  /// The xylophone's eight keys, low to high, in semitones above C5.
  static const semitones = [0, 2, 4, 7, 9, 12, 14, 16];
  static const names = ['Do', 'Re', 'Mi', 'Sol', 'La', 'Do', 'Re', 'Mi'];

  /// The note's colour (Do red, Re orange, Mi yellow, Sol green, La blue), the
  /// same everywhere in the app.
  static const colours = [Color(0xFFFF7A8A), Color(0xFFFFA65E), Color(0xFFFFE066), Color(0xFF7EEB8F), Color(0xFF6EC8FF)];

  static Color colour(int key) => colours[key % 5];

  /// Hz of key [key] (C5 is 523.25 Hz).
  static double hz(int key) => 523.2511 * math.pow(2, semitones[key] / 12).toDouble();

  /// Whether two keys are a half step apart (never, in this scale).
  static bool clash(int a, int b) => ((semitones[a] - semitones[b]).abs() % 12) == 1 || ((semitones[a] - semitones[b]).abs() % 12) == 11;
}

/// The three instruments of 敲敲樂.
enum Instrument {
  xylo('木琴', ['Do', 'Re', 'Mi', 'Sol', 'La', '高音 Do', '高音 Re', '高音 Mi']),
  drum('鼓', ['大鼓', '低低的鼓', '高高的鼓', '小鼓', '鈴鼓']),
  pot('鍋碗瓢盆', ['鍋子', '鍋蓋', '碗', '杯子', '湯匙']);

  const Instrument(this.zh, this.keys);

  final String zh;

  /// The name of each key (said in the parent's notes, and for the drums and pots out loud).
  final List<String> keys;

  /// How many keys a child of [level] gets: the xylophone has 5 for 小小 and 8 for 大; drums and pots have 5.
  int count(Level level) => this == xylo && level == Level.big ? 8 : 5;

  String sound(int key) => '${name}_$key';

  String art(int key, {bool lit = false}) => 'assets/art/keys/${name}_${key}_${lit ? 'lit' : 'idle'}.svg';
}

/// The band's three speeds; every animal's two bars are drawn out at each one
/// (the same number of samples for every animal at one tempo).
enum Tempo {
  slow(80, '慢～'),
  normal(100, '中'),
  fast(120, '快！');

  const Tempo(this.bpm, this.zh);

  final int bpm;
  final String zh;

  Tempo get faster => Tempo.values[math.min(index + 1, 2)];
  Tempo get slower => Tempo.values[math.max(index - 1, 0)];

  /// The snail/rabbit button goes round: normal, fast, slow, normal…
  Tempo get next => switch (this) { normal => fast, fast => slow, slow => normal };
}

/// What an animal is doing on the stage.
enum Pose { idle, sing, frozen, cheer }

/// The ten band animals (the first six are in the free version).
enum Animal {
  bear('小熊', 'bear', Color(0xFFFFA66B)),
  frog('青蛙', 'frog', Color(0xFF8EF09A)),
  bird('小鳥', 'bird', Color(0xFF63DCF5)),
  cat('小貓', 'cat', Color(0xFFFF8FC8)),
  dog('小狗', 'dog', Color(0xFFC7A6FF)),
  elephant('小象', 'elephant', Color(0xFF8FB8FF)),
  blackbear('台灣黑熊', 'black bear', Color(0xFFDAD4FF)),
  leopard('石虎', 'leopard cat', Color(0xFFFFC86B)),
  magpie('藍鵲', 'blue magpie', Color(0xFF5E8CFF)),
  duck('小鴨', 'duck', Color(0xFFFFE16E));

  const Animal(this.zh, this.en, this.colour);

  final String zh;
  final String en;
  final Color colour;

  bool get free => index < 6;

  String art(Pose pose) => 'assets/art/animals/${name}_${pose.name}.svg';
  String loop(Tempo t) => 'band_${name}_${t.name}';
  String get call => 'call_$name';

  /// The animals a child may play with.
  static List<Animal> available({required bool full}) => [for (final a in values) if (full || a.free) a];
}

/// The sounds of Taiwanese daily life in 聽聽看 (no thunder, no ambulance).
enum StreetSound {
  garbage('垃圾車', 'garbage truck', Family.street),
  scooter('機車', 'scooter', Family.street),
  mrt('捷運', 'MRT', Family.street),
  bike('腳踏車', 'bicycle', Family.street),
  crossing('平交道', 'railway crossing', Family.street),
  rain('下雨', 'rain', Family.nature),
  temple('廟裡的鼓', 'temple drum', Family.temple),
  ricecooker('電鍋', 'rice cooker', Family.kitchen),
  stirfry('炒菜', 'stir-fry', Family.kitchen),
  cat('小貓', 'cat', Family.animal),
  dog('小狗', 'dog', Family.animal),
  frog('青蛙', 'frog', Family.animal);

  const StreetSound(this.zh, this.en, this.family);

  final String zh;
  final String en;

  /// Sounds of one family are alike; 小小 only ever chooses between families.
  final Family family;

  String get sound => 'ls_$name';

  String get art => switch (this) {
        cat => Animal.cat.art(Pose.idle),
        dog => Animal.dog.art(Pose.idle),
        frog => Animal.frog.art(Pose.idle),
        _ => 'assets/art/listen/$name.svg',
      };
}

enum Family { street, nature, temple, kitchen, animal }

/// Music that plays under a screen (design/sounds/README.md).
enum Music {
  stage('music_stage'),
  freeze('music_freeze'),
  rest('music_rest');

  const Music(this.file);

  final String file;
}

/// Where the pictures are (docs/art.md).
abstract final class ArtPath {
  static String stage(String name) => 'assets/art/stage/$name.svg';
  static String ui(String name) => 'assets/art/ui/$name.svg';
  static String step(int i, {bool lit = false}) => 'assets/art/keys/step_${i}_${lit ? 'lit' : 'idle'}.svg';
  static String tape(int colour) => 'assets/art/ui/tape_${colour % 8}.svg';
  static String balloon(int i) => 'assets/art/ui/balloon_${i % 3}.svg';
  static String note(int i) => 'assets/art/ui/note_${i % 5}.svg';
}
