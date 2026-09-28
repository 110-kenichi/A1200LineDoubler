# 主要部品の選定状況

2026-09-10更新。これは完成BOMではない。回路図の134部品は`hardware/circuit_manifest.json`に登録済み。配置検討用の座標は`hardware/placement_report.json`にあるが、発注用CPLではない。受動部品の注文型番・定格、保護回路、各部品の調達・実装条件には未確定項目が残る。

| 機能 | 候補 | 確認できた番号・資料 | 残る確認 |
|---|---|---|---|
| RGB ADC | TVP7002PZP | JLCPCB C3824085、TI製品ページACTIVE | 最新在庫、実装余剰数、RGB15kHz用初期値、PLLロックと画質 |
| FPGA | GW1N-LV4QN88C6/I5 | LCSC C31900351、QN88端子表で仮割り当て済み | 実在庫、合成、配置配線、端子機能の実装確認 |
| RGB DAC | ADV7125KSTZ140 | LCSC中国サイト C9668 | JLCPCB国際サービス側での調達・実装可否、電流設定 |
| H/V入力バッファ | SN74LVC2G17（3.3V駆動） | TIデータシートで5.5V入力許容 | 正確なパッケージとJLCPCB番号 |
| 入出力コネクター | CONEC 33DSMT1-E15SNCT | メーカー図面、信号端子SMTの3列DE-15メス | 専用フットプリント、固定脚の実装、JLC調達 |
| USB電源入力 | HRO TYPE-C-31-M-12 | C165948、対応するKiCadフットプリントを配置 | 5Vの給電条件、必要電流、保護、シェル固定脚の実装 |
| 27MHz発振器 | ECS-3225MVLC-270-CN-TR | メーカー資料、専用ランド作成 | JLC調達番号、実在庫 |
| 電源インダクター | TDK VLS4012CX-2R2M-1 | C7413169、メーカー推奨ランド | 実在庫、電源回路での温度・電流の確認 |
| 電源 | TPS62160DSGR ×3 | 3.3V、1.9V、1.2V。3.3V PGで1.2Vを有効化 | 受動部品定格、効率、発熱、リップル、立ち上がり、USB給電条件 |

FPGAのピン数は映像入出力だけで48本、クロック・同期・I²C・リセット・JTAG等を加えると60本以上を見込む。40～45GPIO級の小型パッケージは避ける。2048画素×24bit×2の記憶には約98kbitが必要。GW1N-4の180kbit、GW1N-9の468kbitは容量面では候補になるが、BRAMの構成単位に丸めた合成結果で判断する。

JLCPCBの検索結果にある「JLCPCB Assembly」名義、ゼロ在庫、数セントの価格は、IC自体がその価格で購入できる根拠にしない。委託実装用の登録である可能性を含め、メーカー型番との照合が必要。カタログ掲載と発注できる在庫を区別する。

在庫数量は変動し、今回の検索結果には過去に取得されたページが含まれる。注文枚数と実装予備数に足りる現時点の数量は未確認。部品購入やJLCPCBへの発注は行っていない。

参照：

- [TI TVP7002](https://www.ti.com/product/TVP7002)
- [JLCPCB TVP7002PZP](https://jlcpcb.com/partdetail/TexasInstruments-TVP7002PZP/C3824085)
- [LCSC GW1N-LV4QN88C6/I5](https://www.lcsc.com/product-image/C31900351.html?whichImg=sch)
- [CONEC DE-15メーカー図面](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/1039/33DSMT1-E15SNCT_Dwg.PDF)
- [TI TPS62160](https://www.ti.com/product/TPS62160)
- [LCSC ADV7125KSTZ140](https://item.szlcsc.com/10198.html)
- [GOWINメモリ・I/O仕様](https://www.gowinsemi.com/en/product/littlebee_fpga/)
- [JLCPCB BOM/CPL説明](https://jlcpcb.com/help/article/how-to-generate-bom-and-centroid-files-from-kicad-8)
