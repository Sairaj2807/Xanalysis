"""Small sequence / shared-head networks for multi-horizon forecasting (PyTorch, CPU).

Kept deliberately small: ~1k training rows cannot support large networks. Preprocessing (median imputation,
standardisation) is fitted on the training rows only. Early stopping uses a chronological validation tail.
Architectures: `shared_mlp` (shared trunk + horizon heads = architecture C), `gru`, `lstm`, `tcn`, `transformer`.
"""
from __future__ import annotations

import numpy as np

KINDS = ("shared_mlp", "gru", "lstm", "tcn", "transformer")


def _build(kind: str, n_feat: int, n_out: int, seq_len: int, hidden: int = 32, dropout: float = 0.2):
    import torch
    from torch import nn

    class Heads(nn.Module):
        def __init__(self, d):
            super().__init__()
            self.heads = nn.ModuleList([nn.Linear(d, 1) for _ in range(n_out)])   # one head per horizon

        def forward(self, z):
            return torch.cat([h(z) for h in self.heads], dim=1)

    class SharedMLP(nn.Module):
        def __init__(self):
            super().__init__()
            self.trunk = nn.Sequential(nn.Linear(n_feat, hidden), nn.ReLU(), nn.Dropout(dropout),
                                       nn.Linear(hidden, hidden), nn.ReLU())
            self.out = Heads(hidden)

        def forward(self, x):                       # x: (B, L, F) -> last step
            return self.out(self.trunk(x[:, -1, :]))

    class Rec(nn.Module):
        def __init__(self, cell):
            super().__init__()
            self.rnn = cell(n_feat, hidden, batch_first=True)
            self.drop = nn.Dropout(dropout)
            self.out = Heads(hidden)

        def forward(self, x):
            o, _ = self.rnn(x)
            return self.out(self.drop(o[:, -1, :]))

    class TCN(nn.Module):
        def __init__(self):
            super().__init__()
            self.pad = nn.ConstantPad1d((2, 0), 0.0)          # causal padding
            self.c1 = nn.Conv1d(n_feat, hidden, 3)
            self.c2 = nn.Conv1d(hidden, hidden, 3, dilation=2)
            self.pad2 = nn.ConstantPad1d((4, 0), 0.0)
            self.act, self.drop = nn.ReLU(), nn.Dropout(dropout)
            self.out = Heads(hidden)

        def forward(self, x):
            z = x.transpose(1, 2)
            z = self.act(self.c1(self.pad(z)))
            z = self.act(self.c2(self.pad2(z)))
            return self.out(self.drop(z[:, :, -1]))

    class Transformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.inp = nn.Linear(n_feat, hidden)
            self.pos = nn.Parameter(torch.zeros(1, seq_len, hidden))
            layer = nn.TransformerEncoderLayer(hidden, 4, hidden * 2, dropout, batch_first=True)
            self.enc = nn.TransformerEncoder(layer, 1)
            self.out = Heads(hidden)

        def forward(self, x):
            z = self.enc(self.inp(x) + self.pos)
            return self.out(z[:, -1, :])

    if kind == "shared_mlp":
        return SharedMLP()
    if kind == "gru":
        return Rec(nn.GRU)
    if kind == "lstm":
        return Rec(nn.LSTM)
    if kind == "tcn":
        return TCN()
    if kind == "transformer":
        return Transformer()
    raise ValueError(kind)


def make_windows(X: np.ndarray, idx: np.ndarray, seq_len: int) -> np.ndarray:
    """Windows ending at each row in idx using only rows <= that row (past data). Early rows are left-padded
    by repeating the first available row."""
    out = np.empty((len(idx), seq_len, X.shape[1]), dtype=np.float32)
    for k, t in enumerate(idx):
        lo = t - seq_len + 1
        w = X[max(lo, 0): t + 1]
        if lo < 0:
            w = np.vstack([np.repeat(X[:1], -lo, axis=0), w])
        out[k] = w
    return out


def fit_predict(kind: str, X_all: np.ndarray, Y_all: np.ndarray, train_idx: np.ndarray, test_idx: np.ndarray,
                max_h: int, seq_len: int = 10, epochs: int = 80, lr: float = 2e-3, wd: float = 1e-3,
                patience: int = 10, seed: int = 0) -> np.ndarray:
    """Fit on train_idx rows (all horizons non-NaN), predict test_idx. Returns (len(test_idx), n_horizons)."""
    import torch

    torch.manual_seed(seed)
    np.random.seed(seed)
    torch.set_num_threads(4)
    ok = train_idx[~np.isnan(Y_all[train_idx]).any(axis=1)]
    med = np.nanmedian(X_all[ok], axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    Xf = np.where(np.isnan(X_all), med, X_all)
    mu, sd = Xf[ok].mean(0), Xf[ok].std(0)
    sd = np.where(sd < 1e-12, 1.0, sd)
    Xs = ((Xf - mu) / sd).astype(np.float32)
    ymu, ysd = Y_all[ok].mean(0), Y_all[ok].std(0)
    ysd = np.where(ysd < 1e-12, 1.0, ysd)

    n_val = max(int(0.2 * len(ok)), 20)
    fit_idx = ok[:-n_val]
    fit_idx = fit_idx[fit_idx + max_h < ok[-n_val]]          # purge overlap with the validation tail
    val_idx = ok[-n_val:]
    Wt = torch.tensor(make_windows(Xs, fit_idx, seq_len))
    Yt = torch.tensor(((Y_all[fit_idx] - ymu) / ysd).astype(np.float32))
    Wv = torch.tensor(make_windows(Xs, val_idx, seq_len))
    Yv = torch.tensor(((Y_all[val_idx] - ymu) / ysd).astype(np.float32))
    net = _build(kind, X_all.shape[1], Y_all.shape[1], seq_len)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
    best, best_state, bad = np.inf, None, 0
    for _ in range(epochs):
        net.train()
        perm = torch.randperm(len(Wt))
        for s in range(0, len(Wt), 64):
            b = perm[s:s + 64]
            opt.zero_grad()
            loss = torch.mean((net(Wt[b]) - Yt[b]) ** 2)
            loss.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            v = float(torch.mean((net(Wv) - Yv) ** 2))
        if v < best - 1e-6:
            best, bad = v, 0
            best_state = {k: t.clone() for k, t in net.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    net.load_state_dict(best_state)
    net.eval()
    with torch.no_grad():
        pred = net(torch.tensor(make_windows(Xs, test_idx, seq_len))).numpy()
    return pred * ysd + ymu
