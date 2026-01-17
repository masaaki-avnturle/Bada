ilent_talk_bada_passphrases に音声トリガー（日本語発話で「聞き取り開始／停止／合い言葉／挿入／ロック／言語切替」）を組み合わせて動かすための最短手順です。前提：Ubuntu（Xorg）、Python3、pip、sndデバイス（マイク）、xdotool、injector ソースが手元にあること。

1) ビルド確認（injector 側）
- ソースに必要ヘッダがあるか確認（先頭に最低限）:
  #include <fcntl.h>
  #include <unistd.h>
  #include <sys/types.h>
  #include <sys/stat.h>
- コンパイル:
  gcc -O2 silent_talk_bada_passphrases.c -o silent_talk_bada_passphrases -lpthread -lm

2) FIFO 作成と injector 起動
- FIFO を作る:
  mkfifo /tmp/inject_fifo
- injector を FIFO から読み取るように起動（バックグラウンド例）:
  ./silent_talk_bada_passphrases /dev/video0 < /tmp/inject_fifo &

3) Python 音声リスナー準備（Vosk を利用／日本語）
- 必要パッケージ:
  pip install vosk sounddevice
- 日本語モデル（小モデル等を入手）をダウンロードして展開。例パス: ~/models/vosk-model-small-ja-0.22
  ※モデルは Vosk サイト等から取得してください。

4) voice_injector.py（日本語キーワード対応）  
- ファイル作成例（~/voice_injector.py）。必要箇所（MODEL_PATH）を自分のモデルパスに書き換えて保存。

```python
# voice_injector.py -- Japanese phrase mapping for silent_talk_bada_passphrases
import sys, json, queue, subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer

FIFO = "/tmp/inject_fifo"
MODEL_PATH = "/home/youruser/models/vosk-model-small-ja-0.22"   # ← ここを修正
SAMPLE_RATE = 16000

q = queue.Queue()
def callback(indata, frames, time, status):
    q.put(bytes(indata))

def send_cmd(s):
    subprocess.Popen(f"bash -c \"echo '{s}' > {FIFO} &\"", shell=True)

model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)
listening = True  # デフォルト聞き取り ON/ OFF を好みで変更

with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype='int16',
                       channels=1, callback=callback):
    print("voice_injector: listening...")
    while True:
        data = q.get()
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text = res.get("text","").strip()
            if not text: continue
            t = text.lower()
            print("HEARD:", t)
            # 聞き取り制御（日本語）
            if "聞き取り開始" in t or "聞き取りオン" in t:
                listening = True
                print("=> listening ON"); continue
            if "聞き取り停止" in t or "聞き取りオフ" in t:
                listening = False
                print("=> listening OFF"); continue
            # 基本操作
            if "挿入" in t or "インジェクト" in t or "入力" in t:
                send_cmd("inject"); print("=> sent: inject"); continue
            if "ロック" in t or "無効" in t:
                send_cmd("lock"); print("=> sent: lock"); continue
            if "言語 c" in t or "ランク シー" in t or "ランクc" in t:
                send_cmd("lang:c"); print("=> sent: lang:c"); continue
            if "言語 パイソン" in t or "ランク パイソン" in t or "ランクpy" in t:
                send_cmd("lang:py"); print("=> sent: lang:py"); continue
            # 合い言葉候補（日本語発音に対応させる）
            if listening:
                if "オメガ データベース" in t or "オメガデータベース" in t:
                    send_cmd("Omega::DATABASE"); print("=> sent: Omega::DATABASE"); continue
                if "タプルスペース" in t or "タプル スペース" in t:
                    send_cmd("tuplespace"); print("=> sent: tuplespace"); continue
                if "バーチャルマシン" in t or "バーチャル マシン" in t:
                    send_cmd("VIRTUALMACHINE"); print("=> sent: VIRTUALMACHINE"); continue
                if "ウルトラネットワーク" in t or "ウルトラ ネットワーク" in t:
                    send_cmd("ultranetwork"); print("=> sent: ultranetwork"); continue
                # その他はそのまま送信（必要ならマッピング追加）
                # send_cmd(t)
```

5) 実行
- voice_injector を起動:
  python3 ~/voice_injector.py &
- マイクとモデルが正常なら "聞き取り開始" / "タプルスペース" 等を発声すれば /tmp/inject_fifo へ書き込みされ、injector が許可扱いにする。

6) vim/gedit/emacs との連携（補足）
- エディタ側の追加設定は不要（前述の FIFO ショートカットは併用可能）。
- 自動挿入対象にするため、エディタの編集ウィンドウを必ずフォーカスする（xdotool がそのウィンドウへタイプするため）。
- テスト手順:
  1) エディタで新しいファイルを開きフォーカス。
  2) 発声: 「聞き取り開始」
  3) 発声: 「タプルスペース」 → injector が一回分の許可を取得
  4) 発声: 実体的な熱検出トリガー（または手動で「挿入」）→ 文字列が挿入される

7) 注意点（要約）
- Vosk モデルは言語依存。日本語モデルを使い、キーワードは上スクリプトの通りに調整する。  
- 雑音や誤認識が発生しやすいので合い言葉は固有語（長めのフレーズ）にするのが安全。  
- FIFO と injector/microphone の権限を確認。必要なら chmod で権限を調整。  
- Wayland 環境では xdotool が効かない（自動タイプ不可）。Xorg を使ってください。

必要なら:
- あなたの環境（日本語モデルのパス、マイク名）に合わせた具体的な設定ファイルを作りますか？
