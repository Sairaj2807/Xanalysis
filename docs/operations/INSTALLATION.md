# Installation

Windows 11, Python 3.12 (installed with `winget install Python.Python.3.12 --scope user`).

```
py -3.12 -m venv .venv            # or %LOCALAPPDATA%\Programs\Python\Python312\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu126
```
`requirements.txt` pins `torch==2.14.1+cu126`, which needs the PyTorch cu126 index; for CPU-only use install a plain `torch` instead. This exact clean-machine install has **not been tested** (SEC-002). GPU used: Quadro P2200 (`torch.cuda.is_available()` → True).

First FinBERT use downloads `ProsusAI/finbert` (~440 MB) to the HuggingFace cache; Windows symlink warning is harmless (`HF_HUB_DISABLE_SYMLINKS_WARNING=1` silences it).

Verify: `.venv\Scripts\python.exe -m pytest -q` (expect 51 passed).

Additional packages used since the first install (already in `requirements.txt`): `py3langid`, `alembic`, `shap`, `catboost`, `lightgbm`, `xgboost`. FinTwitBERT and the other comparison models download from the HuggingFace Hub on first use.
