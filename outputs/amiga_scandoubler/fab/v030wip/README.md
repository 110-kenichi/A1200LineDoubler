# 製造データ v0.30wip（2026-09-29）

**発注用の確定版ではない。** JLC などへのアップロードはしていない（CLAUDE.md の規則）。

## 中身
| ファイル | 内容 | 作り方 |
|---|---|---|
| `gerber/*.gtl .g2 .g3 .gbl` | 銅箔4層（F / In1=GND / In2=3V3 / B） | `kicad-cli pcb export gerbers`（KiCad 7.0.11、Protel 拡張子、Value を除外、シルクからマスク開口を削る） |
| `gerber/*.gts .gbs .gtp .gbp .gto .gbo .gm1` | マスク、ペースト、シルク、外形 | 同上 |
| `gerber/*-PTH.drl`, `*-NPTH.drl`, `*_map.svg` | ドリル（Excellon、mm、PTH と NPTH を分割）と穴位置の図 | `kicad-cli pcb export drill --excellon-separate-th --generate-map` |
| `cpl_raw.csv` | KiCad の部品位置データ（上面139点） | `kicad-cli pcb export pos --side front` |
| `jlc_cpl.csv`, `jlc_bom.csv` | JLC 形式の CPL と BOM（37行） | `work/v030wip/w30/scripts/r10_fab.py` |
| `parts_to_select.csv` | LCSC 番号が未選定の部品（32行、132点） | 同上 |
| `fab_check.json` | ドリルのヒット数と基板の照合結果 | 同上 |
| `preview_top.png` | 上面のプレビュー（gerbv で描画） | gerbv |
| `bitstream/*.fs` | FPGA ビットストリーム（H_SAMPLES 1816 / 2048） | apycula `gowin_pack -d GW1N-4 --sspi_as_gpio`（v0.31 cst で配置配線した結果から） |
| `*SHA256SUMS` | 各ファイルのハッシュ | sha256sum |

## 検査（実測）
- 対象の基板：`hardware/amiga_scandoubler_v030wip.kicad_pcb`。
- DRC：エラー0件、未接続0件。
  - 残っている警告は、ライブラリ設定（lib_footprint_issues、クラウドにライブラリの設定がないため）と、USB コネクタ J3 の外形シルクが基板端にかかる2件。
- 監査 `audit_sync_in_k7.py`：PASS（139部品、600パッドのネット）。
- 回路図とネットリストと基板のネットは一致（595ノード）。
- ドリル：PTH 303 ＝ ビア295 ＋ PTH パッド8、NPTH 6。基板と一致した。
- RTL シミュレーション：12本すべて PASS（`work/v031dac/sim/`）。

## 発注前に必要なこと（未完了）
1. **部品選定**：LCSC 番号が入っているのは139点中7点だけ。`parts_to_select.csv` を見て選び、manifest か BOM に記入する。F1 は未選定（「1A hold - select」）。
2. **CPL の回転**：KiCad と JLC では、部品の向きの基準が違う場合がある（SOT-23、WSON、QFN、コネクタなど）。JLC のプレビューで全数を確認する。
3. **ビアの処理**：U1/U2 の EP 内のビアと、J2.7/J2.8 のパッド上のビアは、**充填（plugged / via-in-pad）**を指定する。ほかのビアは蓋（tented）。
4. **層構成**：インピーダンス制御は指定していない。JLC の標準4層（1.6mm）を想定。
5. **ビットストリーム**：
   - apycula のオープンソースツールで生成したもので、実機でも Gowin 純正ツールでも未検証。
   - 生成時に apycula が「IOLOGIC の INIT が未処理」と表示した（ODDR の初期値）。
   - H_SAMPLES 1816/2048 は暫定値で、PAL/NTSC の確定値ではない。
6. **ERC**：KiCad 7 の CLI では実行できないため未実行。利用者PCの KiCad 7 で実行する。

## 部品選定（2026-09-29、JLCPCB の部品検索 API で在庫・価格を取得）
- スクリプト：`work/v030wip/w30/scripts/r11_select.py`（選定）→ `r11_apply.py`（manifest、回路図、ネットリストへ反映）。
  - 仕様は `r11_parts_spec.json`。API の呼び出しは `tools/jlcsel.py`（読み取りのみ。注文はしていない）。
- 結果は `parts_selection.csv` / `.json`：LCSC 番号、基本/拡張の区分、在庫、5枚分の数量での単価、代替2件。
- 選定の規則：
  - パッケージと仕様（容量、耐圧、誘電体、抵抗値、許容差、0.1% は薄膜）が一致するもの。
  - 基本部品 → 優先拡張部品 → 在庫の多いもの、の順。
  - 在庫は必要数の20倍以上を優先する。
- 確定したもの：37行中 35行（135点）。
  - 基本部品 15行、拡張部品 22行。
  - 部品代の目安は約 60.7 USD/枚（取得時点の単価。拡張部品の手数料と基板代は含まない）。
- 耐圧：C55/57/59（5V 入力）と C47/C54 は 25V の 10uF（CL21A106KAYNNNE、C15850）。回路図の値の表記「10V」は最低定格の意味として残した。
- **2026-09-29 追記（利用者の判断）**：
  - 製作は **2枚**。選定の数量も2枚分でやり直した（`BOARDS=2`）。
    - JLCPCB の PCBA は Economic・Standard とも最少2枚（公式の capabilities ページで確認）。
  - **Y1 を YXC OT2EL4C4JI-111OLP-27M（C5203549）に置き換えた**（`scripts/r12_y1.py`）。フットプリントは同じ。
  - U1 TVP7002（C3824085）はそのまま使う。在庫4個で、必要数2個に対して余裕は小さい。
  - J1/J2（C3146802）は在庫0のため、JLCPCB の **Global Sourcing** で調達する前提にした。LCSC 番号は記入済み。
- 全139点の LCSC 番号がそろった。部品代の目安は約 60.3 USD/枚（2枚分の数量での単価。拡張部品の手数料、Global Sourcing の費用、基板代は含まない）。

## U1・U2 を手はんだにする場合（別版）
- `jlc_bom_dnp_U1U2.csv`、`jlc_cpl_dnp_U1U2.csv`：U1（TVP7002、HTQFP-100 と EP）と U2（GW1N、QFN-88 0.4mm と EP）を除いた版。137点。
- 必要なもの：
  - 両方とも裏の EP（GND）のはんだ付けが必須で、ホットエアかホットプレートが要る。U2 は端子も裏にあるため、はんだごてでは付けられない。
  - ステンシルは JLCPCB に同時に注文できる。
  - U1/U2 は別に購入する。LCSC なら C3824085 / C31900351。
- ビアの指定：
  - ホットエアやホットプレートで付ける場合は、EP 内のビアを充填（plugged）にする。はんだの吸い込みを防げる。
  - 裏からビア越しにはんだを流す方法をとる場合は、充填しない指定にする必要がある。
- 取り付けの順番の推奨：JLCPCB の実装品が届いたら、先に U2、次に U1 を付ける。そのあと電源を単体で確認してから、ビットストリームを書き込む。
