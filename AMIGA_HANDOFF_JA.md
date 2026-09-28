# Amiga 1200 スキャンダブラー：他の生成AIへの引き継ぎ

作成日：2026-09-27。会話を知らない担当者向け。**製造可能な完成品ではない。最新の検証済み部分配線版はv0.27。** ここでいう検証済みとは、記載した導通・幾何学的DRC・シミュレーションの確認範囲を指し、電気性能や実機動作の合格ではない。

## 1. 引き継ぎ先への依頼文

> 添付ファイルを読み、Amiga 1200の15kHz RGBを低遅延で約31kHzへ変換する基板とFPGAの設計を継続してください。最初にこの引き継ぎ文書とプロジェクトREADME、最新検査報告を確認してください。v0.27が検証済みの基準です。入力同期の作業途中データを完成版として扱わないでください。既に承認された設計方針を維持し、通常の可逆的な設計・検査は都度の継続確認なしで進めてください。クレジット使用は少なく、品質を優先し、変更に関係のある検査に絞ってください。最終目標は製造可能なKiCad設計、Gerber/ドリル、JLCPCB向けBOM/CPL、動作するFPGAビットストリームです。未解決の課題を隠さず、根拠を添えて進めてください。発注・購入・公開・外部への送信は依頼していません。

## 2. ユーザーが確定した要件

- 入力：Amiga 1200の約15kHzアナログRGB。PAL/NTSC、プログレッシブとインターレースの両方。
- 出力：約31kHz RGB。入力・出力ともPC用DE-15（通称D-SUB15）メス。
- 電源：USB。現行設計はUSB-Cコネクタを使用。
- 低遅延優先。外部フレームメモリや動き適応型処理など、要求に不要な機能を増やさない。
- インターレースは各フィールドを独立したフレームにするBob方式。通常のPALなら25フレーム/50フィールドから50出力フレームという意図であり、フィールド周波数をさらに倍にする要求ではない。
- Amiga本体との接続ケーブルは所有済み。ケーブルの製作は不要。その変換アダプターはH/V同期バッファを内蔵しない「UNBUFFERED VERSION」。
- LCDはBENQ GW2780。PAL対応はユーザー申告。今回設計した信号条件での実機表示は未確認。
- 基板は可能なら100×100mm以内。現行は95×95mm・4層。
- JLCPCBの表面実装発注を想定。GerberだけでなくBOM/CPLも最終的に必要。
- ユーザーは繰り返し継続を承認している。最新の追加要望は「クレジット使用量を最低に、成果は最高に」。説明と成果物を簡潔にし、無関係な再合成や同じ検査の反復を避ける。ただし検査を省略して完成扱いしない。

## 3. 引き継ぎZIPの構成

ZIPを任意の作業フォルダーに展開する。以下のパスは展開先からの相対パス。

| パス | 内容と扱い |
|---|---|
| `AMIGA_HANDOFF_JA.md` | この説明書 |
| `NEXT_AI_PROMPT_JA.txt` | 引き継ぎ先へ最初に渡す短い依頼文 |
| `outputs/amiga_scandoubler/` | **v0.27の既存ZIPから取り出した、検証済み部分配線版一式** |
| `outputs/amiga_scandoubler/release_manifest.json` | v0.27内のファイルSHA-256。過去版のファイルも含む |
| `work/handoff_pending/` | 未検証の入力同期候補基板・生成記録・処理ログ。基準版とは分離 |
| `work/route_sync_in.py` | 入力同期候補をv0.27から再生成する作業スクリプト |
| `work/audit_sync_in.py` | 入力同期候補を検査する作業スクリプト。現候補では未接続のため合格しない見込み |
| `work/build_output_release.py`、`work/mapped_output_release.py` | 現行FPGA実装のローカル再構築補助。ツールのパスは移行先で修正が必要 |
| `HANDOFF_MANIFEST.json` | 引き継ぎZIPに同梱した各ファイルのSHA-256と元リリースZIPのSHA-256 |

KiCad、Icarus、Yosys、nextpnr等の実行ファイル、巨大なツールキャッシュ、過去の全作業ログは同梱していない。現行成果物のレビュー・RTL・シミュレーションソース・制約・合成/配置配線結果と必要な作業スクリプトは含めた。

