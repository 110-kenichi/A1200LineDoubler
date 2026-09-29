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
