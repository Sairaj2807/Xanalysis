"""Evaluate a sentiment scorer against the manually reviewable validation set."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

LABELS = ["positive", "neutral", "negative"]


def predict_labels(scores: dict[str, np.ndarray]) -> np.ndarray:
    probs = np.stack([scores["p_positive"], scores["p_neutral"], scores["p_negative"]], axis=1)
    return np.array(LABELS)[probs.argmax(axis=1)]


def calibration_table(conf: np.ndarray, correct: np.ndarray, bins: int = 5) -> pd.DataFrame:
    """Reliability table: does higher confidence actually mean higher accuracy?"""
    edges = np.linspace(1 / 3, 1.0, bins + 1)
    b = np.clip(np.digitize(conf, edges[1:-1]), 0, bins - 1)
    rows = []
    for i in range(bins):
        m = b == i
        rows.append({"bin": f"{edges[i]:.2f}-{edges[i + 1]:.2f}", "n": int(m.sum()),
                     "mean_confidence": float(conf[m].mean()) if m.any() else np.nan,
                     "accuracy": float(correct[m].mean()) if m.any() else np.nan})
    return pd.DataFrame(rows)


def evaluate(df: pd.DataFrame, scores: dict[str, np.ndarray]) -> dict:
    pred = predict_labels(scores)
    correct = pred == df["label"].to_numpy()
    out = {
        "accuracy": float(accuracy_score(df["label"], pred)),
        "report": classification_report(df["label"], pred, labels=LABELS, output_dict=True, zero_division=0),
        "confusion": pd.DataFrame(confusion_matrix(df["label"], pred, labels=LABELS),
                                  index=[f"true_{l}" for l in LABELS], columns=[f"pred_{l}" for l in LABELS]),
        "calibration": calibration_table(scores["confidence"], correct),
        "by_category": df.assign(correct=correct).groupby("category")["correct"].agg(["mean", "size"]),
    }
    return out
