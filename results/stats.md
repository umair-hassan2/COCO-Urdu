# COCO-Urdu v1 counts (computed from the public HF datasets)

- Images: **63,549** ({'train': 58549, 'validation': 5000})
- Captions: **317,921** ({'train': 292907, 'validation': 25014})
- Captions/image: mean 5.00, range 5–7
- Flagged by v1 hybrid score < 0.7: 3,572
- Empty Urdu outputs: 0

| v1 QE metric | mean | std | n < 0.7 |
|---|---|---|---|
| comet_score | 0.755 | 0.094 | 80,344 |
| bert_score | 0.970 | 0.023 | 4 |
| clip_score | 0.749 | 0.124 | 98,003 |
| final_score | 0.840 | 0.050 | 3,572 |
