# 給 Claude 的專案規則（小小音波）

這份是這個專案的「記憶」。每個在這個專案裡工作的 Claude 都要照著做。它是「畫畫小鎮」（https://github.com/yaufan/APP_Kids_Paint）、「字母寵物」（https://github.com/yaufan/APP_Kids_Paint_for_learning_writing）、「動物小餐廳」（https://github.com/yaufan/APP_Kids_Cook）、「小卡認天下」（https://github.com/yaufan/APP_Kids_Card_Game）、「想一想樂園」（https://github.com/yaufan/APP_Kids_Brainstorming）、「眼尖尖大挑戰」（https://github.com/yaufan/APP_Kids_FalseCharge）、「迷宮小冒險」（https://github.com/yaufan/APP_Kids_maze）和「小小生活家」（https://github.com/yaufan/APP_Kids_live_circ）的兄弟 APP，技術和流程照那邊（畫風不同），這裡寫這個專案自己的事。程式的架構最接近小小生活家（Python 畫 SVG、ParentPass、休息時間），聲音的部分最重要，有疑問先看那邊怎麼做。

## 和使用者合作
- **一律用繁體中文回覆**，用白話說明，少用技術名詞；要用的話順便解釋。
- 使用者用手機上的 Claude App 看對話，**打不開 artifact 連結**。圖片、影片、聲音、QR code 都用傳檔案的方式（SendUserFile）給。
- 設計階段：每個想法都畫成草圖（`docs/mockups/`）傳給使用者看，再問。
- 之後每做完一版：給示範影片片段、手機截圖、下載 QR code（和畫畫小鎮一樣）。
- 有要使用者決定的事，列出選項和我的建議，再問。
- 不要開 pull request，除非使用者要求。用了網路搜尋，回覆最後附「Sources:」和連結。

## 這個 APP
- 給 **2～5 歲**的小朋友，在台灣，國語為主：**音樂玩具，不是遊戲**。隨便敲、隨便拖都好聽（全部在同一個調、同一個速度）；沒有關卡、分數、失敗。
- 六個玩具（0.1 全做）：敲敲樂（木琴、鼓、鍋碗瓢盆）、動物樂團（拖 10 隻發光動物上舞台一起唱，含台灣黑熊、石虎、藍鵲）、音樂木頭人（音樂停就不能動，練自我控制）、高低快慢、錄下來（錄「敲了哪個鍵」，不用麥克風）、聽聽看（台灣生活的聲音，不放打雷和救護車）。
- 兩個難度：小小（2～3 歲）、大（4～5 歲）。
- 設計在 [docs/design.md](docs/design.md)，改設計時一起改它；草圖在 `docs/mockups/`。
- 畫風：**霓虹舞台風**，只做一種（深藍紫底、粉彩霓虹燈管加柔光、大圓形、臉看得到；給 2 歲看的舞台，不是夜店）。要和兄弟 APP 的畫風**不一樣**。
- 每次玩多久由家長設定（預設 15 分鐘），時間到了霓虹燈一盞一盞暗下來，APP 說「換你去做了！」。
- 聲音引擎用 **flutter_soloud**（不是兄弟 APP 的 audioplayers）：動物樂團每個速度的十段循環一樣長，在引擎時鐘的同一刻一起開始（沒上台的音量 0），上台、下台、「噓」是排在下一小節開頭的音量淡入淡出，所以永遠對拍、不靠手機的計時器（`docs/design.md`「技術」）。真手機上還要確認：點下去的延遲、十隻一起會不會太大聲、切到背景再回來、便宜手機卡不卡。
- 免費版：敲敲樂三種樂器＋樂團 6 隻＋音樂木頭人＋高低快慢；完整版：10 隻、錄下來、聽聽看。購買只在家長模式。
- 技術名稱：Flutter 專案 `little_wave`、applicationId `com.yaufan.littlewave`、APK `little-wave-版本-arm64.apk`、簽章環境變數 `LITTLE_WAVE_KEYSTORE`。
- 資安：不接受別的 APP 傳來的頁面（`flutter_deeplinking_enabled` 關掉、`overridePlatformDefaultLocation`），家長模式只能從家長關卡進去（`ParentPass`），不要任何權限。
- 不連網、不定位、沒有廣告、沒有帳號。以後上架要收費：免費下載一部分，一次買斷完整版，購買只在家長模式（要過家長關卡）。
- 每個動作都要有音效，全部用程式合成。
- 授權：非商業使用（`LICENSE`），中英文版本；別人做的部分（字型）在 `NOTICE.md`。
- 名稱：小小音波。GitHub：https://github.com/yaufan/APP_Kids_Music

## GitHub Actions
- 工作流程（照小小生活家；第一次放上 main 前要先問）：
  - `app.yml`（App）：推到 `main` 而且改到 `app/**` 時跑分析、全部測試（含完整流程）、打包 APK，約 15～20 分鐘。
  - `release.yml`（Release）：推到 `main` 而且改到 `app/pubspec.yaml`、`CHANGELOG.md` 或它自己時，版本還沒發布過就打包三個 APK 放上 Releases，約 20 分鐘；版本沒變約 1 分鐘。
  - `cleanup.yml`：手動，刪舊的建置檔案，約 1 分鐘。
