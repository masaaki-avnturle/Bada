# Bada Oracle — Desktop (Windows 10 / 11)

Python + Tkinter 実装。PyInstaller で単一の `BadaOracle.exe` に固めます。
生成エンジンは Android 版と同一の考え方（ガンマ関数 + エントロピー + ハッシュ）。

> ⚠️ 娯楽・内省用の生成アートです。アカシックレコードへのアクセスや未来予知では
> ありません。重要な判断の根拠には使わないでください。

## 実行（開発時）
```bash
python bada_oracle.py        # tkinter が必要（Windows の公式 Python に同梱）
```

## EXE ビルド（Windows）
```bat
pip install -r requirements.txt
pyinstaller --onefile --windowed --name BadaOracle bada_oracle.py
:: 出力: dist\BadaOracle.exe
```

チャイム音は Windows の `winsound.Beep` を使用（非 Windows では自動的に無音）。
