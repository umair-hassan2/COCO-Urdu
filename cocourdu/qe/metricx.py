"""MetricX-24 hybrid (QE mode when no reference). google/metricx-24-hybrid-large-v2p6 is ~1.2B (mT5-large)."""
from __future__ import annotations

METRICX_LARGE = "google/metricx-24-hybrid-large-v2p6"
METRICX_XL = "google/metricx-24-hybrid-xl-v2p6"


class MetricX24QE:
    """Lower is better (predicted MQM-style error score, 0..25). We return 25 - score so higher = better."""

    def __init__(self, model_id: str = METRICX_LARGE, device: str | None = None, batch_size: int = 16, max_len: int = 1536):
        import torch
        from transformers import AutoTokenizer, MT5ForConditionalGeneration
        self.device = device or ("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained("google/mt5-xl")
        self.model = MT5ForConditionalGeneration.from_pretrained(model_id, torch_dtype=torch.float16 if self.device != "cpu" else torch.float32).to(self.device).eval()
        self.batch_size, self.max_len = batch_size, max_len

    def _fmt(self, src: str, mt: str) -> str:
        # QE format from the MetricX-24 README: no reference segment
        return f"source: {src} candidate: {mt}"

    def score(self, src: list[str], mt: list[str]) -> list[float]:
        import torch
        out = []
        for i in range(0, len(src), self.batch_size):
            batch = [self._fmt(s, m) for s, m in zip(src[i:i + self.batch_size], mt[i:i + self.batch_size])]
            enc = self.tok(batch, max_length=self.max_len, truncation=True, padding=True, return_tensors="pt")
            # MetricX drops the trailing </s> token
            enc["input_ids"] = enc["input_ids"][:, :-1]
            enc["attention_mask"] = enc["attention_mask"][:, :-1]
            enc = {k: v.to(self.device) for k, v in enc.items()}
            with torch.no_grad():
                dec = torch.zeros((enc["input_ids"].shape[0], 1), dtype=torch.long, device=self.device)
                logits = self.model(**enc, decoder_input_ids=dec).logits[:, 0, 0]
            preds = logits.float().clamp(0, 25).cpu().tolist()
            out.extend(25.0 - p for p in preds)
        return out
