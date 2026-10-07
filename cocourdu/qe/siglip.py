"""SigLIP 2 scorers: image embeddings (cached) and direct Urdu-text <-> image similarity.

SigLIP 2 is trained on multilingual WebLI, so it reads Urdu directly — unlike v1's English CLIP on back-translations.
"""
from __future__ import annotations

import numpy as np

SIGLIP2_BASE = "google/siglip2-base-patch16-224"
SIGLIP2_SO400M = "google/siglip2-so400m-patch14-384"


class SigLIP2:
    def __init__(self, model_id: str = SIGLIP2_BASE, device: str | None = None):
        import torch
        from transformers import AutoModel, AutoProcessor
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.model = AutoModel.from_pretrained(model_id).to(self.device).eval()
        self.proc = AutoProcessor.from_pretrained(model_id)
        self.model_id = model_id

    def embed_images(self, images, batch_size: int = 64) -> np.ndarray:
        import torch
        out = []
        for i in range(0, len(images), batch_size):
            px = self.proc(images=images[i:i + batch_size], return_tensors="pt")["pixel_values"].to(self.device)
            with torch.no_grad():
                f = self.model.get_image_features(pixel_values=px)
            out.append(torch.nn.functional.normalize(f, dim=-1).float().cpu().numpy())
        return np.concatenate(out)

    def embed_texts(self, texts: list[str], batch_size: int = 128) -> np.ndarray:
        import torch
        out = []
        for i in range(0, len(texts), batch_size):
            enc = self.proc(text=texts[i:i + batch_size], padding="max_length", max_length=64, truncation=True, return_tensors="pt").to(self.device)
            with torch.no_grad():
                f = self.model.get_text_features(**enc)
            out.append(torch.nn.functional.normalize(f, dim=-1).float().cpu().numpy())
        return np.concatenate(out)

    def relative_score(self, img: np.ndarray, en: np.ndarray, ur: np.ndarray, eps: float = 1e-6) -> np.ndarray:
        """v1's relative formula, but with the Urdu text embedded directly (no back-translation):
        min(1, 2.5 * max(s_ur,0) * hmean(1, s_ur / max(s_en, eps)))."""
        s_en = (img * en).sum(-1)
        s_ur = (img * ur).sum(-1)
        ratio = s_ur / np.maximum(s_en, eps)
        hm = 2 * 1 * ratio / (1 + ratio)
        return np.minimum(1.0, 2.5 * np.maximum(s_ur, 0) * hm)
