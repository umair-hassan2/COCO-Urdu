# Repair report: gemma27b

Source: `data/translations/gemma27b.parquet` (317,829 captions) · map: `repairs/script_contamination_gemma27b.tsv`
Repaired corpus: `data/translations/gemma27b_repaired.parquet` — the raw file is left untouched.

| | forms | occurrences |
|---|---|---|
| applied (verified) | 396 | 6,790 |

| | captions | rate |
|---|---|---|
| contaminated before | 6,723 | 2.115% |
| contaminated after | 31 | 0.010% |
| repaired | 6,692 | — |

## Still contaminated (70 forms)

Rows in the map with an empty `replacement`, or marked `rejected`.

| form | occurrences |
|---|---|
| `ہیں—ایک` | 2 |
| `आपत्तिजनक` | 2 |
| `शब्द` | 2 |
| `@` | 2 |
| `¾` | 2 |
| `چیزیں—ایک` | 1 |
| `کتاب—نمائش` | 1 |
| `کھانے—جیسے` | 1 |
| `دودھ—کے` | 1 |
| `جہاز—ایک` | 1 |
| `"#480` | 1 |
| `نیچے—ایک` | 1 |
| `*intended*` | 1 |
| `$3.69"` | 1 |
| `#20` | 1 |
| `*most*` | 1 |
| `ہاتھی—ایک` | 1 |
| `چھوٹا—باہر` | 1 |
| `शामिल` | 1 |
| `है।` | 1 |
| `मैं` | 1 |
| `एक` | 1 |
| `सुरक्षित` | 1 |
| `और` | 1 |
| `सम्मानजनक` | 1 |

## Degenerate captions (26)

These repeat a phrase and cannot be fixed by substitution — regenerate or exclude them.

- `207763:7420edee` — Two girls wearing black shorts are in a park while one girl holds her leg up in front of the other as the other holds a white Frisbee.
- `397475:b42cbc3a` — One man preparing to catch a Frisbee as another man guards him.
- `388599:3c5bf235` — A yellow dog holds one side of a Frisbee while a hand holds the other side.
- `171443:4ad782c3` — In the background a ramshackle fence separates the street level with street lamps. buildings and pedestrians under a stand, while in the foreground a young man in swim trunks is standing on a sandy beach, an arm on his hip, awaiting a frisbee.  
- `560272:aff14341` — Two planes- one flying right side up, the other flying upside down.
- `143876:363db32e` — A cat inside a truck and a cat sitting on top of a truck.
- `481064:0d1013dc` — One boy in a black t-shirt holds a Frisbee as another boy in a white t-shirt faces him and both are in front of a house.
- `454449:f8608794` — An owl looking up at somebody looking at it.
- `206539:aac3eeb7` — A woman wearing tight jeans holding a Wii game controller next to a man also holding a controller.
- `8909:dc35a260` — A girl in a blue shirt throwing a blue frisbee.

## Audit trail

- `results/contamination_before.txt` — every affected caption, as the model produced it
- `results/contamination_after.txt` — the same captions, same order, after repair
- `results/contamination_diff.txt` — uid, English source, before and after together
