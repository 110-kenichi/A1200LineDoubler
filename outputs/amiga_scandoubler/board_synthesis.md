# 基板用トップの合成確認 v0.14

2026-09-12。Yosys 0.69（git 9f75ca1f9、YoWASP 0.69.0.0.post1233）で `amiga_board_top` を合成した。RTLと基板の変更はなく、検証ファイルと結果を追加した。

|1ラインのサンプル数|LUT1～4|ALU|FF|専用RAM|PLL|ODDR|
|---:|---:|---:|---:|---:|---:|---:|
|1816|764|476|672|6|1|1|
|2048|781|453|674|6|1|1|

両条件で最終CHECKは0 problems。入力バッファ29、出力バッファ31、双方向バッファ2を生成し、62本の物理信号と端子対応表が一致した。CSTによる実際の端子配置はまだ実行していない。LUTとALUの共有・配線を含む物理使用率は未評価。

## 合成後の接続検査

`synthesis/audit_board_netlist.py` で、I²Cの出力データが常にLow、Low要求時だけ出力許可、それ以外は開放、読み戻しが制御回路へ接続されることを確認した。合成時のtri-state警告2件はこの確認と併記する。もう1件の警告はI²C送信用3バイトのレジスター展開であり、映像RAMは6個のDPX9Bに割り当てられている。

ODDRの定数入力、Q0から端子バッファへの直接接続、PLLのCLKOUTPからODDRへの接続、32段の起動リセットの配線と初期値も照合した。結果は `board_netlist_audit.txt`。

## 合成後のリセット試験

リセット長2/32/65について個別に合成し、生成されたVerilogネットリストをIcarus Verilogで実行した。初期リセット、参照クロック停止中の保持、指定クロック数での解除がすべて通過した。これは元RTLだけの試験ではなく、合成後のDFF/LUT接続の試験である。

モデルは [Yosysの合成版と同じコミットのセル定義](https://raw.githubusercontent.com/YosysHQ/yosys/9f75ca1f9/techlibs/gowin/cells_sim.v) を使用した。DFFの省略時INIT=0を含むモデル上の確認であり、実デバイスの設定シーケンスやGSRの測定ではない。ライブラリーのSHA-256と結果は `mapped_reset_simulation_report.txt` に記録。

## 再現

展開したフォルダーを作業フォルダーとして、Yosys 0.69で実行する。

```text
yosys -l synthesis/board_1816.log synthesis/board_1816.ys
yosys -l synthesis/board_2048.log synthesis/board_2048.ys
python synthesis/audit_board_netlist.py
yosys -l synthesis/reset_2.log synthesis/reset_2.ys
yosys -l synthesis/reset_32.log synthesis/reset_32.ys
yosys -l synthesis/reset_65.log synthesis/reset_65.ys
python sim/run_mapped_reset_tests.py --bin-dir <Icarusのbinフォルダー> --gowin-library <対応するcells_sim.v> --report mapped_reset_simulation_report.txt
```

1816/2048は以前と同じ合成比較用プロファイル。実機検証済みPAL/NTSC設定ではない。`.ys`、`.log`、`.json`、リセットの生成Verilog、セル集計とRTLハッシュを同梱した。

## 位相と未完了事項

[Gowin UG289-2.2.1E、図4-17](https://cdn.gowinsemi.com.cn/UG289E.pdf) の定常波形ではD0が立ち上がり側、D1が立ち下がり側へ出る。D0=0/D1=1の候補は、定常状態では映像クロックに対し反転したDACクロックになる。図には内部パイプラインによる開始遅延もある。前版の簡易ODDRモデルを、この開始遅延や実デバイスの位相検証として扱わない。

合成ライブラリーのPLL/ODDRはブラックボックスであり、今回の合成成功は専用回路の配置や波形を保証しない。PLL・IO logicの実配置、CSTの受理、設定兼用端子のGPIO解放、入力・出力タイミング、基板バッファの遅延、実機GSRが引き続き未確認。長短ラインの連続処理と実入力設定も残る。95×95mmの基板は未配線で、製造Gerber・完成BOM/CPL・ビットストリームは未完成。

## v0.15追記

選定FPGAへの配置配線を試行し、両条件で完了した。`implementation_review.md` を参照。位相関係と外部入出力を含むタイミングの最終確認は未完了。