## 4. 最初に読むファイル

以下は `outputs/amiga_scandoubler/` 内。

1. `README.md` と `design.md`：全体設計・成果物索引。
2. `sync_out_review.md`：v0.27で完了した出力同期。
3. `hardware/sync_out_report.json` と `hardware/sync_out_drc.txt`：現在の基準となる接続・DRC結果。
4. `hardware/circuit_manifest.json`：部品・ピン・ネット定義。推測でピン番号を変更しない。
5. `hardware/amiga_scandoubler.kicad_sch`：階層回路図の入口。ルート＋6子シート。`schematic_review.pdf`は閲覧用。
6. `hardware/amiga_scandoubler_sync_out.kicad_pcb` と同名 `.kicad_pro`：**編集を引き継ぐ基準基板**。
7. `output_release_review.md`、`phase180_integration.md`、`implementation/output_release/`：現行FPGAと検証限界。
8. `parts_review.md`、`hardware/footprint_review.md`、`input_circuit.md`、`adc_configuration.md`、`verification.md`：部品・入力条件・設定・残る確認。

フォルダーには多数の過去基板が残る。`placement`、`routing`、`distribution`、`analog`、`refined`、`pll_top`、`rgb_out`は履歴であり、最新は`sync_out`。FPGA側の最新は`implementation/output_release/`で、`output_stage/`や`phase180/`は前段階の履歴。

## 5. ハードウェア構成

入力RGBの終端・結合回路 → TVP7002 ADC → GW1N-4 FPGAのラインバッファ/Bob処理 → ADV7125 DAC → RGB出力。入力同期には5V入力を受ける3.3Vバッファを使用する設計。正確な電圧・ピン接続・動作条件は回路定義とデータシートで照合する。

| 主要部品 | 現行選定 |
|---|---|
| ADC U1 | TI TVP7002PZP、LCSC C3824085。1.9V系と3.3V系を使用 |
| FPGA U2 | Gowin GW1N-LV4QN88C6/I5、C31900351。1.2Vコア・3.3V I/O |
| DAC U3 | ADV7125KSTZ140、C9668、3.3V |
| 同期バッファ U4/U5 | SN74LVC2G17DBVR |
| DACクロックバッファ U6 | SN74LVC1G17DBVR |
| 電源 U7/U8/U9 | TPS62160DSGR、3.3V/1.9V/1.2V |
| 入出力コネクタ | CONEC 33DSMT1-E15SNCT、自作フットプリント |
| USB-C | HRO TYPE-C-31-M-12、C165948 |
| 基準発振器 | ECS-3225MVLC-270-CN-TR、27MHz ±25ppm。調達番号等は要最終確認 |
| インダクター | VLS4012CX-2R2M-1、C7413169、2.2µH |

重要な照合事項：ADCのPLLフィルターはPLL_FへのRC接続であり、安易にGNDへ置換しない。DACのRSETは536Ω、COMP/VREFは各専用コンデンサへ接続。補完RGB出力はGNDに接続する現行回路。部品の調達可否・製造ステータス・MLCCの実効容量・コネクタの実装条件は最終承認されていない。

FPGAの62信号制約は `constraints/amiga_board_top.cst` と `constraints/board_port_map.json`。過去にIOLOGIC制約に対応するため、DAC_CLK_RAWを物理16番、ADC_PWDNを57番へ変更している。古いピン表に戻さない。

## 6. v0.27で確認した範囲

