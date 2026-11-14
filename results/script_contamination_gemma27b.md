# Cross-script contamination: gemma27b

Source: `data/translations/gemma27b.parquet` — 317,549 captions.
A caption is flagged if it contains a character outside the Arabic/Urdu blocks, Latin,
digits and shared punctuation (`cocourdu.urdu_text.URDU_OK`).

**6,686 of 317,549 captions (2.106%)** are affected: 16,569 characters, 208 distinct.

| system | affected | rate |
|---|---|---|
| gemma27b | 6,686 | **2.106%** |
| seamless_v1 | 0 | 0.000% |

SeamlessM4T produces **none** on the same 317,549 source captions.

## By writing system

| script | captions | % of corpus | characters |
|---|---|---|---|
| Japanese | 4,425 | 1.393% | 9,030 |
| Devanagari | 1,375 | 0.433% | 4,573 |
| Cyrillic | 610 | 0.192% | 1,993 |
| Bengali | 92 | 0.029% | 482 |
| Han | 81 | 0.026% | 187 |
| Gujarati | 62 | 0.020% | 124 |
| Kannada | 35 | 0.011% | 125 |
| Hangul | 16 | 0.005% | 19 |
| Malayalam | 9 | 0.003% | 20 |
| Tamil | 2 | 0.001% | 6 |
| Hebrew | 2 | 0.001% | 4 |
| Telugu | 1 | 0.000% | 2 |
| Thai | 1 | 0.000% | 3 |
| Gurmukhi | 1 | 0.000% | 1 |

## Shape of the contaminated tokens

Denominator is the 6,784 contaminated token occurrences, **not** the 317,549-caption corpus.

| shape | occurrences | % of contaminated tokens | % of corpus tokens |
|---|---|---|---|
| Urdu word with an embedded foreign fragment | 6,496 | 95.8% | 0.163% |
| token entirely in another script | 288 | 4.2% | 0.007% |

## Word-forms

391 distinct forms, 6,784 occurrences.

| # | form | code points | count | % of contaminated tokens | cumulative |
|---|---|---|---|---|---|
| 1 | `فرسビー` | U+30D3 U+30FC | 4,315 | 63.6% | 63.6% |
| 2 | `سноу` | U+043D U+043E U+0443 | 499 | 7.4% | 71.0% |
| 3 | `سجاवट` | U+0935 U+091F | 195 | 2.9% | 73.8% |
| 4 | `دھकेल` | U+0915 U+0947 U+0932 | 154 | 2.3% | 76.1% |
| 5 | `کشتियों` | U+093F U+092F U+094B U+0902 | 128 | 1.9% | 78.0% |
| 6 | `মূর্তি` | U+09AE U+09C2 U+09B0 U+09CD U+09A4 U+09BF | 63 | 0.9% | 78.9% |
| 7 | `جیーンズ` | U+30FC U+30F3 U+30BA | 49 | 0.7% | 79.6% |
| 8 | `उल्लू` | U+0909 U+0932 U+094D U+0942 | 47 | 0.7% | 80.3% |
| 9 | `ٹमाटर` | U+092E U+093E U+091F U+0930 | 41 | 0.6% | 80.9% |
| 10 | `جंगली` | U+0902 U+0917 U+0932 U+0940 | 39 | 0.6% | 81.5% |
| 11 | `ٹमाटर،` | U+092E U+093E U+091F U+0930 | 39 | 0.6% | 82.1% |
| 12 | `سجاवटी` | U+0935 U+091F U+0940 | 37 | 0.5% | 82.6% |
| 13 | `والے滑雪` | U+6ED1 U+96EA | 37 | 0.5% | 83.2% |
| 14 | `स्कर्ट` | U+0938 U+094D U+0915 U+0930 U+091F | 35 | 0.5% | 83.7% |
| 15 | `बिल्یاں` | U+092C U+093F U+0932 U+094D | 34 | 0.5% | 84.2% |
| 16 | `سجاया` | U+092F U+093E | 32 | 0.5% | 84.7% |
| 17 | `बरामدا` | U+092C U+0930 U+093E U+092E | 30 | 0.4% | 85.1% |
| 18 | `چશ્مے` | U+0AB6 U+0ACD | 27 | 0.4% | 85.5% |
| 19 | `چپسٹیಕ್ಸ್` | U+0C95 U+0CCD U+0CB8 | 26 | 0.4% | 85.9% |
| 20 | `مウンド` | U+30A6 U+30F3 U+30C9 | 26 | 0.4% | 86.3% |
| 21 | `سٹروलर` | U+0932 U+0930 | 22 | 0.3% | 86.6% |
| 22 | `жіں` | U+0436 U+0456 | 20 | 0.3% | 86.9% |
| 23 | `بिल्ली` | U+093F U+0932 U+094D U+0940 | 20 | 0.3% | 87.2% |
| 24 | `شاورカーテン` | U+30AB U+30FC U+30C6 U+30F3 | 19 | 0.3% | 87.5% |
| 25 | `بोगیاں` | U+094B U+0917 | 18 | 0.3% | 87.7% |

