# Silent Talk — サイレントトーク（無音ハンズフリー操作）

Voice Access の「無音版」として、**声を出さずに**端末を操作するための Android
支援アプリです。視線・表情・近接(赤外線)・温度センサーから読み取った信号を
**言語コマンドに翻訳**し、アクセシビリティ機能で実際にタップ・スクロール・
戻る/ホーム等を実行します（発話困難な方の支援を想定）。

> **重要・正直な前提**
> 温度計や赤外線センサーで「思考そのもの」を読むことは物理的にできません。
> 本アプリは**観測可能な信号**（視線＝頭の向き、まばたき、表情、近接、温度）を
> コマンドに翻訳します。依頼にある「ガンマ関数の大域的部分積分多様体／大脳基底核の
> 熱ネットワーク」は、複数センサーを融合する**理論モデル**（`ThermalManifold`）として
> 確信度と確定時間(ドウェル)の調整に用いています。

---

## 仕組み

| 入力（無音シグナル） | 取得方法 | 役割 |
|:--|:--|:--|
| 視線追跡（頭の向き） | 前面カメラ + ML Kit 顔検出（オンデバイス） | カーソル移動 |
| まばたき / 笑顔 | 同上（目の開閉・笑顔確率） | 決定 / クイック選択 |
| 近接（**赤外線**）センサー | `TYPE_PROXIMITY` | 覆うと「決定」 |
| 温度（**温度計**） | `TYPE_AMBIENT_TEMPERATURE` | 熱ネットワーク（確信度） |
| 端末の傾き | `TYPE_ACCELEROMETER` | カメラ無し時のカーソル操作 |

1. `FaceGazeAnalyzer` … カメラ映像 → 視線方向・まばたき・表情
2. `SensorHub` … 近接(IR)・温度・傾き
3. `ThermalManifold` … Γ関数カーネルで信号を融合 → 確信度／確定時間
4. `CommandTranslator` … シグナル → 言語コマンド（「タップ」「戻る」等）
5. `SilentTalkAccessibilityService` … コマンドを実機操作に変換（Voice Access と同方式）
6. `OverlayService` … Voice Access と同じ**円形ボタン**＋カーソル＋ドック＋HUD

すべてオンデバイス処理。カメラ映像は端末外へ送信しません。

---

## 使い方

1. アプリ「**Silent Talk**」を起動。
2. セットアップで **① アクセシビリティ有効化 / ② オーバーレイ許可 / ③ カメラ許可**。
3. 円形ボタン（Voice Access と同デザイン）をタップで起動。画面に丸ボタン＋カーソルが出ます。
4. **視線（頭の向き）または傾き**でカーソル移動 →
   **見つめて静止 / まばたき / 近接センサーを覆う** で決定。
5. 右端のドックを決定すると **戻る・ホーム・履歴・通知・上/下スクロール**、
   それ以外の位置を決定するとその座標を**タップ**します。
6. 丸ボタン再タップで停止、長押しは不要（タップでトグル）。

---

## APK の入手（ビルド済み）

GitHub Actions（`.github/workflows/silenttalk.yml`）が push ごとに APK をビルドします。

1. **Actions** タブ →「Build SilentTalk APK」最新の成功実行 → **Artifacts** の
   `SilentTalk-debug-apk` をダウンロード（zip）→ 展開して `app-debug.apk`。
2. Android 12 端末に「提供元不明アプリ」を許可してインストール。

### 自分でビルド

```bash
cd silenttalk_android
./gradlew assembleDebug   # app/build/outputs/apk/debug/app-debug.apk
```
JDK 17 と Android SDK（platform 34 / build-tools 34）が必要。Wrapper 同梱。

---

## 構成

```
silenttalk_android/app/src/main/java/com/bada/silenttalk/
  MainActivity.java                   セットアップ＋起動（Voice Access風ボタン）
  OverlayService.java                 円形ボタン/カーソル/ドック/HUD＋エンジン
  SilentTalkAccessibilityService.java 実機操作（タップ/スワイプ/戻る…）
  FaceGazeAnalyzer.java               ML Kit 視線・表情検出
  SensorHub.java                      近接(IR)・温度・傾き
  ThermalManifold.java                Γ関数による信号融合（理論モデル）
  CommandTranslator.java              シグナル→言語コマンド
```

## 制限・今後

- 顔検出は ML Kit（オンデバイス）。暗所や正面でない場合は傾き操作にフォールバック。
- 視線は「頭の向き」を用いた実用的な近似です（厳密な眼球視線推定ではありません）。
- 温度センサーは多くの端末で非搭載 → その場合は中立値として動作します。
