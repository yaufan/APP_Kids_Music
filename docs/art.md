# 圖和程式的約定（小小音樂家）

所有的圖都是 `design/art/` 的 Python 畫的 SVG（霓虹舞台風），放在 `app/assets/art/`，APP 用 flutter_svg 畫。這份是「程式要哪些檔、每個檔多大」的約定；改了這裡，`test/art_test.dart` 也要跟著改。

## 規則（flutter_svg 畫得出來的才用）
- 只用 `<path>`、`<circle>` 這些基本形狀，加 `fill`、`stroke`、`fill-opacity`、`stroke-opacity`、`opacity`、線性和放射漸層。
- **不用** `<filter>`（模糊）、`<mask>`、`<clipPath>`、`<style>`、`<text>`、`<image>`、`<pattern>`、混合模式。
- 霓虹的光暈不能用模糊做，一律是「同一條線，畫兩條更粗、半透明的在下面」（`kit.Ctx.line`）：粗 4.2 倍 8%、粗 2.3 倍 20%，然後燈管本身，最裡面一條細白線（燈管最亮的芯）。
- 每個檔小於 70 KB，`viewBox` 從 `0 0` 開始。`python3 design/art/build.py check` 檢查這些，`fluttercheck` 用真的 flutter_svg 和 Chromium 各畫一次比對。
- 燈管在手機上一律約 3 點粗：每個檔有自己的 `unit`（幾個 viewBox 單位是畫面上 1 點），所以大小不同的圖看起來一樣粗。
- 顏色（`kit.py`）：底色深藍紫 `#1B1A3A`→`#2A2550`；燈管粉彩霓虹（粉紅、珊瑚、橘、黃、金、綠、薄荷、青、天藍、藍、淡紫）；五個音的顏色整個 APP 一樣：Do `#FF7A8A`、Re `#FFA65E`、Mi `#FFE066`、Sol `#7EEB8F`、La `#6EC8FF`。
- 臉：眼睛白色發光（有小小的黑眼珠）、臉頰粉紅發光、嘴巴粉紅燈管。表情：`idle`（張眼微笑）、`sing`（開心瞇眼、嘴巴「喔」）、`frozen`（眼睛睜大、嘴巴一條線）、`cheer`（瞇眼、大笑）、`sleep`。

## 檔案
| 資料夾 | 檔名 | viewBox | 是什麼 |
|---|---|---|---|
| `stage/` | `bg.svg` | 400×860 | 夜晚舞台的底（畫滿整個畫面，`BoxFit.cover`） |
| | `curtain_left.svg`、`curtain_right.svg` | 110×700 | 兩邊綁起來的霓虹布幕 |
| | `valance.svg` | 400×90 | 上面一排垂下來的布幔 |
| | `floor.svg` | 400×150 | 發光的舞台地板 |
| | `spot.svg` | 200×560 | 聚光燈的光（半透明） |
| | `audience.svg` | 400×70 | 台下一排發光的小眼睛 |
| `animals/` | `<動物>_<姿勢>.svg` | 200×200 | 十隻動物 × 四個姿勢（`idle`、`sing`、`frozen`、`cheer`），腳在 y=188 |
| `keys/` | `xylo_<0..7>_<idle\|lit>.svg` | 80×400 | 木琴 C5 D5 E5 G5 A5 C6 D6 E6，越高的音越短，站在底邊 |
| | `drum_<0..4>_<狀態>.svg` | 160×160 | 大鼓、低中鼓、高中鼓、小鼓、鈴鼓 |
| | `pot_<0..4>_<狀態>.svg` | 160×160 | 鍋子、鍋蓋、碗、杯子、湯匙 |
| | `step_<0..4>_<狀態>.svg` | 80×400 | 高低的樓梯（一階比一階高） |
| `toys/` | `xylo`、`band`、`freeze`、`highlow`、`record`、`listen` | 120×120 | 舞台上六個玩具按鈕裡的圖 |
| `ui/` | `home lock sun moon snail rabbit play stop rec replay mute plus star mouse slot` | 100×100 | 按鈕和小圖 |
| | `hand.svg` | 200×200 | 音樂木頭人的紅色「停！」燈和手掌 |
| | `balloon_<0..2>.svg` | 100×140 | 飄過去的氣球（粉紅、青、黃） |
| | `note_<0..4>.svg` | 60×60 | 五個音顏色的音符 |
| | `tape_<0..7>.svg` | 120×80 | 我的小曲子（八種顏色的小磁帶） |
| `listen/` | `garbage scooter mrt rain temple bike crossing ricecooker stirfry` | 160×160 | 聽聽看的圖卡；貓、狗、青蛙用 `animals/<動物>_idle.svg` |

動物的 id：`bear`（小熊）、`frog`（青蛙）、`bird`（小鳥）、`cat`（小貓）、`dog`（小狗）、`elephant`（小象）、`blackbear`（台灣黑熊）、`leopard`（石虎）、`magpie`（藍鵲）、`duck`（小鴨）。前六隻是免費版。

## APP 圖示
`design/art/icon.py`：一個有笑臉的黃色霓虹音符加三道音波（粉紅、青、綠），深藍紫底。`python3 design/art/icon.py preview 圖.png` 先看，`export` 寫進 Android（含 adaptive icon）和 iOS。
