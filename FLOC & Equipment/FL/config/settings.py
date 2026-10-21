"""
Central configuration for the FL (Functional Location / Equipment) validation agent.

Every value is resolved in this order:
  1. process environment variable
  2. the project-root .env file (AgentV2/.env), then a .env in the working directory
  3. the default below

To run the same agent for another site, change the SITE block in .env (FL_SITE_NAME, FL_SITE_CODE,
FL_PLANT_CODE, ...). File names, the ECA table, the ECA folder, output names, the asset cache and
the prompt wording are derived from it; any of them can still be overridden by its own key.

The .env file is only read here; os.environ is not modified, so the Claude / Langfuse
loading in llm.llm_model (including --env-file) is unaffected.
Secrets (FOUNDRY_*, LANGFUSE_*, FL_DB_*) never get a default in code.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# AgentV2/FL/config/settings.py -> AgentV2
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in values:
            values[key] = value
    return values


_DOTENV: dict[str, str] = {}
for _path in (PROJECT_ROOT / ".env", Path(".env")):
    for _key, _value in _read_dotenv(_path).items():
        _DOTENV.setdefault(_key, _value)


def env_str(key: str, default: str = "") -> str:
    return os.getenv(key) or _DOTENV.get(key) or default


def env_int(key: str, default: int) -> int:
    return int(env_str(key, str(default)))


def env_float(key: str, default: float) -> float:
    return float(env_str(key, str(default)))


def require(key: str) -> str:
    """Value that must be set in .env (connection details, secrets)."""
    value = env_str(key)
    if not value:
        raise ValueError(f"Missing {key}. Set it in {PROJECT_ROOT / '.env'} (see FL/.env.example).")
    return value


# ------------------------------------------------------------------ site
SITE_NAME = env_str("FL_SITE_NAME", "Bokor")                 # used in file names and prompts
SITE_CODE = env_str("FL_SITE_CODE", SITE_NAME.upper())       # top node of the FLOC hierarchy (Inventory 3)
SITE_SLUG = re.sub(r"[^a-z0-9]+", "_", SITE_NAME.lower()).strip("_")
PLANT_CODE = env_str("FL_PLANT_CODE", "M014")
COMPANY_NAME = env_str("FL_COMPANY_NAME", "PETRONAS")

# ------------------------------------------------------------------ input (relative to the working directory = AgentV2 root)
INPUT_SOURCE = env_str("FL_INPUT_SOURCE", "cache")           # cache = asset master from the DB cache; excel = input files below
DATASET = env_str("FL_DATASET", "both")                      # both | fl | equipment | auto
INPUT_FILE = env_str("FL_INPUT_FILE", f"FL_{SITE_NAME}.xlsx")
FL_INPUT_FILE = env_str("FL_FL_INPUT_FILE")                  # Excel FL sheet for --dataset both (falls back to INPUT_FILE)
EQ_INPUT_FILE = env_str("FL_EQ_INPUT_FILE")                  # Excel Equipment sheet for --dataset both (falls back to INPUT_FILE)
_input_sheet = env_str("FL_INPUT_SHEET", "0")
INPUT_SHEET: int | str = int(_input_sheet) if _input_sheet.isdigit() else _input_sheet

# ------------------------------------------------------------------ output
OUTPUT_FILE = env_str("FL_OUTPUT_FILE", f"outputs/FL_{SITE_NAME}_validated.xlsx")
FL_OUTPUT_FILE = env_str("FL_FL_OUTPUT_FILE", f"outputs/FL/FL_{SITE_NAME}_validated.xlsx")
EQ_OUTPUT_FILE = env_str("FL_EQ_OUTPUT_FILE", f"outputs/Eq/Equipment_{SITE_NAME}_validated.xlsx")

# ------------------------------------------------------------------ reference folders and caches
STANDARDS_DIR = env_str("FL_STANDARDS_DIR", "STANDARDS")
ECA_DIR = env_str("FL_ECA_DIR", f"{SITE_CODE} ECA REPORT")
CACHE_DIR = env_str("FL_CACHE_DIR", "cache_agent")
ASSET_CACHE_FILE = env_str("FL_ASSET_CACHE_FILE", f"cache/{SITE_SLUG}/asset_master_cache.pkl")
STANDARDS_KB_FILE = env_str("FL_STANDARDS_KB_FILE", f"{CACHE_DIR}/standards_kb.json")
ENV_FILE = env_str("FL_ENV_FILE", ".env")

# Local Excel fallbacks for the reference tables (relative to PROJECT_ROOT).
PROCESS_SUBPROCESS_FALLBACK = PROJECT_ROOT / env_str("FL_PROCESS_SUBPROCESS_FALLBACK", "STANDARDS/process_subprocess_extracted.xlsx")
CATALOG_PROFILE_FALLBACK = PROJECT_ROOT / env_str("FL_CATALOG_PROFILE_FALLBACK", "STANDARDS/Catalog_Profile_COMPLETE_Extraction.xlsx")
ECA_REPORT_FALLBACK = PROJECT_ROOT / env_str("FL_ECA_REPORT_FALLBACK", f"{ECA_DIR}/ECA_Extract.xlsx")
ECA_EXTRACT_DIR = PROJECT_ROOT / env_str("FL_ECA_EXTRACT_DIR", ECA_DIR)

# ------------------------------------------------------------------ PostgreSQL (connection details are required, see require())
ECA_TABLE = env_str("FL_ECA_TABLE", f"{SITE_SLUG}_eca_report")   # site ECA criticality table in the public schema
ECA_TABLE_FQN = f"public.{ECA_TABLE}"
DB_PORT = env_int("FL_DB_PORT", 5432)
DB_SSLMODE = env_str("FL_DB_SSLMODE", "require")
DB_CONNECT_TIMEOUT = env_int("FL_DB_CONNECT_TIMEOUT", 30)
# FL_DB_HOST, FL_DB_NAME, FL_DB_USER, FL_DB_TENANT_ID and FL_DB_TOKEN_SCOPE are read with require()
# in data/db_connection.py, only when the database is actually used.

# ------------------------------------------------------------------ Claude (Azure AI Foundry) client limits
LLM_MAX_TOKENS = env_int("FL_LLM_MAX_TOKENS", 16000)
LLM_MAX_RETRIES = env_int("FL_LLM_MAX_RETRIES", 4)
LLM_TIMEOUT_SECONDS = env_float("FL_LLM_TIMEOUT_SECONDS", 600.0)

# ------------------------------------------------------------------ Langfuse trace labels
AGENT_NAME = env_str("FL_AGENT_NAME", "Agent A")
TRACE_TAG = env_str("FL_TRACE_TAG", f"{SITE_SLUG}-validation")