- 95×95mm、4層、135部品、129ネット、592パッドのネット定義を維持。
- 電源部、ADC/FPGA/DACへの電源配線の一部とGND面接続を実装。
- DACのRGB3色は、DAC・終端抵抗・出力コネクタ間の導通を確認。
- 出力同期のH_OUT_RAW、V_OUT_RAW、H_OUT_BUF、V_OUT_BUF、H_OUT、V_OUTの6ネットは全端子の導通を確認。
- U5/C52/R41/R42の電源4端子、U5/C52のGND2端子を確認。
- C52は(84.4,59.0)mm、180度。U5電源端子からの配線長6.405mm。配置・導通は確認したがデカップリング性能の合格ではない。
- PLL_FILT1、PLL_FILT2、PLL_RC、PLL_Fは全て表面配線、信号ビア0個。総銅箔長はそれぞれ2.956、4.158、4.751、13.956mm。PLL_Fは枝分かれ合計。
- PLL周辺のC25/C26は配置と電源経路を変更している。以前の端子→コンデンサ最長5.384mmを現行に適用しない。現報告には履歴値であることと再評価フラグを明示。
- R34近くの1.9V迂回配線はv0.24で85.170→38.427mmへ短縮済み。履歴の迂回経路を復活させない。
- 配線区間2,062本、貫通ビア152個。**未接続160件**。これはラッツネスト件数で、未完了ネット数や完成率ではない。
- 短絡、銅箔間隔、穴間隔、コートヤード、未接続配線端/ビア等は0件。
- 残るDRC：未接続160、文字高さ135、シルクと銅箔70、シルク同士25、基板端シルク2。**基板全体のDRCは未合格。**

In1.CuはGND面、In2.Cuは主に電源分配。プレビューの赤=F.Cu、青=B.Cu、橙=In2.Cu。GND面は見やすさのため図から省略している。色は電圧の種類ではない。裏面信号の直近内層には電源配線があり、信号帰路・インピーダンスの評価は未完了。

既存ビアは主に径0.60/穴0.30mm、最近の追加分には径0.55/穴0.30mm（名目環状幅0.125mm）がある。設計ルール上の合格をJLCPCBでの最終製造承認と混同しない。

## 7. 中断時の入力同期作業（未採用・未検査）

v0.27を入力に `work/route_sync_in.py` を実行し、候補基板を生成した直後に引き継ぎ依頼が来た。**この候補に対する独立監査はまだ実行していない。** v0.28はリリースしていない。

候補はパッケージの `work/handoff_pending/` に分離した。元作業環境では `outputs/amiga_scandoubler/hardware/amiga_scandoubler_sync_in.kicad_pcb` と `sync_in_progress.json` が存在するが、v0.27のマニフェストには含まれない。

生成ログ上の状態：

| 入力同期ネット | 生成処理の結果。導通検査結果ではない |
|---|---|
| H_IN | 接続候補生成 |
| V_IN | 未接続1端子を残す |
| H_IN_BUF | 接続候補生成 |
| V_IN_BUF | 接続候補生成 |
| H_IN_3V3 | 未接続1端子を残す |
| V_IN_3V3 | 未接続1端子を残す |

計5組の信号接続候補。U4/C51の電源・GND、R19/R21の3.3Vプルアップも生成を試みているが独立検査前。U4→C51の生成経路長は2.470mm。

端子位置（mm）は次のとおり。

- U4中心(17,59)。1=H_IN_BUF(15.8625,58.05)、2=GND(15.8625,59)、3=V_IN_BUF(15.8625,59.95)、4=V_IN_3V3(18.1375,59.95)、5=3V3(18.1375,59)、6=H_IN_3V3(18.1375,58.05)。
- C51中心(20.5,58)、90度。1=3V3(20.5,58.775)、2=GND(20.5,57.225)。
- J1.13 H_IN=(5.65,42)、J1.14 V_IN=(5.65,44.28)。
- R18.1 H_IN=(11.175,53.5)、R18.2 H_IN_BUF=(12.825,53.5)。
- R20.1 V_IN=(11.5,57.325)、R20.2 V_IN_BUF=(11.5,55.675)。
- U1.81 H_IN_3V3=(29.5,34.35)、U1.78 V_IN_3V3=(31,34.35)。

最初の再開作業：候補の残る3ネットの障害物を調べ、必要なら局所的に引き出し・配置を修正する。生成ログだけで完成としない。全6ネット、既存接続、電源・GND、DRCを独立監査する。現在の `audit_sync_in.py` は全6ネットの導通を要求するため、現候補のままでは合格しない見込み。

## 8. FPGAの現行状態と限界

ソースは `rtl/`、テストは `sim/`、最新の実装結果は `implementation/output_release/`。基板作業中にRTLを変更していない。古い実装フォルダーを最新と思い込まない。

