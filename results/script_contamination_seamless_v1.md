# Cross-script contamination: seamless_v1

Source: `captions_v1.ur_seamless` — 317,921 captions.
A caption is flagged if it contains a character outside the Arabic/Urdu blocks, Latin,
digits and shared punctuation (`cocourdu.urdu_text.URDU_OK`).

**36 of 317,921 captions (0.011%)** are affected: 41 characters, 10 distinct.

## By writing system

| script | captions | % of corpus | characters |
|---|---|---|---|
| Other | 36 | 0.011% | 41 |

## Shape

| shape | occurrences | share |
|---|---|---|
| Urdu word with an embedded foreign fragment | 1 | 2.6% |
| token entirely in another script | 37 | 97.4% |

## Word-forms

21 distinct forms, 38 occurrences.

| # | form | code points | count | share | cumulative |
|---|---|---|---|---|---|
| 1 | `$` | U+0024 | 8 | 21.1% | 21.1% |
| 2 | `#` | U+0023 | 6 | 15.8% | 36.8% |
| 3 | `@` | U+0040 | 3 | 7.9% | 44.7% |
| 4 | `=` | U+003D | 2 | 5.3% | 50.0% |
| 5 | `<` | U+003C | 2 | 5.3% | 55.3% |
| 6 | `3⁄4` | U+2044 | 2 | 5.3% | 60.5% |
| 7 | `+9` | U+002B | 1 | 2.6% | 63.2% |
| 8 | `#213` | U+0023 | 1 | 2.6% | 65.8% |
| 9 | `'#480` | U+0023 | 1 | 2.6% | 68.4% |
| 10 | `2+` | U+002B | 1 | 2.6% | 71.1% |
| 11 | `1⁄2` | U+2044 | 1 | 2.6% | 73.7% |
| 12 | `C++"` | U+002B | 1 | 2.6% | 76.3% |
| 13 | `<br` | U+003C | 1 | 2.6% | 78.9% |
| 14 | `>` | U+003E | 1 | 2.6% | 81.6% |
| 15 | `$1` | U+0024 | 1 | 2.6% | 84.2% |
| 16 | `Zit<<` | U+003C | 1 | 2.6% | 86.8% |
| 17 | `&` | U+0026 | 1 | 2.6% | 89.5% |
| 18 | `a=` | U+003D | 1 | 2.6% | 92.1% |
| 19 | `n=میٹر` | U+003D | 1 | 2.6% | 94.7% |
| 20 | `"@me"` | U+0040 | 1 | 2.6% | 97.4% |
| 21 | `**` | U+002A | 1 | 2.6% | 100.0% |

Top 14 forms cover 80% of occurrences.

Top 18 forms cover 90% of occurrences.

Top 20 forms cover 95% of occurrences.

## Trigger words

Share of captions containing each English word whose translation is contaminated.

| EN word | captions | contaminated | rate |
|---|---|---|---|
| frisbee | 4,389 | 1 | 0.0% |
| owl | 62 | 0 | 0.0% |
| jeans | 167 | 0 | 0.0% |
| skirt | 170 | 0 | 0.0% |
| snowboard | 2,481 | 0 | 0.0% |
| tomato | 728 | 0 | 0.0% |
| statue | 856 | 0 | 0.0% |
| broccoli | 1,971 | 0 | 0.0% |
| ski | 8,604 | 0 | 0.0% |
| skier | 2,119 | 0 | 0.0% |
| skateboard | 7,489 | 0 | 0.0% |
| zebra | 4,965 | 0 | 0.0% |
| giraffe | 6,649 | 1 | 0.0% |
| elephant | 5,681 | 0 | 0.0% |
| umbrella | 5,490 | 0 | 0.0% |
| scissors | 939 | 0 | 0.0% |
| graffiti | 534 | 0 | 0.0% |
| teddy | 2,760 | 0 | 0.0% |
| pepperoni | 249 | 0 | 0.0% |
| stroller | 74 | 0 | 0.0% |
| chopstick | 64 | 0 | 0.0% |

## Examples (20 of 36)

Foreign-script characters are bracketed `⟦ ⟧`.

- EN: A baby playing with a radio whle sitting in bed.+9
  UR: ایک بچہ ریڈیو کے ساتھ کھیل رہا ہے جبکہ بستر میں بیٹھا ہے۔ ⟦+⟧9
  chars: U+002B (Other)

- EN: #213 leans into a very tight turn in this race
  UR: ⟦#⟧213 اس ریس میں ایک بہت ہی تنگ موڑ میں جھک جاتا ہے
  chars: U+0023 (Other)

