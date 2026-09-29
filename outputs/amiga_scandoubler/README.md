# Amiga 1200 15kHz → 31kHz スキャンダブラー

2026-09-29 / 全配線完了・製造データ一次版 v0.30 / **製造用リリースではありません（発注前の確認が残っている）**

## v0.30（最新）

- 変更点・検査結果・残作業：`revision_0.30.md`（作業ログは `revision_0.30wip.md`）
- 基板：`hardware/amiga_scandoubler_v030wip.kicad_pcb`（KiCad 7 形式。DRC エラー0・未接続0）
- 製造データ：`fab/v030wip/`（README に一覧と発注前の注意）
- 配線レビューとシミュレーション：`review_v030wip_wiring.md`
- ERC：`hardware/erc_k9.rpt`、除外 `hardware/erc_exclusions.json`

## v0.27 の内容（以下は当時の記述）

- **最新：出力側H/V同期配線**：`sync_out_review.md`
- 現行基板：`hardware/amiga_scandoubler_sync_out.kicad_pcb`
- 独立検査：`hardware/sync_out_report.json`、`hardware/sync_out_drc.txt`
- 配線図：`sync_out_review.png`、`sync_out_detail.png`

- v0.26：DACのRGB出力接続：`rgb_out_review.md`
- v0.26基板：`hardware/amiga_scandoubler_rgb_out.kicad_pcb`
- 検査：`hardware/rgb_out_report.json`、`hardware/rgb_out_drc.txt`
- 配線図：`rgb_out_review.png`、`rgb_out_detail.png`

- v0.25：PLLフィルター表面配線：`pll_top_review.md`
- v0.25基板：`hardware/amiga_scandoubler_pll_top.kicad_pcb`
- 独立検査：`hardware/pll_top_report.json`、`hardware/pll_top_drc.txt`
- 配線図：`pll_top_review.png`、`pll_top_detail.png`

- v0.24：R34付近の電源配線見直し：`r34_review.md`
- v0.24基板：`hardware/amiga_scandoubler_refined.kicad_pcb`
- 検査：`hardware/refined_report.json`、`hardware/refined_drc.txt`
- 配線図：`refined_review.png`

- v0.23：アナログ信号の部分配線：`analog_review.md`
- v0.23基板：`hardware/amiga_scandoubler_analog.kicad_pcb`
- 独立検査：`hardware/analog_report.json`、`hardware/analog_drc.txt`
- 配線図：`analog_review.png`、`analog_detail.png`

- v0.22：主要ICへの電源分配：`distribution_review.md`
- v0.22基板：`hardware/amiga_scandoubler_distribution.kicad_pcb`
- 接続・間隔の検査：`hardware/distribution_report.json`、`hardware/distribution_drc.txt`
- 主要IC周辺の配線図：`distribution_detail.png`

- v0.21 電源部の部分配線：`power_routing_review.md`
- v0.21の部分配線基板：`hardware/amiga_scandoubler_routing.kicad_pcb`
- 電源部の拡大図：`power_routing_detail.png`
- 接続・DRC検査：`hardware/power_routing_report.json`、`hardware/power_routing_drc.txt`

- FPGA現行：出力リセット解除の同期化：`output_release_review.md`
- 現行実装・経路解析・再現手順：`implementation/output_release/`

- v0.19 DAC出力段同期化：`output_stage_review.md`
- v0.19の再合成・配置配線と解析：`implementation/output_stage/`

- 出力段追加前のDACタイミング調査：`dac_timing_review.md`
- 端子別の暫定条件と解析手順：`implementation/dac_timing_budget.json`、`implementation/analyze_dac_sdf.py`

- PLLを180度へ更新：`phase180_integration.md`
- 180度の再合成・配置配線・遅延解析：`implementation/phase180/`
- 更新後の試験：`system_phase180_report.txt`、`capture_phase180_current_report.txt`

- 旧90度設定の調査履歴：`capture_timing_review.md`
- 配置後52経路の暫定解析：`implementation/capture_timing_estimate.json`
- 90度／180度の機能試験：`capture_phase90_report.txt`、`capture_phase180_report.txt`

- FPGA配置配線の試行結果と検証限界：`implementation_review.md`
- 配置配線後の回路・ログ・周期制約・再現手順：`implementation/`

- 基板トップの合成・合成後リセット検証：`board_synthesis.md`
- 合成後接続の照合：`board_netlist_audit.txt`、`synthesis/board_summary.json`
- 合成後リセット試験：`mapped_reset_simulation_report.txt`

- 基板接続と端子修正：`board_integration.md`、`rtl/amiga_board_top.sv`
- 62信号の端子制約候補：`constraints/amiga_board_top.cst`、`constraints/board_port_map.json`
- 起動リセット候補と試験：`rtl/configuration_reset.sv`、`board_simulation_report.txt`

- 統合回路の合成結果：`system_synthesis.md`、`synthesis/system_summary.json`
- 1816/2048条件の合成手順・ログ・ネットリスト：`synthesis/system_*`

- 機能回路の全体接続：`system_integration.md`、`rtl/amiga_logic_core.sv`
- ADC起動から映像出力までの機能試験：`system_simulation_report.txt`

- PLL再起動と監視接続：`pll_restart.md`、`rtl/pll_restart_control.sv`、`rtl/clock_recovery_system.sv`
- 起動・復帰の試験記録：`pll_restart_simulation_report.txt`

- PLL設定・ADC入力レジスターの構成候補：`pll_capture.md`、`rtl/gowin_video_pll.sv`、`rtl/adc_rgb_capture.sv`
- 理想クロックによる取り込み試験：`capture_simulation_report.txt`

