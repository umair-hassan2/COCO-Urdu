# Datasheet for COCO-Urdu v2 (Gebru et al. format) — DRAFT, fill before release

## Motivation
- **Purpose:** Urdu image–caption data for captioning/retrieval and a human-rated benchmark for translation QE in Urdu.
- **Creator / funding:** Umair Hassan, independent; no funding. Annotators: volunteers (named in acknowledgements with consent).

## Composition
- 63,549 COCO-2017 images (58,549 train / 5,000 val), stratified 50% subset preserving category co-occurrence; 317,921 English captions; Urdu captions from: `seamless` (SeamlessM4T v2 Large), `<llm>` (TBD), `qe_selected`.
- Human study: ~1,000 captions × systems × ≥2 raters, adequacy/fluency 0–100 + error tags.
- No personal data beyond what COCO images contain; images are referenced by id/URL, not redistributed.

## Collection process
- Translation: see `cocourdu/prompts.py`, `scripts/03_*`. QE: `scripts/06_score_qe.py`. Human study protocol: `rating_tool/guidelines.md`.
- Known issues: MT-derived; Western-centric imagery; author is one of the raters.

## Preprocessing / uses / distribution / maintenance
- TBD at release: HF dataset card, Croissant metadata, versioning (v1 kept immutable), contact for corrections.