- 推工作分支（`claude/...`）不會啟動任何工作流程。
- 簽章：和畫畫小鎮用**同一把測試金鑰**（別名 `kidspaint`），Secrets 名稱一樣：`ANDROID_KEYSTORE_BASE64`、`ANDROID_KEYSTORE_PASSWORD`，要放在這個專案的 Actions → Secrets → Repository secrets。指紋 `TEST_KEY_SHA256` 寫在工作流程裡。以後上架要換成正式的上傳金鑰。
- 發新版本：`app/pubspec.yaml` 的 `version`、`app/lib/app/version.dart` 的預設值、`CHANGELOG.md` 最上面一段（`## 版本 …`）三個要一致（`test/version_test.dart` 檢查）。
- **任何會啟動 Actions 的動作，都要先問使用者，等使用者同意才做**，問的時候說清楚四件事：
  1. 會跑哪些工作流程。
  2. 這次大約用掉幾分鐘。
  3. 這個月目前用了多少。
  4. 跑完大約還剩多少。

  規則和畫畫小鎮的 `CLAUDE.md` 一樣；那個帳號每月 2,000 分鐘是所有私有專案共用的，Mac 主機的 1 分鐘算 10 分鐘。

## Git
- **發布新版本、做成可以安裝的 APK、給下載 QR code**：照 skill `release-kids-app`（`.claude/skills/release-kids-app/SKILL.md`），兄弟 APP 共用同一份。
- 在系統指定的 `claude/...` 工作分支上開發，commit 完就推這個分支。
- commit 訊息用英文寫清楚改了什麼和為什麼，結尾加系統要求的署名行。不要寫模型名稱。
- 不能 commit：金鑰、密碼、不公開的文件、`__pycache__`。

## 和畫畫小鎮共用的做法（開始寫程式時照著做）
- Flutter 3.47.8、Riverpod、flutter_svg、flutter_soloud（不是 audioplayers，見上面）、flutter_tts。`flutter test` 第一次會在這台機器上編譯 soloud 的 C++（約 1 分鐘，要 clang）；pubspec 的 `hooks: user_defines: flutter_soloud: no_xiph_libs: true` 要留著（全部是 WAV，不用 Ogg/Opus）。存檔是一個 JSON 檔（`app/lib/core/store.dart`），沒有用 drift，所以本機跑測試**不用** sqlite 那段，直接 `flutter test`。
- 觸控：用原始的手指事件（`Listener`），手指一碰就畫。不要用拖曳手勢，它要移動 36 點才開始，小朋友短短的一筆會不見。
- 圖和聲音都用程式產生（SVG 用 Python 畫；聲音用 numpy 合成），不用別人的素材。
- 本機測試：在 `app/` 裡 `flutter test`（不含 `test/flow_test.dart`），`flutter analyze` 要零問題。以後加了 drift，才照畫畫小鎮的 `tools/run_tests.sh`（pubspec 的 sqlite 那段不能 commit）。
- 完整流程和截圖：`flutter test test/flow_test.dart`，截圖在 `app/build/screenshots/`。
- 示範影片（每一版都要給使用者）：在 `app/` 裡 `flutter test test/demo/demo_video_test.dart --dart-define=DEMO=true`（約 5～10 分鐘，要 ffmpeg），再在專案根目錄 `python3 tools/demo_audio.py` 把背景音樂和音效混進去。輸出 `app/build/demo/demo.mp4`；`chapters.txt` 是每一段開始的格數（每秒 10 格），用來剪新功能的片段。

## 程式在哪裡
- `app/lib/core/`：內容的名字（`content.dart`：玩具、樂器和琴鍵、十隻動物、三個速度、聽聽看的 12 種聲音、五個音和顏色）、規則（`music.dart`：樂團的時鐘 `MusicClock`、錄音的磁帶 `Tape`、木頭人什麼時候停 `FreezePlan`、聽聽看出題 `ListenRound`）、存檔的東西（`game.dart`：設定、最多 8 首小曲子、今天玩了多久、休息）、聲音引擎（`sounds.dart`：`EngineSounds` 用 soloud，`RecordingSounds` 給測試和示範影片）、`providers.dart`（含台上有哪些動物 `bandProvider`）、`store.dart`、`voice.dart`。
- `app/lib/features/`：舞台首頁（`stage/`）、敲敲樂（`tap/`，琴鍵 `keys_view.dart` 三個地方共用）、動物樂團（`band/`）、音樂木頭人（`freeze/`）、高低快慢（`highlow/`）、錄下來（`record/`）、聽聽看（`listen/`）、休息（`rest/`）、家長關卡和家長模式（`parent/`）。
- `app/lib/app/`：路由和休息時間（`app.dart`）、顏色（`theme.dart`）、所有的字（`strings.dart`）、共用的小元件（`widgets.dart`：`NeonButton`、`StageBackdrop`、`ToyPage`……）。
- 圖：`design/art/`（`kit.py` 霓虹燈管畫法、`stage.py`、`animals.py`、`keys.py`、`ui.py`、`listen.py`、`icon.py`；`build.py all` 產生和檢查，`sheet` 看圖，`fluttercheck` 用真的 flutter_svg 比對）；約定在 `docs/art.md`。聲音：`design/sounds/make_sounds.py`（`README.md` 有每個檔）。
- 測試：`test/rules_test.dart`（規則、樂團每個檔一樣長）、`art_test.dart`、`safety_test.dart`、`version_test.dart`、`flow_test.dart`（手機和平板、兩個難度、每個玩具，截圖 44 張）、`test/demo/demo_video_test.dart`。

## 目前的狀態（2026-11-15）
- 0.1.0 做好、測試都過了，在本機 `claude/relaxed-albattani-6mbwpz` 分支 commit；GitHub 專案使用者還沒建，建好後再推（推 main 前要先問）。
- 還沒在真手機上試過、沒用耳朵聽過聲音（垃圾車的〈少女的祈禱〉是憑記憶寫的，要聽聽看像不像）。soloud 的 Android 打包只能在 GitHub Actions 試。示範影片和截圖在 `app/build/`。