- 入力同期前段と映像処理への接続：`stream_input.md`、`rtl/stream_sync_frontend.sv`、`rtl/stream_input_video.sv`
- 前段・統合試験の記録：`stream_simulation_report.txt`

- ADCの36件の設定候補と起動統合：`adc_configuration.md`、`rtl/tvp7002_boot.sv`
- ADC起動統合の試験結果：`adc_boot_simulation_report.txt`

- クロック停止監視・DAC省電力制御の接続条件：`clock_integration.md`
- 監視回路と統合映像処理：`rtl/video_clock_guard.sv`、`rtl/supervised_video_core.sv`
- 新規試験結果：`clock_simulation_report.txt`

- RGB・HS・VSを整列した統合映像処理：`rtl/video_core.sv`
- 統合試験の結果：`video_simulation_report.txt`
- 専用RAMへの合成確認：`synthesis_review.md`、`synthesis/`

- 合意済み仕様と回路構成案：`design.md`
- 編集可能なKiCad 7回路図（6機能シート）：`hardware/amiga_scandoubler.kicad_sch`
- 閲覧用の回路図（7ページ）：`schematic_review.pdf`
- 135部品・129接続の定義：`hardware/circuit_manifest.json`
- FPGAの仮端子割り当て：`hardware/fpga_pin_assignment.json`
- KiCad出力ネットリスト：`hardware/amiga_scandoubler.net`
- 接続照合の結果：`hardware/connectivity_report.txt`
- この版の変更点と残作業：`revision_0.27.md`
- 95×95mm・全135部品の配置基板：`hardware/amiga_scandoubler_placement.kicad_pcb`（未配線）
- 配置図：`placement_review.png`、`placement_review.svg`
- パッド接続・部品外形の照合：`hardware/placement_report.json`
- FPGA・ADCの専用フットプリント：`hardware/Amiga.pretty/`
- フットプリントの確認記録：`hardware/footprint_review.md`
- ADC起動制御・I²C通信：`rtl/adc_power_sequence.sv`、`rtl/i2c_register_write.sv`
- 制御系の接続条件：`control_interface.md`、試験結果：`control_simulation_report.txt`
- メーカー資料に基づく入力回路・端子接続案：`input_circuit.md`
- 主要部品の選定・調達確認状況：`parts_review.md`
- ライン倍化のSystemVerilog処理核：`rtl/line_double.sv`
- フィールド単位の出力同期処理核：`rtl/field_sync.sv`
- 自動照合付きシミュレーション：`sim/`、実行結果：`simulation_report.txt`
- 実機での確認項目と製造データの完成条件：`verification.md`

現在のコードは、ADC起動から映像出力までの機能回路を接続した**検証版**です。基板トップと実PLL・DDR出力の接続候補を追加しましたが、実入力設定、DACタイミング、端子の実配置まで検証した製品用FPGAデータではありません。

回路図と4層基板は検討版です。現行基板には電源部の部分配線と内層GND面がありますが、未接続160件とシルクの問題が残り、基板全体のDRCは合格していません。ガーバー、完成BOM、CPL、書き込み用ビットストリームは未作成です。フットプリントには寸法・実装条件の確認が残るものがあります。この版をJLCPCBに提出しないでください。

KiCadで開くときは`hardware`フォルダーをまとめて展開し、`amiga_scandoubler.kicad_sch`を開いてください。子シートとローカルシンボルも同梱しています。接続検査はKiCadが実際に出力したデータを照合しました。ERC、基板DRC、基板全体の合成・配置配線、実機試験の合格を意味するものではありません。

## 合意済み条件

Amiga 1200、所有済みのUNBUFFERED VGA変換アダプター、BENQ GW2780を使用。基板の入出力はいずれも3列15ピンDE-15メス。USB給電。15kHzのPAL/NTSCプログレッシブおよびインターレースを2倍の水平周波数に変換。インターレースはBob方式、各フィールドを1出力フレームにする。低遅延を優先し、外付けフレームメモリ・動き適応・フレームレート変換は搭載しない。

基板は100×100mm以内を目標とし、配線品質や実装性を優先する。今回の配置案は95×95mm。これは基板外形であり、コネクターや接続ケーブルを含む外形ではない。

## 検証の再実行

Python 3とIcarus Verilogを用意して、次を実行します。

```text
python sim/run_tests.py --bin-dir <Icarusのbinフォルダー> --report simulation_report.txt
python sim/run_control_tests.py --bin-dir <Icarusのbinフォルダー> --report control_simulation_report.txt
python sim/run_video_tests.py --bin-dir <Icarusのbinフォルダー> --report video_simulation_report.txt
python sim/run_clock_tests.py --bin-dir <Icarusのbinフォルダー> --report clock_simulation_report.txt
python sim/run_adc_boot_tests.py --bin-dir <Icarusのbinフォルダー> --report adc_boot_simulation_report.txt
python sim/run_stream_tests.py --bin-dir <Icarusのbinフォルダー> --report stream_simulation_report.txt
python sim/run_capture_tests.py --bin-dir <Icarusのbinフォルダー> --report capture_simulation_report.txt
python sim/run_pll_restart_tests.py --bin-dir <Icarusのbinフォルダー> --report pll_restart_simulation_report.txt
python sim/run_system_tests.py --bin-dir <Icarusのbinフォルダー> --report system_simulation_report.txt
python sim/run_board_tests.py --bin-dir <Icarusのbinフォルダー> --report board_simulation_report.txt
```

シミュレーションは処理核のデジタル動作を確認します。Amiga実機、アナログ画質、モニター互換性、FPGAへの実装可能性や実測遅延の確認ではありません。
