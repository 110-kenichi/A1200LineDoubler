# v0.19 DAC出力段を同期化

RGB/BLANK/H/Vを同時に1クロック遅延。追加部品なし。単体RTL・合成後各516件、全体12,261件、両プロファイルの配置配線と接続検査を通過。詳細は `output_stage_review.md`。現行実装は `implementation/output_stage/`。製造用ではない。
