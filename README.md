# 小小音樂家

給 **2～5 歲**的小朋友，在台灣，國語為主：**音樂玩具，不是遊戲**。隨便敲、隨便拖都好聽（全部在同一個調、同一個速度）；沒有關卡、分數、失敗。

- 設計：[docs/design.md](docs/design.md)，草圖在 `docs/mockups/`。
- 和「畫畫小鎮」「字母寵物」「動物小餐廳」「小卡認天下」「想一想樂園」「眼尖尖大挑戰」「迷宮小冒險」「小小生活家」是兄弟 APP：同一個作者、同一套技術、不同畫風。
- 不連網、不定位、沒有廣告、沒有帳號。

## 六個玩具
敲敲樂（木琴、鼓、鍋碗瓢盆）、動物樂團（10 隻發光動物一起唱，含台灣黑熊、石虎、藍鵲）、音樂木頭人、高低快慢、錄下來（錄敲了哪個鍵，不用麥克風）、聽聽看（台灣生活的聲音）。兩個難度：小小（2～3 歲）、大（4～5 歲）。

## 下載（Android）
- 最新版：[Releases](https://github.com/yaufan/APP_Kids_Music/releases/latest)，一般手機下載 `little-musician-版本-arm64.apk`。
- 用手機掃描 [docs/download-qr.png](docs/download-qr.png)。

## 目前進度
- 0.1.0 測試版：六個玩具全部做好，見 [CHANGELOG.md](CHANGELOG.md)。還沒在真手機上試過，聲音也還沒用耳朵聽過。

## 程式
- `app/`：Flutter APP（`little_musician`）。聲音用 flutter_soloud（在 APP 裡自己混音，動物樂團才會準確對拍）。
- `design/art/`：Python 畫的霓虹舞台風 SVG（`docs/art.md` 是約定）；`design/sounds/`：numpy 合成全部聲音。
- `tools/demo_audio.py`：把聲音混進示範影片。

## 授權
- 非商業使用授權：自己、家人使用，或學校、非營利團體的教學，都可以免費使用、修改、分享，要註明出處。
- 商業用途（販賣、收費、廣告、上架）要先取得作者書面同意。也不可以拿來訓練 AI。
- 細節見 [LICENSE](LICENSE)；別人做的部分（字型）見 [NOTICE.md](NOTICE.md)。
