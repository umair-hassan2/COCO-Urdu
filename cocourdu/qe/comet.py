"""COMET-Kiwi (v1 metric) and xCOMET-QE. Both are gated on HF: run `huggingface-cli login` once."""
from __future__ import annotations

COMET_KIWI = "Unbabel/wmt22-cometkiwi-da"
XCOMET_XL = "Unbabel/XCOMET-XL"      # 3.5B; needs ~16 GB in fp16 — Mac >=32 GB or Colab L4
XCOMET_XXL = "Unbabel/XCOMET-XXL"    # 10.7B; Colab A100 only


class CometQE:
    def __init__(self, model_id: str = COMET_KIWI, device: str | None = None, batch_size: int = 32):
        from comet import download_model, load_from_checkpoint
        import torch
        self.model = load_from_checkpoint(download_model(model_id))
        self.batch_size = batch_size
        self.gpus = 1 if (device or "").startswith("cuda") or torch.cuda.is_available() else 0
        self.accelerator = "mps" if (device == "mps" or (device is None and torch.backends.mps.is_available())) else None

    def score(self, src: list[str], mt: list[str]) -> list[float]:
        data = [{"src": s, "mt": m} for s, m in zip(src, mt)]
        kw = {"batch_size": self.batch_size, "gpus": self.gpus, "progress_bar": True}
        if self.accelerator:
            kw.update(accelerator="mps", devices=1, gpus=0)
        return list(self.model.predict(data, **kw).scores)
