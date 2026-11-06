# Security

- Secrets: `APIFY_API_TOKEN`, `APIFY_ACTOR_ID`, `TAVILY_API_KEY`, `DATABASE_URL` via environment / `.env` only. `.env` is git-ignored; [.env.example](../../.env.example) holds blank placeholders. No credential has been created or used so far.
- Verified: regex secrets scan of source, docs, configs and requirements (2026-11-05) found nothing; `.env` does not exist; `.gitignore` excludes `.env`, `artifacts/`, `data/raw`, logs.
- Downloaded model weights come from the HuggingFace Hub (`ProsusAI/finbert`, safetensors) — trust is that of the hub.
- Input validation: asset config validated by pydantic; API items validated before use. DB connections are local SQLite; no remote DB.
- Data privacy: tweets contain usernames and public text; keep `data/` out of version control (git-ignored).
- Dependency pinning: [requirements.txt](../../requirements.txt) (pip freeze). No vulnerability scan performed.
