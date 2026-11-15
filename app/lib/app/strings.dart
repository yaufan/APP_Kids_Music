import '../core/content.dart';
import '../core/game.dart';

/// Everything the app says, in Traditional Chinese (Taiwan). The child does
/// not need to read: everything important is also said out loud.
abstract final class Strings {
  static const appName = '小小音波';

  // The stage.
  static const welcome = '歡迎來到小小音波！點一個玩具開始玩。';
  static const parent = '家長';
  static String timeLeft(int minutes) => '還可以玩 $minutes 分鐘';
  static const locked = '這個要請爸爸媽媽打開喔！';
  static const backToStage = '回舞台';
  static const mySongs = '我的小曲子';
  static String songN(int n) => '小曲子 $n';
  static const balloon = '氣球';
  static const encore = '安可！安可！';

  // 敲敲樂.
  static const tapHint = '敲敲看！手指滑過去是一串「刷～」';
  static String key(Instrument i, int k) => '${i.zh} ${i.keys[k]}';

  // 動物樂團.
  static const bandHint = '把動物拖上舞台，牠就開始唱！';
  static const bandHintBig = '把動物拖上舞台；按住牠是「噓」，先不唱。';
  static String joins(Animal a) => '${a.zh}來唱歌了！';
  static String shushed(Animal a) => '噓～${a.zh}先不唱';
  static String sings(Animal a) => '${a.zh}又唱了！';
  static const tempo = '慢・中・快';
  static String tempoIs(Tempo t) => switch (t) { Tempo.slow => '慢～慢～', Tempo.normal => '中', Tempo.fast => '快！快！' };
  static String spot(int i) => '舞台位子 ${i + 1}';
  static String tray(Animal a) => '拖${a.zh}上台';
  static String onStage(Animal a) => '台上的${a.zh}';
  static const full = '樂團滿了！好好聽！';
  static const lockedAnimal = '這隻動物要完整版才有喔！';

  // 音樂木頭人.
  static const freezeHint = '音樂放的時候點一點，動物會跳舞；音樂停了，手也不要動！';
  static const stop = '停！不要動～';
  static const stopSoon = '要停囉……';
  static const go = '開始！跳舞！';
  static const still = '好棒，都沒動！';
  static const shh = '噓～';
  static const stopLight = '停';

  // 高低快慢.
  static const highlowHint = '把小鳥拖上樓梯，越高叫聲越高！';
  static const high = '高～';
  static const low = '低～';
  static const fast = '快！';
  static const slow = '慢～～';
  static const loud = '大聲～';
  static const soft = '小聲（悄悄話）';
  static String stepN(int i) => '樓梯第 ${i + 1} 階';
  static const speed = '快慢';
  static const volume = '大小聲';
  static const elephant = '小象：大聲';
  static const mouse = '小老鼠：小聲';
  static const snail = '蝸牛：慢';
  static const rabbit = '兔子：快';
  static const bird = '小鳥';

  // 錄下來.
  static const recordHint = '按紅色的錄音，敲幾個音，就是你的小曲子！';
  static const rec = '錄音';
  static const play = '放出來';
  static const recording = '錄音中……敲敲看！';
  static const playing = '動物在演你的小曲子！';
  static const saved = '存起來了！';
  static String cell(int i) => '磁帶第 ${i + 1} 格';

  // 聽聽看.
  static const listenAsk = '這是什麼聲音？';
  static const again = '再聽一次';
  static String right(StreetSound s) => '對！是${s.zh}！';
  static String thisIs(StreetSound s) => '這是${s.zh}喔。';
  static String goFind(StreetSound s) => switch (s) {
        StreetSound.ricecooker => '去廚房看看家裡的電鍋！',
        StreetSound.stirfry => '下次炒菜的時候聽聽看！',
        StreetSound.garbage => '下次垃圾車來的時候，和爸爸媽媽一起聽！',
        _ => '',
      };

  // Rest.
  static const restTitle = '換你去做了！';
  static const restLine = '去敲敲家裡的鍋子，\n或唱一首歌給媽媽聽。';
  static const goodnight = '晚安！';

  // Parent gate (as in the sibling apps).
  static const callParent = '請爸爸媽媽來幫忙喔！';
  static const parentGateTitle = '家長確認';
  static String gateQuestion(String a, String b) => '$a 加 $b 等於多少？';
  static const gateRules = '答錯三次要等一分鐘。';
  static const wrongAnswer = '不對喔，換一題。';
  static String gateWait(int s) => '請等 $s 秒再試';
  static const backspace = '刪掉';
  static const cancel = '取消';

  // Parent mode.
  static const parentTitle = '家長模式';
  static const back = '回去';
  static const age = '年齡（難度）';
  static const ageNote = '小小：5 個琴鍵、樂團 4 個位子、停很久而且會提醒、兩張圖選一張、錄 4 格。\n大：8 個琴鍵、6 個位子和「噓」、停得又快又隨機、四張圖選一張、錄 8 格（照拍子）。';
  static const playTime = '每次玩多久';
  static String minutes(int m) => '$m 分鐘';
  static const playTimeNote = '時間到了，霓虹燈一盞一盞暗下來，布幕合起來，提醒孩子去做真的事。要等一個小時，或家長在這裡按「再玩一下」才能再玩。';
  static const resting = '現在是休息時間。';
  static const playOn = '再玩一下';
  static const toys = '要開哪些玩具';
  static const toysNote = '關掉的玩具不會出現在舞台上（例如晚上關掉鼓）。';
  static const sound = '聲音';
  static const music = '背景音樂（舞台和休息時的音樂）';
  static const musicNote = '動物樂團和音樂木頭人的音樂是玩具本身，一直都會響。';
  static const effects = '按鈕音效（按鈕、氣球、拍手這些提示聲）';
  static const effectsNote = '樂器、動物、聽聽看和小曲子的聲音是玩具本身，一直都會響；要全部小聲，請調下面的音量上限。';
  static const voice = '國語念出來';
  static const english = '也念英文（動物和聲音的名字）';
  static const maxVolume = '音量上限（保護小耳朵）';
  static String percent(double v) => '${(v * 100).round()}%';
  static const songs = '我的小曲子';
  static const songsNone = '還沒有。在「錄下來」錄完會自動存起來，最多 8 首。';
  static String songLine(Song s) => '${s.instrument.zh}，${s.count} 個音';
  static const delete = '刪掉';
  static const playSong = '放';
  static const today = '今天';
  static String todayLine(int minutes, Toy? fav) => '玩了 $minutes 分鐘${fav == null ? '' : '，最常玩：${fav.zh}'}';
  static const together = '一起玩';
  static const tips = [
    '玩完「敲敲樂」，拿鍋子、碗和湯匙在家裡真的敲敲看。',
    '「音樂木頭人」可以在客廳真的玩：放音樂跳舞，音樂一停就不動。',
    '和孩子一起唱「動物樂團」裡的那一段，拍手打拍子。',
    '聽到垃圾車、機車、下雨的聲音時，問問孩子：「這是什麼聲音？」',
  ];
  static const fullVersion = '完整版';
  static const fullNote = '免費版：敲敲樂三種樂器、動物樂團 6 隻動物、音樂木頭人、高低快慢。完整版：10 隻動物、錄下來、聽聽看。測試版先全部打開；以後一次買斷，購買只在這裡。';
  static const fullSwitch = '完整版（測試中）';
  static const about = '關於';
  static const privacy = '不連網、不定位、沒有廣告、沒有帳號、不用麥克風；小曲子和紀錄只存在這支手機裡，不會傳給任何人。';
  static String version(String v) => '版本 $v';
}
