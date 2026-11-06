"""Documentation consistency checks. Exit code 1 on errors. Warnings do not fail.

Checks: required files, required sections, broken relative links, task-register integrity (IDs, categories,
statuses, dependencies), NEXT_ACTIONS task references, stale CURRENT_CONTEXT.
"""
from __future__ import annotations

import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

REQUIRED_FILES = """README.md PROJECT_MASTER_CONTEXT.md PROJECT_CHARTER.md PROJECT_STATUS.md DEVELOPMENT_ROADMAP.md MASTER_TASK_REGISTER.md
architecture/SYSTEM_ARCHITECTURE.md architecture/DATA_FLOW.md architecture/DATABASE_ARCHITECTURE.md architecture/MODULE_ARCHITECTURE.md
architecture/API_INTEGRATION.md architecture/DEPLOYMENT_ARCHITECTURE.md
research/RESEARCH_OBJECTIVE.md research/RESEARCH_HYPOTHESES.md research/DATA_METHODOLOGY.md research/SENTIMENT_METHODOLOGY.md
research/FEATURE_ENGINEERING.md research/FORECASTING_METHODOLOGY.md research/VALIDATION_METHODOLOGY.md research/STATISTICAL_TESTING.md
research/RESEARCH_FINDINGS.md
data/DATA_INVENTORY.md data/DATA_DICTIONARY.md data/DATA_LINEAGE.md data/DATA_QUALITY_REPORT.md data/INGESTION_STATUS.md data/DATA_LIMITATIONS.md
models/MODEL_REGISTRY.md models/MODEL_EXPERIMENTS.md models/MODEL_PERFORMANCE.md models/WALK_FORWARD_RESULTS.md
models/FEATURE_IMPORTANCE.md models/MODEL_LIMITATIONS.md
engineering/IMPLEMENTATION_TRACKER.md engineering/CODEBASE_MAP.md engineering/TESTING_STATUS.md engineering/TECHNICAL_DEBT.md
engineering/BUG_REGISTER.md engineering/SECURITY.md
decisions/ARCHITECTURE_DECISIONS.md decisions/RESEARCH_DECISIONS.md decisions/DECISION_LOG.md
history/CHANGELOG.md history/DEVELOPMENT_LOG.md history/EXPERIMENT_LOG.md history/INCIDENT_LOG.md history/RELEASE_HISTORY.md
operations/INSTALLATION.md operations/CONFIGURATION.md operations/EXECUTION_GUIDE.md operations/PIPELINE_OPERATIONS.md
operations/TROUBLESHOOTING.md operations/BACKUP_AND_RECOVERY.md
ai_context/AGENTS.md ai_context/CURRENT_CONTEXT.md ai_context/SESSION_HANDOFF.md ai_context/CODING_STANDARDS.md
ai_context/RESEARCH_RULES.md ai_context/NEXT_ACTIONS.md""".split()

REQUIRED_SECTIONS = {
    "ai_context/SESSION_HANDOFF.md": ["Commands executed", "Test results", "Known errors", "Next action"],
    "ai_context/CURRENT_CONTEXT.md": ["Next five priorities", "Immediate blockers"],
    "PROJECT_MASTER_CONTEXT.md": ["Critical constraints", "Instructions for AI agents", "Current implementation status"],
    "decisions/DECISION_LOG.md": ["Revisit Conditions"],
}
CATEGORIES = {"ARCH", "DATA", "ING", "NLP", "FEAT", "DB", "ML", "VAL", "STAT", "VIS", "REP", "MON", "OPS", "SEC", "TEST"}
STATUSES = {"NOT_STARTED", "IN_PROGRESS", "IMPLEMENTED", "TESTED", "VERIFIED", "BLOCKED", "DEPRECATED"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
ID_RE = re.compile(r"\b([A-Z]{2,4})-(\d{3})\b")


def parse_register() -> dict[str, dict]:
    tasks: dict[str, dict] = {}
    txt = (DOCS / "MASTER_TASK_REGISTER.md").read_text(encoding="utf-8")
    for line in txt.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"[A-Z]{2,4}-\d{3}", cells[0]):
            tasks[cells[0]] = {"title": cells[1], "priority": cells[2], "status": cells[3], "deps": cells[4]}
    return tasks


def main() -> int:
    errors, warns = [], []
    for f in REQUIRED_FILES:
        if not (DOCS / f).exists():
            errors.append(f"missing required file docs/{f}")
    for f, secs in REQUIRED_SECTIONS.items():
        p = DOCS / f
        if p.exists():
            t = p.read_text(encoding="utf-8").lower()
            errors += [f"docs/{f}: missing section '{s}'" for s in secs if s.lower() not in t]
    for p in DOCS.rglob("*.md"):
        for m in LINK_RE.finditer(p.read_text(encoding="utf-8")):
            tgt = m.group(1)
            if tgt.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = (p.parent / tgt.split("#")[0]).resolve()
            if not path.exists():
                errors.append(f"broken link in {p.relative_to(ROOT).as_posix()}: {tgt}")
    # task register
    if (DOCS / "MASTER_TASK_REGISTER.md").exists():
        tasks = parse_register()
        if not tasks:
            errors.append("no tasks parsed from MASTER_TASK_REGISTER.md")
        for tid, t in tasks.items():
            if tid.split("-")[0] not in CATEGORIES:
                errors.append(f"{tid}: unknown category")
            if t["status"] not in STATUSES:
                errors.append(f"{tid}: invalid status {t['status']!r}")
            for d in ID_RE.findall(t["deps"]):
                dep = f"{d[0]}-{d[1]}"
                if dep not in tasks:
                    errors.append(f"{tid}: dependency {dep} not in register")
        na = DOCS / "ai_context" / "NEXT_ACTIONS.md"
        if na.exists():
            for a, b in ID_RE.findall(na.read_text(encoding="utf-8")):
                if f"{a}-{b}" not in tasks and a in CATEGORIES:
                    errors.append(f"NEXT_ACTIONS references unknown task {a}-{b}")
    # staleness
    cc = DOCS / "ai_context" / "CURRENT_CONTEXT.md"
    if cc.exists():
        m = re.search(r"Last updated:\s*(\d{4}-\d{2}-\d{2})", cc.read_text(encoding="utf-8"))
        if not m:
            warns.append("CURRENT_CONTEXT.md has no 'Last updated: YYYY-MM-DD'")
        else:
            ctx_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            src = [p for p in ROOT.rglob("*.py") if not any(x in {".venv", "data", "docs", "artifacts", ".git"} for x in p.relative_to(ROOT).parts)]
            newest = max((date.fromtimestamp(p.stat().st_mtime) for p in src), default=ctx_date)
            if newest > ctx_date:
                warns.append(f"CURRENT_CONTEXT.md ({ctx_date}) older than newest source change ({newest})")
    for w in warns:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"documentation validation: {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
