# 180度設定への更新 v0.17

2026-09-12。製品側の検討RTL `gowin_video_pll.sv` のPSDA_SELを0100から1000へ変更した。映像クロックの位相を自身の周期の90度から180度へ変更し、ADC負エッジ取得から次段への理想時間を広げる。2倍周波数、静的50%デューティー、VCO分周比など他のPLL設定は変更していない。[設定値の根拠：Gowin UG286、Table 5-7](https://cdn.gowinsemi.com.cn/UG286E.pdf)

## 実装と機能試験

1816/2048条件で基板トップを再合成・再配置配線し、最終CHECKは0 problems、配置配線も完了。合成後と配置後のPSDA_SEL=1000を検査し、他のPLLパラメーターが以前と同じことを照合した。62信号、RAM6個、DACクロックODDRの16番端子側配置も維持している。

|サンプル数|配置後LUT4|FF|映像領域内Fmax MHz|
|---:|---:|---:|---:|
|1816|1130|672|85.06|
|2048|1109|674|79.09|

今回の合成はOSS CAD Suite 2026-09-12内のネイティブYosys 0.69+24（d0e71cfb7-dirty）を使用した。以前のYoWASP Yosys 0.69とは版が異なる。配置配線は以前と同じnextpnr-0.11.1-26-ga601751d。したがって配置結果の差をすべて位相変更だけの効果とは解釈しない。ログ・版・RTLハッシュを `implementation/phase180/summary.json` に記録した。

取り込み単体は180度の理想クロックで24条件、5,472画素の照合を通過。全体試験のクロック位相も180度に変更し、ADCの36件の設定送信、取得・同期、12,258回の可視RGB照合、ADCクロック停止後の別色での復帰、電源断、再起動時のNACKを確認した。試験終了時刻とクロック位相の関係で、可視照合回数は旧試験の12,259回から1回変わった。

## 配置後の暫定予算

両条件とも26本のADC負エッジ→映像正エッジ経路をSDFから再抽出した。最大の必要エッジ間隔は推定3.837ns。28.375MHz・ADC High 52%で、180度の理想間隔は8.106nsとなり、差は約4.269ns。現行設定では、前版の90度で見つかった理想時間不足の懸念を、暫定計算上は避けられる。

ただし26経路の挿入LUTのSDF遅延欠落は残る。同一SDFの他のLUT4 I3→Fの625psを参考値として補っており、最終setup slackではない。PLL実位相・ジッター、未モデル化の経路、不確かさ、最小遅延とholdの検証は未完了。位相設定がネットリストに残ることと、実デバイスが期待どおりの波形を出すことを区別する。

DACクロックは映像クロックに対して反転するODDR構成を維持した。その外部setup/holdやU6バッファ遅延、入力RGB/HSの取得条件、実入力のVS整列位置も引き続き確認が必要。

## 使用する成果物

今回の180度の合成・配置結果は **`implementation/phase180/`** にまとめた。`commands.txt` で再現し、`verify_phase180.py` で設定・資源・単一領域タイミングを照合、`python implementation/analyze_capture_sdf.py --phase 180` で暫定予算を再計算できる。

```text
python sim/run_capture_tests.py --bin-dir <Icarusのbinフォルダー> --report capture_phase180_current_report.txt
python sim/run_system_tests.py --bin-dir <Icarusのbinフォルダー> --report system_phase180_report.txt
```

単体試験の既定位相も180度へ更新。90度の比較は `--phase 90` を明示する。旧 `synthesis/board_*` と `implementation/board_*`、旧報告書は履歴として残しており、現在の180度RTLに対する実装結果ではない。最新の再現にはphase180内の手順を使う。

基板や部品は変更していない。95×95mmのプリント基板は未配線。実PLLと外部入出力を含むタイミング確認、PAL/NTSC入力プロファイル、長短ライン連続処理、製造用Gerber・完成BOM/CPL・実機ビットストリームは未完成。
