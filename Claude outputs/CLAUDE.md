# CLAUDE.md — Amiga 1200 スキャンラインダブラー（15kHz→31kHz）

最終更新: 2026-09-28（Cowork クラウドセッションから Claude Code へ移行）
作業フォルダ（利用者PC）: `E:\A1200\A1200 Line Doubler\`

---

## 0. 最初に読むこと（厳守ルール）

1. **発注・購入・公開・外部送信はしない。** 依頼されていない。JLCPCB へのアップロード、部品購入、GitHub 公開などは禁止。
2. **KiCad 7 形式（`(version 20221018)`）を維持する。** 利用者は KiCad 7 を使う。KiCad 8 以降で保存しない。
   - クラウドでは KiCad 10 の CLI を DRC 専用に使い、基板は行単位のテキスト編集（`tools/pcbedit.py`）で変更した。
   - 利用者PCの KiCad 7 の pcbnew（Python を含む）なら、ゾーン再充填も保存も直接できる。この場合 `refill_v7.py` は不要。
3. **承認済みの方針は変えない。**
   - DE-15 メスの入出力、USB 給電。
   - 95×95mm の 4層基板。
   - Amiga 側ケーブルはバッファなし（UNBUFFERED）。
   - 処理は Bob 方式で低遅延。フレームメモリは持たない。
4. **クレジットを節約し、品質は最大に。** 可逆な通常作業は毎回確認せずに進めてよい。不可逆な判断や方針の変更だけを確認する。
5. **変更後は毎回検査する。** 手順は次のとおり。
   - DRC（`--refill-zones`）を実行する。
   - 前版と未接続をネット単位で比較する（`uncmp.py`）。
   - 監査（`audit_sync_in.py`）を実行する。
   - 版ごとに `revision_0.xx.md` を残す。
   - 数値は推定と実測を区別して書く。「未検証」を「合格」と書かない。
6. 報告は日本語で簡潔に書く。

---

## 1. 製品仕様（設計方針）

| 項目 | 内容 |
|---|---|
| 入力 | Amiga 1200 の RGB（15kHz、アナログ RGB＋H/V 同期）。DE-15 メス |
| 出力 | 31kHz VGA（DE-15 メス）。水平周波数は入力の2倍（PAL 約31.25k、NTSC 約31.47k）。垂直周波数は入力のまま |
| 方式 | ラインダブラー（Bob）。各入力ラインを2倍の画素クロックで2回出力する。インターレースは各フィールドを独立に倍化し、奇偶のフィールドを合成しない |
| メモリ | ラインバッファ 2048画素×24bit×2本（約98kbit）。フレームメモリなし |
| 遅延 | 1回目の出力は0.5H～H、2回目はH～1.5H（H≈64µs なので約32～96µs）。ADC/DAC/FPGA のパイプライン遅延が加わる。目標は基板単体0.2ms以下（未測定） |
| 画素 | RGB888（HAM8 も含め、入力されたRGBをそのまま標本化） |
| 同期喪失・モード変更 | 映像を消し、再ロックしてから再開する |
| 電源 | USB-C 5V（CC1/CC2 に独立した 5.1k Rd）。TPS62160×3 で 3.3V / 1.9V / 1.2V を生成（3.3V の PG で 1.2V を有効化） |
| 基板 | 4層。L1＝部品と信号、In1＝GND ベタ、In2＝3V3 ベタと電源配線、L4（B.Cu）＝信号。部品は原則として上面のみ |

---

## 2. 回路構成（主要部品）

| Ref | 部品 | 役割・要点 |
|---|---|---|
| U1 | TI TVP7002PZP（TQFP-100、EP付き） | RGB ADC。3.3V と 1.9V（A/PLL は別フィルター）。FPGA から I²C で初期化する |
| U2 | Gowin GW1N-LV4QN88C6/I5（QFN-88、EP=pin89 GND） | ラインダブラー本体。1.2V コア、3.3V I/O。**基板上で180°回転済み（v0.29）** |
| U3 | ADI ADV7125KSTZ140 | RGB DAC。PSAVE_N＝FPGA 56番（R44 4.7k で GND へプルダウン） |
| U4 | SN74LVC2G17 | H/V 入力同期のバッファ（5V 入力に耐え、3.3V へ変換） |
| U5 | 出力同期バッファ | H/V_OUT |
| U6 | DAC クロックバッファ | DAC_CLK_RAW(16番) → DAC_CLK_BUF → R24 → U3 |
| U8, U9 | 電源（POWER_GOOD 系） | POWER_GOOD は FPGA 62番へ |
| Y1 | 27MHz 発振器 ECS-3225MVLC-270 | REF_27M。R36 で分岐し、U1.80 と U2.11 へ |
| J1 / 出力 | CONEC 33DSMT1-E15SNCT | 3列 DE-15 メス（信号端子SMT）。2列15ピン品を誤って採用しないこと |
| J4 | JTAG/設定ヘッダ | JTAG_TMS/TCK/TDI/TDO、RECONFIG_N |
| USB | HRO TYPE-C-31-M-12 | 5V 給電のみ |

部品は134点。部品番号と数量は `hardware/circuit_manifest.json` にある。完成 BOM ではない（在庫・定格・調達は未確定）。

---

## 3. FPGA とタイミング仕様

- ツール：OSS CAD Suite 2026-09-12（Yosys 0.69+24、nextpnr-himbaechel 0.11.1-26-ga601751d）
- 配置配線コマンド：
  ```
  nextpnr-himbaechel --device GW1N-LV4QN88C6/I5 --vopt family=GW1N-4 \
    --json implementation/output_release/board_{1816|2048}.json \
    --vopt cst=constraints/amiga_board_top.cst --vopt sspi_as_gpio \
    --sdc implementation/exploratory_periods.sdc --freq 56.75 \
    --write ..._routed.json --report ..._timing.json --sdf ....sdf --log ....log
  ```
  完全な手順は `implementation/output_release/commands.txt` を参照（合成、配置配線、`verify_phase180.py`、`analyze_dac_sdf.py`、`analyze_capture_sdf.py --phase 180 --implementation output_release`、シミュレーション）。

| クロック | 周波数 | 備考 |
|---|---|---|
| clk_ref | 27.00MHz | Y1。監視と I²C 制御に使用 |
| ADC_CLK（adc_clock） | 約28.375MHz | TVP7002 の DATACLK。**U2.63（PLL 入力ピン、変更不可）** |
| video_clock | 56.75MHz | PLL で ADC クロックの厳密な2倍を生成。**位相180°（PSDA_SEL=1000）**、デューティー50% |
| DAC クロック | video に対して反転 | ODDR 出力を U2.16 から出す |

- ADC 取り込み（負エッジ→映像正エッジ、26経路）の暫定予算：
  - 2048画素条件：+4.269ns。
  - 1816画素条件：+3.786ns。
  - いずれも High 52%、180°の理想間隔8.106ns からの差。
  - 挿入 LUT の SDF 遅延が欠落しており、625ps を借用して補った推定値である。最終的なスラックではない。
- DAC データ側の最大抽出遅延は3.632ns（OBUF、基板、負荷を含まない）。
- 出力の解除は2段同期。recovery/removal 規格が SDF にないため、最終判定はしていない。
- 1816/1820 は暫定の検討値で、PAL/NTSC の確定値ではない。

**v0.30wip の新ピン割当（`fpga/amiga_board_top_v030wip.cst`）で nextpnr を再実行した結果：** 1816／2048 とも全クロックが PASS（2048：video 89.05MHz、adc 310.75MHz、clk_ref 73.15MHz）。ただし次は未実行で、ピン変更後に必ず実行する。
- `analyze_capture_sdf` / `analyze_dac_sdf` / `verify_phase180`
- シミュレーション

---

## 4. FPGA ピン割当（v0.30wip 現行）

U2 を180°回転したため、**左辺（x=45.05）が U1(ADC) 側**、右辺（x=54.95）が U3(DAC) 側になっている。

| 信号 | ピン | 変更 |
|---|---|---|
| ADC_R0–R7 | 48–55（左辺） | ADC 再ピン（v0.30） |
| ADC_G0–G7 | 68–75（下辺） | 同上 |
| ADC_B0, B1 | 76, 77 | 同上 |
| ADC_B2–B7 | 79–84 | 同上 |
| ADC_HS / ADC_VS | 85 / 86 | 同上 |
| ADC_CLK | 63 | 不変（PLL 入力） |
| DAC_PSAVE_N | 56 | 不変 |
| I2C_SDA | 57 | 変更（旧14） |
| I2C_SCL | 59 | 変更（旧13） |
| ADC_RESET_N | 60 | 変更（旧15） |
| ADC_PWDN | 61 | 変更（旧57） |
| POWER_GOOD | 62 | 不変 |
| H_OUT_RAW / V_OUT_RAW | 13 / 14（右辺） | 変更（旧60/61） |
| DAC_BLANK_N | 15 | 変更（旧59） |
| REF_27M | 11 | 不変 |
| DAC_CLK_RAW | 16 | 不変 |
| DAC_R0–R3 | 17–20 | 不変（DAC 再ピンは未検討） |
| DAC_R4–R7, G0–G7, B0–B5 | 25–42（上辺） | 不変 |
| DAC_B6 / B7 | 47 / 3 | 不変（47番は左上にあり配線上不利） |
| JTAG, JTAGSEL_N, RECONFIG_N, DONE, MODE0/1 | 4–10, 87, 88 | 固定 |

制御線の並びは、U1 側の上下順（SDA 36.0 → SCL 36.5 → RESET 38.0 → PWDN 38.5）と一致させた。こうすると交差なしで配線できる。

---

## 5. 基板の現状（v0.30wip）

- 基板：`board/amiga_scandoubler_v030wip.kicad_pcb`（KiCad 7 形式。DRC 結果は `v030wip_drc.txt`）
- DRC 結果：
  - エラー（短絡、クリアランス、穴間隔、配線端・ビアの未接続）0件。
  - 未接続112件（v0.29 は143件）。
  - シルクと `lib_footprint_mismatch` の警告は既知。
- 注意：電源監査（`audit_sync_in.py`）は **C34 が原因で FAIL**（後述の課題1）。

### v0.29 からの変更（v0.30wip）

1. FPGA の ADC 再ピンに合わせてデジタル部を再配置した。
   - U1 下辺のパスコン（C19–C22、C32–C34、C39、C41、C64、C65、R2、R3、R37、R39、R40 など）を移動した。
   - U1 の EP に GND サーマルビア群を追加した。
2. ADC データ24本を**すべてビア0で配線**した。
   - R バス：U1 右辺 → 45° の入れ子 → U2 左辺 48–55（`rbus3.py`、F.Cu）。
   - G/B バス：U1 下辺 → U 字帯 → U2 下辺（`uband.py`、F.Cu）。
   - 面取りは c = 0.3 + 0.234k（0.4mm ピッチ用）。
3. ADC_CLK：U1.28 → ビア(20.9,50.85) → B.Cu 回廊 y=44.4 → ビア(41.9,43.95) → F.Cu → U2.63。ビアは2個。
4. ADC_HS/VS：U1.24/23 から 0.127mm 幅で西へ引き出し、ビア(17.5,48.9)/(16.75,48.5) を置いた。
   - 引き出しの通路を空けるため、GND ビア 16.27,48.5 を 15.95,48.5 へ、17.1,46.55 を 17.15,46.45（0.5/0.3）へ移した。
   - その先は**南回り**：B.Cu → F.Cu ホップ（H/V_IN_3V3 を越える）→ B.Cu y≈55 → U2 下辺。
   - VS は U2 内周ビア(53.2,45.96)、HS は下辺ビア(53.2,48.05)に着く。各ビア4個。
5. 1V2 の U2 左側リンクを B.Cu から **In2.Cu（y=37.225、0.4mm、ビア 44.0↔58.0）** へ移した。U2 左の B.Cu の壁がなくなった。
6. U2 のパッドネットを入れ替えた（13/14/15/57/59/60/61。4章の表のとおり）。

---

## 6. 未解決の課題（優先順）

1. **C34（U2.58 の 3V3 パスコン）が孤立している。** 配置移動で (37,30) へ飛ばしてしまった。
   - 3V3・GND とも未接続で、監査は FAIL。
   - U2.58/64 の近くへ戻し、面へのビアを付けること。
2. **U2 左の制御線**（SDA/SCL/RESET/PWDN → U1.75/74/71/70 とプルアップ R38/R37/R39/R40）
   - 試作案（スクリプト `ctl.py`、`ctl2.py`、`left.py`）：
     - U2 前面ビア：SDA(44.05,42.6)、SCL(43.3,43.15)、RESET(42.55,43.5)、PWDN(41.8,43.6)。
     - U1 内周ビア：(32.2,36.2)、(32.3,36.95)、(32.45,37.8)、(32.45,38.55)。
     - 間を B.Cu で結ぶ。
   - PWDN と RESET は成功した。SCL は迂回し、SDA は F.Cu ホップになり、クリアランス違反が2件出た。**やり直しが必要。**
   - REF_27M の B.Cu（y=35.6、x 30.4–37.75）と In2 の 1V9（x=32.8、y≤35.55）が U1 側ビアの制約になる。
   - `left.py` の内容：CLK をビア(43.95,45.0)で終える、pin64 の 3V3 を内周ビアへ、PG/PSAVE を内周ビアへ。
     - pin64 の 3V3 内周ビア(46.04,45.25)は GND スタブ(y45.8)とのクリアランスが不足する → y≈45.2 に調整すること。
3. POWER_GOOD（62）→ 南の既存配線(49,71)/(60.175,65.7)。案：U2 内周ビアから内部を東へ（サーマルビア行 y=42 と 44 の間、y≈43）→ 右辺から出て南へ。
4. DAC_PSAVE_N（56）→ R44/U3.38（右）。内周ビア(46.04,42.1)から U2 内部を東へ抜ける案。
5. 右辺：H/V_OUT_RAW（13/14）→ R41/R42 の既存の途中配線（ビア 67.3,48.625 / 65.875,49.8）、DAC_BLANK_N（15）→ R14/U3.11、I²C 以外の JTAG/RECONFIG/DONE → J4/R5–R9、DAC_CLK_RAW（16）→ U6/R43。
   - 右側には 1V2 右リンクの B.Cu 壁（x 58–58.75、y 37.2–45.2）がある。
6. **DAC バス24本**（U2 上辺・右辺 → U3）は未配線。必要なら DAC 再ピンを同じ FPGA フローで評価する。
7. 電源の未接続：GND 約31件、3V3 約14件（C53、C61、R6–R9、R38、R40、Y1、J4、U6 ほか）、ADC_3V3A、ADC_1V9PLL、DAC_3V3。
8. アナログ入力の残り：RIN_1–3、BIN_1–2、GIN_3、SOGIN_2（各1件。v0.29 以前から残っている）。
9. ドキュメントの更新（新ピン割当）：
   - `constraints/amiga_board_top.cst`（← `amiga_board_top_v030wip.cst`）
   - `board_port_map.json`、`fpga_pin_assignment.json`、`circuit_manifest.json`（U2 のピン）
   - **`02_fpga.kicad_sch` のグローバルラベル**（ピン対応に合わせて同時に改名する）
   - `rtl/amiga_board_top.sv` のポートは名前のままで変更不要の見込み
10. 仕上げ：シルク整理、最終 DRC/ERC、Gerber/ドリル、JLC BOM/CPL、ビットストリーム。
    - JLC 向け：EP 内の via-in-pad は充填（plugged）または蓋（tented）を指定する。
11. 検証が残っている項目：
    - PLL の実位相とジッター、hold と recovery/removal。
    - DAC 端子での setup/hold、PSAVE Low 時のアナログ出力。
    - PAL/NTSC の実入力プロファイル、長短ラインの連続。
    - ADC_1V9PLL のデカップリング経路（In2 経由）の品質。
    - V_IN_3V3 が U4 本体の下を通過している点の目視確認。

---

## 7. 配線ルールと実装上の知見

- 寸法：クリアランス 0.2、穴クリアランス 0.25、基板端 0.5。信号幅 0.15（狭い部分は 0.127）。ビア 0.55/0.3（最小 0.5/0.3）。GND ビア 0.6/0.3。
- ADC バスは貪欲な A* では通らない。**幾何生成（river routing）**で作る。
- U1（TQFP-100）の内周は幅約3.3mm と広い。内周ビアとして使える。
- U2（QFN-88）の内周は幅1.1mm しかない。
  - ビアは x=46.04 の1列のみ（間隔 ≥0.75）。
  - EP サーマルビアは (48/50/52, 40/42/44)。
  - その間の B.Cu に各2本程度通せる。
- B7(52.6) と MODE1(53.8) の間の溝に置けるビアは1個（x 53.15–53.25）。
- 自作ルーター `tools/router.py`：
  - 0.05mm 格子の A*、F/B 層とビアを扱う。
  - `block()` の矩形にはクリアランスが加算される。細い予約は幅0の線で指定する。
  - 失敗の切り分けには `scripts/reach.py`（到達可能性の flood fill）を使う。
- 監査スクリプト `audit_sync_in.py`：
  - 環境変数 BOARD/TAG で対象を指定する。
  - 連結判定にはゾーンの充填が必要。再充填しないと偽 FAIL になる。

---

## 8. ファイル構成

```
E:\A1200\A1200 Line Doubler\
  outputs\amiga_scandoubler\
    README.md, design.md, *_review.md, revision_0.xx.md   … 設計記録（v0.2〜0.29）
    rtl\        … SystemVerilog（amiga_board_top.sv, line_double.sv, gowin_video_pll.sv, tvp7002_boot.sv など18本）
    sim\        … Icarus テスト（run_*_tests.py、tb_*.sv）
    synthesis\, implementation\output_release\  … 現行の合成・配置配線・解析手順（commands.txt）
    constraints\amiga_board_top.cst, board_port_map.json
    hardware\
      amiga_scandoubler.kicad_sch（01_adc〜06_support）, Amiga.kicad_sym, Amiga.pretty
      amiga_scandoubler_u2rot.kicad_pcb   … v0.29（最後に正式に保存した版）
      circuit_manifest.json, fpga_pin_assignment.json, *_progress.json, power_routing_report.json
  work\audit_sync_in.py