- 2ラインバッファ、ライン倍化、フィールド単位のBob処理。外部フレームメモリなし。実機での遅延測定は未実施。
- `gowin_video_pll.sv`：基準ケースのADCクロック28.375MHz、映像クロック56.75MHz、rPLL PSDA_SEL="1000"（180度）、IDIV0/FBDIV1/ODIV8、VCO454MHz。24MHz条件でODIV8のままではVCO384MHzになり400MHz未満という課題がある。
- DACクロックはODDR（D0=0/D1=1等）から出力し、バッファU6と直列抵抗を通す。
- `dac_output_stage.sv`はRGB/BLANK/H/Vの出力FF段を備える。出力許可の解除は非同期抑止、復帰は2段同期化し、最初の2立上りを抑止して3回目で取り込み。通常動作では1映像クロック分の段遅延。
- 起動リセットはREFクロック32回のシフトレジスター。実GSR・ブートピン・実機電源立上りの確認は未完了。
- ADC初期化は36レジスター書込み＋ALC待ち。I²C読戻しは未実装。
- ADCクロック停止を監視して黒出力・PSAVE・PLL再始動を制御するロジックあり。
- Amigaの交互の長短ラインを連続して処理する対応は未完了。現状の厳密な固定ライン長判定では異常判定・再同期になる。PAL/NTSCの実入力プロファイルを確定する必要がある。

保持している検証結果：出力段593チェック（RTLと合成後）、統合12,261可視RGBチェック、180度取り込み24条件/5,472サンプルなど。これはモデル上の機能確認。

1816条件の実装はLUT4 1,106、FF701、単一ドメインFmax89.53MHz、2048条件はLUT4 1,126、FF703、84.59MHz。RAM6/PLL1/ODDR1。専用配線で `logic_core.adc_rgb[6]` を配線できなかった警告が残り、通常配線で完了している。警告0とは言わない。

タイミング解析は部分的。ADC側の未モデル化パス、PLL不確かさ、hold、ODDR/OBUFパッド/基板の遅延、出力リセットのrecovery/removalが不足。リセット27経路のSDFにはrecovery/removalチェックがない。単一ドメインFmaxや機能試験を外部タイミングのサインオフに置き換えない。完成ビットストリームは未生成。

## 9. 実行環境・再開の要点

元環境はWindows/PowerShell。作業ルートは `C:/Users/zanac2/Documents/Codex/2026-09-08/m`。移行先では相対構成を保てばよい。

KiCad 7付属Python：`C:/Program Files/KiCad/7.0/bin/python.exe`。CLI：同ディレクトリーの `kicad-cli.exe`。KiCad 7 CLIには `pcb drc` がない。検査には `pcbnew.WriteDRCReport(board, path, pcbnew.EDA_UNITS_MILLIMETRES, True)` を使っている。

PowerShellでの準備例（展開先のルートで実行）：

```powershell
New-Item -ItemType Directory -Force work/kicadconfig | Out-Null
$env:KICAD_CONFIG_HOME="$PWD\work\kicadconfig"
$env:KICAD7_FOOTPRINT_DIR='C:\Program Files\KiCad\7.0\share\kicad\footprints'
```

入力同期を修正後に再生成・監査する例：

```powershell
& 'C:\Program Files\KiCad\7.0\bin\python.exe' work/route_sync_in.py
Copy-Item outputs/amiga_scandoubler/hardware/amiga_scandoubler_sync_out.kicad_pro outputs/amiga_scandoubler/hardware/amiga_scandoubler_sync_in.kicad_pro
& 'C:\Program Files\KiCad\7.0\bin\python.exe' work/audit_sync_in.py
```

生成スクリプトは出力を上書きする。手配線を加えた後の不用意な再生成は避ける。`.kicad_pro`をコピーしてから監査し、規則・ライブラリ設定を揃える。監査も報告ファイルを更新するので、基準版のマニフェストを不用意に変えない。

元のIcarusは `work/tools/simulator_path.txt` にあった一時ディレクトリーを参照していた。移行先で再インストール・パス指定が必要。Windowsのiverilogは必要に応じて `-B <install>/lib/ivl` を指定。テストランナーの引数は同梱ソースまたは `--help` で確認する。