Top 8 forms cover 80% of occurrences.

Top 37 forms cover 90% of occurrences.

Top 110 forms cover 95% of occurrences.

## Trigger words

Share of captions containing each English word whose translation is contaminated.

| EN word | captions | contaminated | rate |
|---|---|---|---|
| frisbee | 4,385 | 4,227 | 96.4% |
| owl | 62 | 47 | 75.8% |
| jeans | 167 | 50 | 29.9% |
| skirt | 167 | 35 | 21.0% |
| snowboard | 2,478 | 451 | 18.2% |
| tomato | 728 | 89 | 12.2% |
| statue | 855 | 72 | 8.4% |
| broccoli | 1,970 | 28 | 1.4% |
| ski | 8,598 | 96 | 1.1% |
| skier | 2,118 | 16 | 0.8% |
| skateboard | 7,484 | 39 | 0.5% |
| zebra | 4,962 | 20 | 0.4% |
| giraffe | 6,643 | 21 | 0.3% |
| elephant | 5,677 | 49 | 0.9% |
| umbrella | 5,482 | 50 | 0.9% |
| scissors | 939 | 3 | 0.3% |
| graffiti | 534 | 3 | 0.6% |
| teddy | 2,752 | 19 | 0.7% |
| pepperoni | 249 | 2 | 0.8% |
| stroller | 74 | 44 | 59.5% |
| chopstick | 64 | 16 | 25.0% |

## Examples (20 of 6,686)

Foreign-script characters are bracketed `⟦ ⟧`.

- EN: Woman taking a picture of someone standing behind a sculpture and a child pushing another woman towards the sculpture. 
  UR: ایک عورت مجسمے کے پیچھے کھڑے شخص کی تصویر کھینچ رہی ہے اور ایک بچہ دوسری عورت کو مجسمے کی طرف دھ⟦क⟧⟦े⟧⟦ल⟧ رہا ہے۔
  chars: U+0915 U+0947 U+0932 (Devanagari)

- EN: A lot of white birds flying around boats.
  UR: کئی سفید پرندے کشت⟦ि⟧⟦य⟧⟦ो⟧⟦ं⟧ کے ارد گرد اڑ رہے ہیں۔
  chars: U+093F U+092F U+094B U+0902 (Devanagari)

- EN: A sheep stares as several other sheep graze in a field.
  UR: ایک بھیڑ دوسرے بھیڑوں کے چرم⟦ग⟧⟦ा⟧⟦ह⟧ میں چَرتے ہوئے دیکھ رہی ہے۔
  chars: U+0917 U+093E U+0939 (Devanagari)

- EN: A man with a snowboard next to a man with a mask.
  UR: ایک آدمی س⟦н⟧⟦о⟧⟦у⟧ بورڈ کے ساتھ اور ایک آدمی ماسک کے ساتھ کھڑا ہے۔
  chars: U+043D U+043E U+0443 (Cyrillic)

