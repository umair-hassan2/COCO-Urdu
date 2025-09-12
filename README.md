# COCO-Urdu: Large-Scale Urdu Image-Caption Dataset with Multimodal Quality Estimation

This repository contains scripts and instructions to reproduce the **COCO-Urdu** dataset, a large-scale Urdu image-caption dataset derived from MS COCO. The dataset is accompanied by a hybrid multimodal quality estimation (QE) pipeline for translation, validation, and iterative refinement.

- **Research Paper:** https://www.arxiv.org/abs/2509.09014
- **Dataset:** [COCO-Urdu on Hugging Face](https://huggingface.co/datasets/umairhassan02/urdu-translated-coco-captions-subset)

---

## Overview

Urdu, spoken by over 250 million people, remains critically under-served in multimodal and vision-language research. COCO-Urdu addresses this gap by providing 59K images and 319K high-quality Urdu captions. Captions were generated via zero-shot translation using SeamlessM4T v2, validated with a hybrid QE pipeline combining COMET-Kiwi, CLIP-based visual grounding, and BERTScore with back-translation, and low-scoring captions were iteratively refined using open-source LLMs.

This repository contains scripts for preprocessing, translation, quality estimation, refinement, benchmarking, and dataset assembly to reproduce the full pipeline.

---

## Reproduction Steps

Follow these steps to reproduce the COCO-Urdu dataset:

1. **Dataset Splitting**  
   Load the MS COCO dataset and preprocess it using the `dataset_split` script to generate the desired training and validation splits.

2. **Translation with Hybrid QE**  
   Generate Urdu translations and validate them with the hybrid multimodal quality estimation pipeline using the `translation_pipeline` script.  
   **Requirements:** GPU (≥32GB recommended, e.g., A100 or RTX 5090). The pipeline supports distributed execution across multiple GPUs for faster processing.

3. **Reference Translation Generation**  
   Produce reference translations for evaluation using the `nllb_reference_generation` script. GPU execution is recommended.

4. **Iterative Refinement of Low-Scoring Captions**  
   Refine captions identified as low-quality by the hybrid QE pipeline using the `targeted_refinements` script.

5. **Benchmarking**  
   Evaluate captions before and after refinement with the `benchmarking` script. This handles all metrics and ensures consistency across iterations.

6. **Final Dataset Assembly**  
   Collate all processed translations and generate the final version of COCO-Urdu using the `generate_final_version` script.

**Note:** Depending on hardware and compute resources, full reproduction may take up to ~40 hours.

---

**Consider citing the work if you find this helpful**

```bibtex
@inproceedings{Hassan2025COCOUrduAL,
  title={COCO-Urdu: A Large-Scale Urdu Image-Caption Dataset with Multimodal Quality Estimation},
  author={Umair Hassan},
  year={2025},
  url={https://api.semanticscholar.org/CorpusID:281252320}
}

