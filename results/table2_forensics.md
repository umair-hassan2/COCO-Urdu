# Table 2 forensics

Flagged subset (final_score < 0.7): **3,572** captions.
Refined MT differs from v1 MT in 99.7% of rows; refined *reference* differs from NLLB ref in 97.3% of rows.

| Pairing | BLEU | chrF++ |
|---|---|---|
| (a) v1 MT vs NLLB ref  [paper 'before'] | 34.50 | 57.47 |
| (b) refined MT vs refined ref  [paper 'after'] | 79.74 | 84.51 |
| (c) refined MT vs ORIGINAL ref  [honest 'after'] | 56.52 | 66.98 |
| (d) refined ref vs ORIGINAL ref  [ref drift] | 46.43 | 59.62 |

Interpretation: if (b) >> (c), the reported gain came from scoring one LLM output against another from the same prompt.
Code evidence (legacy notebook): prompt asks to improve A=Reference and B=MT; the code then sets `refined_mt = A` and `refined_ref = B` (swapped) and overwrites both columns before computing metrics.
