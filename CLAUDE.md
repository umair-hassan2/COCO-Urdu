# COCO-Urdu — project instructions

## Working agreements
- **Do not run background agents, background security reviews, or subagent fan-out in this repo.**
  They burn tokens on a research repo whose code is read by one person. If something genuinely needs
  a second pass, say so in one line and let me decide.
- Report findings inline in the reply; no separate review artifacts unless I ask.

## Repo facts worth not re-deriving
- Branch `v2` is the active line of work; `master` holds the v1 paper code.
- Input datasets are hardcoded in `cocourdu/data.py` (`umairhassan02/...`) and are **read-only**.
  `--hf-repo` on `scripts/03_translate_gemma_vllm.py` is a **separate private write target** for
  resumable chunk checkpoints — never point it at a published dataset.
- `data/` and `results/` are gitignored; nothing in them is committed.
- Pipeline order (Mac and Colab interleave): `colab/README.md`.