```

Claude プロジェクト（claude.ai）に保存してあるもの：

- `v029/`：v0.29 の基板一式、ツール、`RESTORE.md`、`bundle_v029.tgz.b64`。
- **`v030wip/bundle_v030wip.tgz.b64`（本移行時点の最新）**
  - 内容：`board/`（v030wip の基板、pro、DRC 結果）、`fpga/`（新 cst と P&R ログ）、`tools/`、`scripts/`。
  - 復元：`base64 -d bundle_v030wip.tgz.b64 | tar xz` → `w30/` が展開される。
  - sha256(tgz) = `4ca79e952e21502aed365bb7cfa9259c09d2e1c9c5f280485fdee521e345e03f`

**移行後の最初の作業：**
1. v030wip の基板を `hardware\amiga_scandoubler_v030wip.kicad_pcb` として配置し、KiCad 7 で開けることを確認する。
2. KiCad 7 で DRC を実行し、ゾーンを再充填して保存する。
3. 6章の課題1（C34）から再開する。
4. 区切りのよいところで v0.30 として revision を記録する。

---

## 9. 推奨モデル

- 配線とレイアウトの推論、タイミングの判断：Claude Opus 系（長い文脈で幾何計算と検証を繰り返すため）。
- 定型作業（ラベルの一括改名、JSON 更新、レポート整形）：Sonnet 系で十分。
