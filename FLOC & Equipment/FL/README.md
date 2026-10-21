# FL agent – site Functional Location / Equipment validation

The agent validates and completes the Functional Location (FL) sheet and the Equipment sheet of a site's asset master.
Python rules run first. In `hybrid` mode, only the rows the rules are unsure about go to Claude (Azure AI Foundry).
The code has no site-specific values. The site, its files and the database connection are all set in `AgentV2/.env`.

## Run (from the AgentV2 root)

```powershell
python FL/main.py                          # hybrid, FL + Equipment sheets
python FL/main.py --mode deterministic     # rules only, no LLM
python -m FL --help                        # all options (every default comes from .env)
python -m FL.data.db_connection --refresh  # rebuild the asset master cache from PostgreSQL only
```

## Run for another site

1. In `AgentV2/.env`, change the site block:
   ```
   FL_SITE_NAME=Kinabalu
   FL_SITE_CODE=KINABALU
   FL_PLANT_CODE=M0xx
   ```
   The following settings then follow from the site automatically:

   | Setting | Value for Kinabalu |
   |---|---|
   | ECA table | `public.kinabalu_eca_report` |
   | ECA folder | `KINABALU ECA REPORT` |
   | Asset cache | `cache/kinabalu/asset_master_cache.pkl` |
   | Outputs | `outputs/FL/FL_Kinabalu_validated.xlsx`, `outputs/Eq/Equipment_Kinabalu_validated.xlsx` |
   | Langfuse trace tag | `kinabalu-validation` |
   | Prompt wording | uses Kinabalu |

   If a name doesn't follow this pattern, override it with its own key (for example `FL_ECA_TABLE`).
2. Choose where the input comes from:
   - `FL_INPUT_SOURCE=cache` (default) reads both sheets from the asset master database cache.
   - `FL_INPUT_SOURCE=excel` reads your own files:
     - With `FL_DATASET=both`, set `FL_FL_INPUT_FILE` and `FL_EQ_INPUT_FILE`.
     - With one sheet (`FL_DATASET=fl` or `equipment`), set `FL_INPUT_FILE`.
     - Use `FL_INPUT_SHEET` when the data isn't on the first sheet.
3. If the site's data is in another database, change the `FL_DB_*` keys.
4. Run `python FL/main.py`. The first run for a site builds its asset cache from the database. Later runs reuse the cache.

The input files must use the SAP column headers ("Functional Location", "Equipment", "Technical IdentNo.", ...).

## Pipeline steps

| # | Step | Code |
|---|------|------|
| 1 | Asset master: load FL + Equipment from the cache, or from PostgreSQL when there is no cache | `data/db_connection.py`, `data/database_evidence.py` |
| 2 | Hierarchy index: join FL + Equipment and attach the ECA equipment links | `core/hierarchy_rules.py` |
| 3 | Standards KB: Claude extracts rules from `STANDARDS/*.md` (hybrid mode, when missing) | `llm/standards_kb.py` |
| 4 | Input sheet: FL / Equipment sheet from the cache or from Excel | `pipeline/run_validation.py` |
| 5 | Rule validators: Functional Location, completion, ABC, Catalog Profile, Technical IdentNo. | `validators/` |
| 6 | Claude review: the hybrid reviewer (`llm`) or the tool-use agent (`agent`) gets the unclear rows only | `llm/llm_reviewer.py`, `llm/llm_agent.py` |
| 7 | Output: styled Excel workbook with the validated sheet and run summary | `pipeline/run_validation.py` |

## Structure

```
FL/
├── main.py / __main__.py      entry points
├── .env.example               every setting the agent reads
├── config/settings.py         all configuration: .env -> defaults (site values are derived)
├── core/                      common.py, hierarchy_rules.py, sources.py
├── data/
│   ├── db_connection.py       PostgreSQL asset master (nodes / edges) -> pickle cache
│   └── database_evidence.py   reference tables (process codes, catalog profiles, site ECA table)
├── validators/                deterministic column validators
├── llm/                       Claude client, prompts, reviewer, agent + tools, standards KB
└── pipeline/run_validation.py CLI and orchestration (steps above)
```

## Coding conventions

- Imports inside the package are relative (`from ..core.common import ...`). Always run the agent from the AgentV2 root as a package.
- Never put a site name, file name, table name, URL, host or key in code. Add it to `config/settings.py` (read from `.env`) and to `.env.example`.
- Required connection values use `settings.require("KEY")`. If one is missing, the run stops with a clear error.
- Constants are UPPER_CASE at module top. Each module starts with a docstring. Public functions have type hints.
- Use `logging` for messages, not `print`. The only `print` is the final "Created: <file>" line.