元の合成/P&Rは `work/tools/pnr_v015/oss-cad-suite/` のネイティブWindows版。Yosys0.69+24 d0e71cfb7-dirty、nextpnr-himbaechel0.11.1-26-ga601751d、対象GW1N-LV4QN88C6/I5/family GW1N-4。元のOSS CAD Suite 2026-09-12アーカイブSHA256は `2e41548bee9c6ea875019f4d1e0c636da92e6ab5bf9c97698a78ab9048ab1c06`。suite/libをPATHへ、nextpnrではPYTHONHOMEもsuiteへ指定していた。実行ファイルは同梱していない。

基板配線のみの変更でFPGAの全再合成を毎回行う必要はない。反対にRTLやピン割り当てを変えた場合は適切な検証を行う。合成/P&R再構築の手順・制約は同梱フォルダーを確認する。

## 10. 過去に分かった作業上の注意

- 自動配線は0.05mmグリッドの簡易A*、基本間隔0.205mm。DRCの0.20mmを維持するための余裕。最短・低ノイズ・インピーダンスを保証するものではない。
- 特に電源・GNDを先に引くとIC端子を囲い込み、信号を引き出せなくなる。無意味な反復より、実際の障害物と端子周辺の引き出しを調べる。
- 表面で接続可能というだけで大迂回を採用しない。R34の例があり、裏面との長さ比較を行う。グリッド上の微小な折れや不要な枝も整理する。
- 同じネットのビア同士でも穴間隔を守る。全層を貫通するビアは全層の障害物を確認する。
- KiCad 7のSWIGでは、削除した配線オブジェクトを参照リストに保持しないと、処理中にラッパー型が壊れる挙動を経験した。`held`等で保持する。終了時のSWIG警告と実際のDRC結果は区別する。
- `Select-Object -First`で実行中Pythonの出力を切ると、意図せずプロセスを途中終了させ得る。ログへ保存し、終了後に必要部分だけ読む。
- KiCad SVGエクスポートは、ファイルを書いた後に終了しないことがある。既存の図はタイムアウト終了後、SVGのXMLとレンダリングを確認している。正常終了したと偽っていない。
- 過去の一括更新・リリース用スクリプトを無条件に再実行しない。非冪等な変更や後からの手配線の上書きがある。まず入力・出力を読む。
- 「独立監査」はKiCadの実際の接続情報をたどる処理。生成スクリプトの成功ログだけを証拠にしない。

## 11. 最終的に残る仕事

1. 入力同期の未完了3ネットを解消し、独立監査。候補を完成と取り違えない。
2. 残るADCのRGB入力・未使用入力処理、24bit ADC→FPGA/FPGA→DAC、クロック、I²C、JTAG、リセット/設定、POWER_GOOD等の配線。
3. U6用C53等の未配線支持部品の配置を対象IC近傍に見直す。C53はまだ入力側近くにあり、U6は出力側にある。
4. 電源品質、GND帰路、IC露出パッドの放熱・サーマルビア・はんだ工程、信号の戻り経路、補償/基準端子のアナログ配線を再評価。ADC/FPGA露出パッドの細いGND接続だけでは放熱設計の根拠にならない。
5. シルク整理、コネクタ寸法/機械干渉、全フットプリント照合、部品調達・実装可否・MLCC容量・USB電源条件を確定。
6. FPGAの実PAL/NTSCプロファイルと長短ライン、外部タイミング、FPGA起動設定、ビットストリーム作成、実機映像/遅延/電源/温度を検証。
7. 最終DRC/ERCとBOM/CPL/実装面・回転を照合し、製造可能なGerber/ドリル・BOM/CPLを生成。未検証の試作品ならその限界を明記し、完成品と称しない。実際の購入・発注は別途ユーザーの依頼が必要。

一次資料：TI TVP7002（https://www.ti.com/lit/ds/symlink/tvp7002.pdf）、TPS62160（https://www.ti.com/lit/ds/symlink/tps62160.pdf）、SN74LVC1G17（https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf）、Analog Devices ADV7125（https://www.analog.com/media/en/technical-documentation/data-sheets/ADV7125.pdf）。Gowinのパッケージ/PLL/IOLOGIC資料も現物で照合する。部品入手性や製造規則は変わるため、最終段階で改めて確認する。
