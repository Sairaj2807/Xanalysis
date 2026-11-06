"""Financial sentiment via a HuggingFace sequence-classification model (default: ProsusAI/finbert).

Outputs the full probability distribution per post. S_i = P(pos) - P(neg) in [-1, 1].
"""
from __future__ import annotations

import logging
from typing import Sequence

import numpy as np

log = logging.getLogger(__name__)

DEFAULT_MODEL = "ProsusAI/finbert"


def model_tag(model_name: str) -> str:
    """'' for the default model (keeps existing file names); '_<slug>' otherwise."""
    import re
    return "" if model_name == DEFAULT_MODEL else "_" + re.sub(r"[^A-Za-z0-9]+", "-", model_name.split("/")[-1]).lower()

OUT_COLS = ["p_positive", "p_neutral", "p_negative", "sentiment_score", "confidence"]


def scores_from_probs(p_pos: np.ndarray, p_neu: np.ndarray, p_neg: np.ndarray) -> dict[str, np.ndarray]:
    probs = np.stack([p_pos, p_neu, p_neg], axis=1)
    return {
        "p_positive": p_pos, "p_neutral": p_neu, "p_negative": p_neg,
        "sentiment_score": p_pos - p_neg,
        "confidence": probs.max(axis=1),  # max class probability; NOT a calibrated correctness probability
    }


_ALIASES = {"positive": "positive", "bullish": "positive", "pos": "positive", "label_2": None,
            "neutral": "neutral", "neu": "neutral",
            "negative": "negative", "bearish": "negative", "neg": "negative"}


def resolve_label_indices(id2label: dict) -> tuple[int, int, int]:
    """Map a checkpoint's labels (positive/bullish, neutral, negative/bearish; case-insensitive) to indices."""
    found: dict[str, int] = {}
    for k, v in id2label.items():
        canon = _ALIASES.get(str(v).lower())
        if canon:
            found[canon] = int(k)
    if set(found) != {"positive", "neutral", "negative"}:
        raise ValueError(f"cannot map labels {id2label}; add aliases to _ALIASES")
    return found["positive"], found["neutral"], found["negative"]


class FinBertAnalyzer:
    def __init__(self, model_name: str = DEFAULT_MODEL, device: str | None = None,
                 batch_size: int = 128, max_length: int = 96, fp16: bool = True):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.batch_size, self.max_length = batch_size, max_length
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name).to(self.device).eval()
        if fp16 and self.device == "cuda":
            self.model.half()
        # map label names -> output index, robust to checkpoint ordering
        self.idx = resolve_label_indices(self.model.config.id2label)
        log.info("loaded %s on %s labels=%s", model_name, self.device, self.model.config.id2label)

    def score(self, texts: Sequence[str]) -> dict[str, np.ndarray]:
        torch = self.torch
        n = len(texts)
        # length-sort to minimise padding, restore order afterwards
        order = np.argsort([len(t) for t in texts])
        probs = np.zeros((n, 3), dtype=np.float32)
        with torch.inference_mode():
            for s in range(0, n, self.batch_size):
                ids = order[s:s + self.batch_size]
                enc = self.tok([texts[i] for i in ids], padding=True, truncation=True,
                               max_length=self.max_length, return_tensors="pt").to(self.device)
                p = torch.softmax(self.model(**enc).logits.float(), dim=-1).cpu().numpy()
                probs[ids] = p[:, list(self.idx)]
        return scores_from_probs(probs[:, 0], probs[:, 1], probs[:, 2])
