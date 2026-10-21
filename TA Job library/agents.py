"""CleaningAgent -- picks the right master equipment row for one worklist row and
suggests cleaned EquipmentNo / FuncLoc / SubLoc1 with evidence.

Runs on Claude Sonnet 4.6 via Azure AI Foundry (Anthropic SDK with Foundry base_url).
"""

import json
import os
import re
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

FOUNDRY_BASE_URL = "https://tridiagonal-ai-eastus2-resource.services.ai.azure.com/anthropic"
MODEL = "claude-sonnet-4-6"
MAX_RETRIES = 3
RETRY_DELAY = 5

client = Anthropic(
    api_key=os.getenv("AZURE_AI_KEY") or os.getenv("ANTHROPIC_API_KEY"),
    base_url=FOUNDRY_BASE_URL,
)

# Master prefix (text before first '-' in TechnicalIdentNo) -> worklist SubLoc1 alias
PREFIX_TO_SUBLOC1 = {
    "BOCP": "BOCPP-A",
    "BOKA": "BOK-A",
    "BOPA": "BOP-A",
    "BOVA": "BOV-A",
    "BODA": "BODP-A",
    "BODB": "BODP-B",
    "BODC": "BODP-C",
    "BODD": "BODP-D",
    "BODE": "BODP-E",
    "BODF": "BODP-F",
}


def call_llm(system, user_payload, max_tokens=800):
    """One LLM call, returns parsed JSON. Retries on transient errors."""
    user_text = json.dumps(user_payload, ensure_ascii=False, default=str)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=MODEL, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user_text}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {"_error": "no json in response", "_raw": text[:400]}
            return json.loads(match.group(0))
        except Exception as e:
            print(f"    LLM attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    return {"_error": "all retries failed"}


# ============================================================
# CleaningAgent
# ============================================================

def _cleaning_system():
    reverse = "\n".join(f"  {k} -> {v}" for k, v in PREFIX_TO_SUBLOC1.items())
    return f"""You are mapping ONE row of a Petronas Bokor SAP maintenance worklist to its correct equipment in the SAP equipment master.

CONTEXT -- how the two data sources look:

Worklist row (human-entered, often messy):
  - EquipmentNo: a free-form field. Sometimes a clean SAP tag ("060SDV-002"), sometimes a
    slash-separated multi-tag ("JB-7702/JB-7771"), sometimes a tag buried in descriptive text
    ("M-3 P-0110B", "ML-3 BO 605 (WHCP)", "SI Line Replacement - 50-SI-68011-13411X"), and
    sometimes almost pure description.
  - SubLoc1: a short platform alias (BOCPP-A, BODP-F, BOK-A, ...). Usually correct but
    occasionally mislabeled (~1% of rows).
  - Discipline, EqptType, Job Description, FuncLoc: additional context.

Master row (clean, authoritative SAP data):
  - TechnicalIdentNo: structured as "<PREFIX>-<TAIL>" where PREFIX is a 4-letter platform code
    (BOCP, BOKA, BOPA, BOVA, BODA, BODB, BODC, BODD, BODE, BODF) and TAIL is the real SAP tag.
    Examples: "BOKA-UPS7700A", "BODD-P0110B", "BODF-50-SI-68011-13411X", "BOCP-WHCP-ML3-BO605".
  - EquipmentNo: a short SAP code (often numeric, e.g. "11061761", or "PIPE-C-LP-0258").
  - FunctionalLocation: hierarchical, e.g. "BOKA.PWR.UPS.UPS7700A".
  - ObjectDescription, FunctLocDescrip, CatalogProfile: human-readable descriptors.

The candidates below (up to 100) are ALL the master equipment under the platform implied by
this row's SubLoc1 -- that is the ONLY narrowing. There is no catalog_profile / Discipline
pre-filter, so the right equipment is in here but you must find it yourself. The exact-match
step has already run and failed, so the worklist tag and master TID are NOT byte-identical --
you need to RECOGNIZE the match from naming patterns, descriptions, and FunctionalLocation.

YOUR TASK:
Pick the single master row that IS the equipment this worklist row refers to. Use your judgment:
  - The real SAP tag inside the worklist EquipmentNo may be surrounded by module numbers,
    action words, descriptive text, or punctuation. Find it.
  - A match is strong when a candidate's TechnicalIdentNo TAIL (the part after the 4-letter
    prefix) appears inside the worklist EquipmentNo, or vice versa, after you ignore
    whitespace, dashes, and parentheses.
  - When no string overlap works, use the Job Description to pick the most likely candidate
    semantically against the candidate's ObjectDescription and FunctLocDescrip.
  - Only return nulls (confidence Low) when no candidate is plausible under ANY of these angles.

Then compute Suggested SubLoc1:
  Take the PREFIX from the picked TechnicalIdentNo (text before the FIRST '-') and map it:
{reverse}
  If this differs from the row's original SubLoc1, OVERRIDE it and explain in subloc1_evidence.

Also decide whether a human should double-check this row (needs_review):
  Set needs_review = true WHENEVER you want a human to verify your pick, EVEN IF your confidence
  is High. Examples:
    - Two candidates were almost equally plausible and you picked the better one by a small margin.
    - You overrode SubLoc1 (platform disagreement).
    - The worklist EquipmentNo was mostly free-text and you had to infer the tag.
    - Multi-tag worklist input where you had to pick one of several possible equipment.
  Set needs_review = false only when your match is unambiguous and nothing is unusual about it.

Rules:
  - Pick only from the candidates provided; never invent an EquipmentNo.
  - For each of the two output fields (EquipmentNo, SubLoc1), return confidence (High / Medium /
    Low) and a one-sentence evidence describing what signal convinced you.

Respond in strict JSON only:
{{
  "suggested_equipment_no":   "<master EquipmentNo | null>",
  "equipment_no_confidence":  "High|Medium|Low",
  "equipment_no_evidence":    "<one sentence>",
  "suggested_subloc1":        "<worklist alias, corrected if needed>",
  "subloc1_confidence":       "High|Medium|Low",
  "subloc1_evidence":         "<one sentence>",
  "needs_review":             true|false
}}"""


def cleaning_agent(row, candidates_df):
    payload = {
        "worklist_row": {
            "EquipmentNo":     str(row.get("EquipmentNo", "")),
            "FuncLoc":         str(row.get("FuncLoc", "")),
            "Discipline":      str(row.get("Discipline", "")),
            "EqptType":        str(row.get("EqptType", "")),
            "SubLoc1":         str(row.get("SubLoc1", "")),
            "Job Description": str(row.get("Job Description", "")),
        },
        "candidates": candidates_df[[
            "EquipmentNo", "TechnicalIdentNo", "FunctionalLocation",
            "ObjectDescription", "FunctLocDescrip", "CatalogProfile",
        ]].to_dict(orient="records"),
    }
    return call_llm(_cleaning_system(), payload, max_tokens=900)
