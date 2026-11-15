# design/art：小小音樂家的圖（霓虹舞台風）

每樣東西都是一圈**霓虹燈管**：裡面淡淡的顏色（玻璃），外面兩條更粗、半透明的同色線（光暈），燈管本身，和最裡面一條細白線（燈芯）。沒有模糊、遮罩、CSS、文字、圖片，只有 `<path>` 加 `fill`／`stroke`／透明度，所以 flutter_svg 畫出來和 Chromium 一樣。和 APP 的約定在 `docs/art.md`，先看那份。

## 畫一個東西
```python
import kit
c = kit.Ctx(200, 200, unit=1.55)                  # viewBox 0 0 200 200，畫面上約 130 點寬
c.fill(kit.circle(100, 90, 50), "#24204A")       # 不透明的深色底：擋住後面的線
c.tube(kit.circle(100, 90, 50), kit.PINK)        # 玻璃 + 光暈 + 燈管 + 燈芯
c.line(kit.arc(100, 95, 20, 30, 150), kit.PINK)  # 一條開口的霓虹線
c.glowdot(60, 40, 4, kit.YELLOW)                 # 發光的小點
c.note(150, 50, 14, kit.YELLOW)                  # 小音符
c.face(100, 90, 24, "idle")                      # idle / sing / frozen / cheer / sleep
kit.write_svg(path, c.svg())                     # 先檢查規則再寫
```
形狀：`rrect ellipse circle poly smooth blob star heart path arc`，用 `+` 合起來，`.move .scale .flip .rotate .map` 變形（從小小生活家的 kit 拿來的）。亂數只用 `kit.rnd(key)`。

## 模組
`stage.py`（舞台）、`animals.py`（十隻動物 × 四個姿勢）、`keys.py`（木琴、鼓、鍋碗瓢盆、樓梯，`idle`／`lit` 兩種）、`ui.py`（玩具按鈕、小圖、停的手、氣球、音符、磁帶）、`listen.py`（聽聽看的圖卡），每個都有 `build()`，列在 `build.py` 的 `MODULES`。`icon.py` 是 APP 圖示。

## 指令（在這個資料夾）
```
python3 build.py all                       # 全部畫一次，再檢查
python3 build.py animals                   # 只畫一個模組
python3 build.py check                     # 只檢查規則
python3 build.py sheet animals 看.png       # 一個資料夾（或 all）的全部圖排在舞台底色上（Chromium）
python3 build.py fluttercheck all          # 用真的 flutter_svg 和 Chromium 各畫一次比對（約 20 秒）
python3 icon.py preview 圖示.png            # 圖示：大圖、各種形狀、和兄弟 APP 放在一起
python3 icon.py export                     # 寫進 Android 和 iOS
```
每次改完用 Read 看 `sheet` 的圖，看清楚：臉看得到、顏色柔、形狀大又圓、是給 2 歲看的舞台不是夜店。
