AntiGravity OS for Windows 10 / 11
==================================

反重力発生器OS風の生成AI (量子プログラミング Bada 言語) の Windows 版です。
インストール不要・自己完結です。

使い方
------
1. この zip を任意のフォルダに展開する
2. AntiGravityOS.bat をダブルクリックする
   -> OS init プロセス (PID 1) がブートし、フライトセッションが表示されます
      G1 揚力保存 / G2 モード隔離 / G3 緊急停止安全 / G4 監査可能テレメトリ
      の 4 不変量が実行時に再導出されます

コマンドラインから個別モジュールを動かすには (cmd.exe):
  bada.exe run agos.bada          OS init プロセス (PID 1)
  bada.exe run sys\agkernel.bada  場カーネル (charge/hover/vent/Telemetry)
  bada.exe run lib\aglift.bada    生成AI揚力制御 (sense/steer)
  bada.exe run lib\agfield.bada   場の命令セット + ゼータ・バラスト
  bada.exe run lib\agsafe.bada    安全インターロック (arm/scram)

注意
----
本ソフトウェアは計算的シミュレーション/思考実験であり、
実際の反重力・推進装置を主張するものではありません。
