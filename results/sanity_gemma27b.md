# Sanity check: gemma27b (317,641 captions)

| check | rate (count) |
|---|---|
| empty | 0.00% (0) |
| has_untranslated_english | 0.10% (321) |
| wrong_script | 0.01% (38) |
| too_short | 0.00% (3) |
| too_long | 0.02% (71) |
| repeated_trigram | 0.31% (975) |
| has_foreign_script | 0.00% (0) |
| has_oov | 11.74% (37296) |
| len_ratio_mean | 1.21 |

Top OOV tokens (lexicon 114,598 words): زبرا (1822), رکیٹ (935), زیرافہ (867), سکیئر (828), بیسبال (798), زیبراؤں (607), سکیئرز (570), گرافٹی (530), گائےوں (516), سکیئنگ (513), سکیز (442), چراہگاہ (437), سکیوں (430), دھلوان (339), قیچی (279), بورڈرز (278), دھلاؤ (243), ماوس (229), نارنجیوں (226), مسکرارہا (226), پیپرونی (212), چھاتوں (194), رکٹ (193), والک (188), دیوال (174), قفص (173), سوند (173), زرافوں (170), رمپ (167), ہائیڈرانٹ (162), ویی (153), مسکرارہی (149), کھمبہ (146), شطرنجی (144), ٹماٹے (144), ذرافا (141), سکئی (137), بھیڑئے (131), بھرواں (128), پٹیو (127)

## Example flagged rows

- EN: A park bench siting next to a tree next to a  park.
  UR: ایک پارک کے پاس ایک درخت کے پاس ایک بینچ رکھا ہوا ہے۔
- EN: a cat sitting with shoes on a bed playing with the strings
  UR: ایک بلی بستر پر جوتوں کے ساتھ کھیل رہی ہے اور ڈوروں سے کھیل رہی ہے۔
- EN: A small dog looks out of a car window, the driver looking on.
  UR: ایک چھوٹا کتا کار کی کھڑکی سے باہر دیکھ رہا ہے، جبکہ ڈرائیور بھی دیکھ رہا ہے۔
- EN: Two three dimensional images of a woman with an umbrella.
  UR: ایک عورت کے چھتری کے ساتھ دو سہ-الابعادی (three dimensional) تصاویر ہیں۔
- EN: a bunch of donuts with different frosting and designs
  UR: مختلف ڈیزاین اور frosting کے ساتھ درجنوں ڈونٹس ہیں۔
- EN: The large bug is trapped inside the cage on the counter. 
  UR: بڑا کیڑا گ counter پر قفص کے اندر پھنس گیا ہے۔
- EN: Man on a soccer field running with soccer ball.
  UR: ایک آدمی فٹ بال کے میدان میں فٹ بال کے ساتھ دوڑ رہا ہے۔
- EN: A small cake is covered in frosting on a plate.
  UR: ایک چھوٹی کیک پلیٹ پر frosting سے ڈھکی ہوئی ہے۔
- EN: A table laden with food features salad and olives and different bowl of foods.
  UR: ایک میز پر کھانے کی چیزیں بکھی ہوئی ہیں جن میں سلاد، زیتون اور مختلف برتنوں میں کھانے کی چیزیں شامل ہیں۔
- EN: Raw cookies in a pan on the counter and baked cookies in a pan on the stove.
  UR: کاﺅنٹر پر ایک پین میں خام ککیاں اور چولھے پر ایک پین میں پکی ہوئی ککیاں ہیں۔
- EN: A bathroom with shower curtain opened and sun shining.
  UR: ایک غسل خانہ جہاں شاور کی پردہ کھلی ہوئی ہے اور دھوپ کھِلی ہوئی ہے۔
- EN: A PICTURE OF A BATHROOM WITH SLIDING SHOWER 
  UR: ایک غسل خانہ جس میں سلائیڈنگ شاور (sliding shower) ہے۔
- EN: a couple of elephants are standing in a pin
  UR: یہ ممکن نہیں ہے کہ میں اس تصویر کی وضاحت کر سکوں کیونکہ "pin" کا یہاں کیا مطلب ہے یہ واضح نہیں ہے۔ کیا آپ وضاحت کریں گے؟
- EN: A man on a skateboard, riding on a sidewalk area while another man on a skateboard rides beside him.
  UR: ایک آدمی سڑک کے کنارے سکیٹ بورڈ پر سوار ہے جبکہ دوسرا آدمی اسی طرح اس کے ساتھ سکیٹ بورڈ پر چل رہا ہے۔
- EN: One man laying on a surfboard whike another man is standing on his surfboard in the ocean.
  UR: ایک آدمی سمندر میں سرف بورڈ پر لیٹا ہوا ہے جبکہ دوسرا آدمی اپنے سرف بورڈ پر کھڑا ہے۔
