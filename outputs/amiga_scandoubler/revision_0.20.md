# v0.20 出力リセット解除を2段同期化

通常の画素遅延は維持し、起動・復帰だけ2立上り保持。単体RTL・合成後各593件、全体12,261件PASS。27解除経路×2条件を解析。詳細は `output_release_review.md`、現行実装は `implementation/output_release/`。製造用ではない。