- EN: A cat is sitting in a recliner chair.
  UR: ایک بلی ایک ری⟦클⟧ینر کرسی پر بیٹھی ہے۔
  chars: U+D074 (Hangul)

- EN: Black and white cats lying on desk with keyboard.
  UR: سیاہ اور سفید رنگ کی ⟦ब⟧⟦ि⟧⟦ल⟧⟦्⟧یاں کی بورڈ کے ساتھ میز پر لیٹی ہوئی ہیں۔
  chars: U+092C U+093F U+0932 U+094D (Devanagari)

- EN: A woman throwing a frisbee as a child looks on.
  UR: ایک عورت ایک بچے کے دیکھتے ہوئے فرس⟦ビ⟧⟦ー⟧ پھینک رہی ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A woman and girl in park playing with frisbee.
  UR: ایک عورت اور لڑکی پارک میں فرس⟦ビ⟧⟦ー⟧ کھیل رہی ہیں۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A woman and child playing frisbee in a grassy area.
  UR: ایک عورت اور بچہ گھاس والے علاقے میں فرس⟦ビ⟧⟦ー⟧ کھیل رہے ہیں۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A person on a field throwing a Frisbee by a kid.
  UR: ایک شخص ایک بچے کے پاس میدان میں فرس⟦ビ⟧⟦ー⟧ پھینک رہا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A woman and a little girl playing with a Frisbee in the sun on a green lawn.
  UR: ایک عورت اور ایک چھوٹی لڑکی دھوپ میں سبز گھاس کے میدان میں فرس⟦ビ⟧⟦ー⟧ کھیل رہی ہیں۔
  chars: U+30D3 U+30FC (Japanese)

- EN: An adult woman playing a game of frisbee with a little girl.
  UR: ایک بالغ خاتون ایک چھوٹی لڑکی کے ساتھ فرس⟦ビ⟧⟦ー⟧ کھیل رہی ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A young child holding a frisbee and posing in a throwing motion with a woman across from her.
  UR: ایک بچہ فرس⟦ビ⟧⟦ー⟧ پکڑے ہوئے ہے اور ایک عورت کے سامنے پھینکنے کی حرکت میں کھڑا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A child getting ready to throw a frisbee to an adult.
  UR: ایک بچہ ایک بالغ کو فرس⟦ビ⟧⟦ー⟧ پھینکنے کے لیے تیار ہو رہا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: There is a little girl throwing a frisbee with a woman
  UR: ایک چھوٹی لڑکی ایک عورت کے ساتھ فرس⟦ビ⟧⟦ー⟧ پھینک رہی ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A guy wearing a white shirt holds up a white frisbee.
  UR: ایک لڑکا سفید قمیص پہنے سفید فرس⟦ビ⟧⟦ー⟧ کو اٹھا کر رکھتا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: there is a man not wearing shoes playing frisbee
  UR: ایک آدمی جو جوتے نہیں پہن رہا، فرس⟦ビ⟧⟦ー⟧ کھیل رہا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A man holding a white frisbee on top of a field.
  UR: ایک آدمی میدان کے اوپر ایک سفید فرس⟦ビ⟧⟦ー⟧ پکڑے ہوئے ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A man with no shoes on catching a Frisbee.
  UR: ایک آدمی بغیر جوتوں کے فرس⟦ビ⟧⟦ー⟧ پکڑ رہا ہے۔
  chars: U+30D3 U+30FC (Japanese)

- EN: A woman catching a frisbee on a beach.
  UR: ایک عورت ساحل پر فرس⟦ビ⟧⟦ー⟧ پکڑ رہی ہے۔
  chars: U+30D3 U+30FC (Japanese)

---

# AFTER FIXING: gemma27b

**0 of 317,549 captions (0.000%)** are affected: 0 characters, 0 distinct.

Source: `data/translations/gemma27b_repaired.parquet` — repaired with `repairs/script_contamination_gemma27b.tsv` via `scripts/15_apply_repairs.py`.

| | captions | rate |
|---|---|---|
| before | 6,686 | 2.106% |
| after | 0 | 0.000% |
| repaired | 6,686 | — |
