"""Shared utilities: config loading, path management, and numeric helpers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()  # load .env if present (no-op in production with IAM roles)

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    raw: Path
    processed: Path
    synthetic: Path


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and return config.yaml, merging environment variable overrides."""
    path = Path(config_path) if config_path else ROOT_DIR / "config" / "config.yaml"
    with path.open("r", encoding="utf-8") as fh:
        cfg: dict[str, Any] = yaml.safe_load(fh)

    # Overlay AWS resource names from environment variables when set.
    aws = cfg.setdefault("aws", {})
    _env_overrides = {
        "bucket_name": "AWS_BUCKET_NAME",
        "glue_job_name": "AWS_GLUE_JOB_NAME",
        "lambda_function_name": "AWS_LAMBDA_FUNCTION_NAME",
        "eventbridge_rule": "AWS_EVENTBRIDGE_RULE",
        "athena_database": "AWS_ATHENA_DATABASE",
    }
    for cfg_key, env_var in _env_overrides.items():
        env_val = os.getenv(env_var)
        if env_val:
            aws[cfg_key] = env_val

    return cfg


def build_paths(config: dict[str, Any]) -> Paths:
    data = config["data"]
    return Paths(
        raw=ROOT_DIR / data["raw_path"],
        processed=ROOT_DIR / data["processed_path"],
        synthetic=ROOT_DIR / data["synthetic_path"],
    )


def ensure_parent(path: Path) -> None:
    """Create parent directories for *path* if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def safe_pct_change(new: float, old: float) -> float:
    """Return percentage change from *old* to *new*; 0.0 if old is zero."""
    return ((new - old) / old * 100) if old != 0 else 0.0