- EN: Player #11 swings the bat hard at the ball.
  UR: کھلاڑی ⟦#⟧ 11 نے گیند پر سخت بیٹ سوئنگ کی.
  chars: U+0023 (Other)

- EN: @ couple of kids walking in the snow
  UR: ⟦@⟧ دو بچے برف میں چل رہے ہیں
  chars: U+0040 (Other)

- EN: A close up of a fruit stand with a sign propped up reading '#480 el kilo'.
  UR: ایک پھل اسٹینڈ کا ایک قریبی اپ جس میں ایک نشان ہے جس پر لکھا ہے '⟦#⟧480 el kilo'۔
  chars: U+0023 (Other)

- EN: A b=very large robust giraffe eating leaves from trees
  UR: ایک b ⟦=⟧ بہت بڑا مضبوط زرافہ درختوں سے پتے کھا رہا ہے
  chars: U+003D (Other)

- EN: a dog is curled up in the corner of a 2+ seater sofa
  UR: ایک کتا ایک 2⟦+⟧ سیٹر صوفے کے کونے میں گھوم رہا ہے
  chars: U+002B (Other)

- EN: 1 1/2 loaded hot dogs and veggie side
  UR: 1 1⟦⁄⟧2 لوڈ شدہ ہاٹ ڈاگ اور سبزیوں کی طرف سے
  chars: U+2044 (Other)

- EN: A vending machine with hot corn dogs for $2.00.
  UR: ایک وینڈنگ مشین گرم مکئی کے کتے کے ساتھ ⟦$⟧ 2.00 کے لئے.
  chars: U+0024 (Other)

- EN: I vending machine containing precooked corn dogs for $2 each.
  UR: میں نے ایک وینڈنگ مشین میں پہلے سے پکا ہوا مکئی کا کتا ⟦$⟧ 2 ہر ایک کے لئے شامل کیا.
  chars: U+0024 (Other)

- EN: A man on a motorcycle with # 20 on the handle bars rounding a curve while others look on.
  UR: ایک موٹر سائیکل پر ایک آدمی کے ساتھ ⟦#⟧ 20 ہینڈل بار پر ایک منحنی خطوط کو گول کرنے کے دوران دوسروں کو دیکھ کر .
  chars: U+0023 (Other)

- EN: A derby car #30 is seen cutting a corner with its right door ajar.
  UR: ڈربی کار ⟦#⟧ 30 کو اس کے دائیں دروازے کے ساتھ ایک کونے کو کاٹتے ہوئے دیکھا جاتا ہے۔
  chars: U+0023 (Other)

- EN: A motor cycle riding on the street with # 6 on the fork.
  UR: ایک موٹر سائیکل سڑک پر سوار ہے جس میں فورک پر ⟦#⟧ 6 ہے.
  chars: U+0023 (Other)

- EN: Picture of a laptop with old dos based screen along with a book titled "Let us C++"
  UR: ایک لیپ ٹاپ کی تصویر جس میں پرانی ڈوس پر مبنی اسکرین کے ساتھ ساتھ ایک کتاب ہے جس کا عنوان ہے "Let us C⟦+⟧⟦+⟧"
  chars: U+002B (Other)

- EN: 2 pieces of bread with bananas on top.... 
  UR: 2 ٹکڑے روٹی کے ساتھ سب سے اوپر کیلے کے ساتھ... ⟦<⟧br ⟦>⟧
  chars: U+003C U+003E (Other)

- EN: A pink, cat-designed microwave is on sale for $69.99 and was originally $91.99. 
  UR: ایک گلابی مائکروویو کی قیمت ⟦$⟧ 69.99 ہے اور اصل میں ⟦$⟧ 91.99 تھی.
  chars: U+0024 (Other)

- EN: # birds fly through the sky one behind the other
  UR: ⟦#⟧ پرندے آسمان کے ذریعے اڑتے ہیں  ایک دوسرے کے پیچھے ایک دوسرے کے پیچھے
  chars: U+0023 (Other)

- EN: Triple Decker bus advertising $1 fares parked by rocks..
  UR: ٹرپل ڈیکر بس اشتہار ⟦$⟧1 ٹیرف پتھروں کی طرف سے پارک کیا..
  chars: U+0024 (Other)

- EN: Foreign poster "Er Zit Muziek in deze poster" for JCDecaux.
  UR: غیر ملکی پوسٹر "Er Zit⟦<⟧⟦<⟧ Muziek in deze poster" for JCDecaux کے لئے۔
  chars: U+003C (Other)

- EN: a stop sign that has m yspace wrote on it
  UR: ایک اسٹاپ سائن جس پر m ⟦<⟧ y space لکھا ہوا ہے۔
  chars: U+003C (Other)
