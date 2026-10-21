"""
===============================================================================
P&ID Major Equipment Extractor Script (High-Speed Parallel Vision AI)
===============================================================================

This script extracts all physical, major process & mechanical equipment from 
P&ID PDF/image files using a vLLM-hosted vision LLM (OpenAI-compatible API).

Features:
- Single-pass high-accuracy extraction (full drawing analysis + equipment table correlation).
- Parallel processing (multi-threading with configurable workers, default: 10).
- Automatic standby/twin tag splitting (e.g. P-101A/B -> P-101A, P-101B).
- Rigorous post-extraction filtering (drops valves, instruments, electrical gear, line numbers).
- Output to Excel (.xlsx) with clean, structured columns.
- Checkpoint/resume support: a per-output-dir "_checkpoint.json" log tracks each file's
  status. Re-running the same command skips files already marked "success" and
  automatically retries anything that previously errored, so large folder-hierarchy runs
  can be safely interrupted (Ctrl+C, crash, rate limit) and resumed without redoing work.
  One bad/corrupt file can no longer abort an entire --input_dir batch.

Configuration (environment or .env):
  # Google Gemini:
  gemini_key=your_api_key_here
  GEMINI_MODEL=gemini-3.1-pro-preview (optional, default: gemini-3.1-pro-preview)

  # vLLM:
  VLLM_BASE_URL=http://172.16.0.14:8000/v1
  VLLM_API_KEY=dummy
  VLLM_MODEL=Qwen/Qwen3.6-35B-A3B-FP8

  # AWS Bedrock:
  BEDROCK_MODEL_ARN=arn:aws:bedrock:...
  AWS_REGION=us-east-1

Output Excel Columns:
  1. pdf name              (e.g., sample_drawing.pdf)
  2. pg number             (e.g., Page 1)
  3. pnid drawing number   (e.g., 05-BOCPP-A-B-1141-1-00)
  4. Equipment name        (e.g., 05-K-1101A, P-101A, V-1116)
  5. Equipment Description (e.g., 1st Stage Suction Scrubber)
  6. Equipment Status      (EXISTING | FUTURE | BY_OTHERS | DELETED | NOT_IN_SCOPE)

Usage Examples:
  # Gemini extraction (auto-detects gemini_key in .env):
  python Titan.py --pdf "drawing.pdf" --output_dir "output"

  # Explicit provider selection:
  python Titan.py --pdf "drawing.pdf" --provider gemini --model "gemini-3.7-flash"

Requirements:
  pip install google-generativeai openai pillow pymupdf pandas openpyxl python-dotenv
===============================================================================
"""

import os
import io
import re
import base64
import json
import time
import argparse
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from PIL import Image
from dotenv import load_dotenv

# Try importing json_repair for auto-fixing malformed LLM JSONs
try:
    import json_repair
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False

# Try importing pdf2image for PDF to PNG conversion (fallback)
try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False

# Try importing PyMuPDF (preferred, pure-wheel fast PDF renderer)
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Try importing boto3 (AWS SDK for Bedrock runtime)
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

# Try importing Google Generative AI (Gemini) SDK
try:
    import google.generativeai as genai
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

# Try importing the OpenAI SDK
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import sys

# -----------------------------------------------------------------------------
# Setup Real-Time Unbuffered Logging
# -----------------------------------------------------------------------------
class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

handler = FlushStreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
logger = logging.getLogger("pnid_equipment_extractor")
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.addHandler(handler)
logger.propagate = False

# Load environment variables (.env file)
load_dotenv()
if not os.getenv("VLLM_BASE_URL"):
    alt_env = Path(__file__).parent / "deployment" / "pnid" / ".env"
    if alt_env.exists():
        load_dotenv(dotenv_path=alt_env)

# =============================================================================
# PROMPT DEFINITIONS (Single-Pass Comprehensive Analysis + Multi-Pass Support)
# =============================================================================

PROMPT_SINGLE_PASS_EXPERT = """You are a Lead Process & Mechanical P&ID Engineer performing an exact, high-precision extraction of the MAJOR PHYSICAL EQUIPMENT present on this P&ID drawing.

CRITICAL INSTRUCTION: Return ONLY a valid JSON object. Do NOT include conversational text, reasoning, or markdown outside the JSON.

======================================================================
1. DRAWING IDENTIFICATION (TITLE BLOCK)
======================================================================
- Look at the bottom-right Title Block or drawing header.
- Read and extract the official Drawing Number from the drawing sheet.
- Do NOT copy placeholder strings. If unreadable, write "UNKNOWN".
- If this sheet is purely a Legend / Symbol Key / Lead Sheet / General Notes / Index (no actual process equipment diagram), set "sheet_is_legend_or_index": true and "equipments": [].

======================================================================
2. WHAT QUALIFIES AS MAJOR PHYSICAL EQUIPMENT (DETECT & EXTRACT)
======================================================================
Extract physical equipment items that have an actual CAD graphic / equipment symbol drawn on THIS page:
- VESSELS / DRUMS / SEPARATORS: Horizontal & vertical vessels, knockout drums, flash drums, scrubbers, coalescers, surge vessels (e.g. V-6450, V-200, V-300, V-1116, D-101).
- REACTORS / FURNACES / HEATERS: Catalytic reactors, fired heaters, boilers, incinerators, flare stacks (e.g. R-0101, R-101, H-0710, H-101).
- TANKS / TOWERS / COLUMNS: Atmospheric storage tanks, distillation/absorption columns, contactors, stripper towers (e.g. T-6550A/B, T-6570A/B, TK-101, C-101).
- PUMPS: Centrifugal, booster, dosing, reciprocating, submersible, sump pumps (e.g. P-101A/B, P-4210, 05-P-1102).
- COMPRESSORS / BLOWERS / FANS: Gas compressors, air compressors, booster blowers, turbo-expanders (e.g. K-101, 05-K-1101A, C-201, B-501).
- HEAT EXCHANGERS / COOLERS: Shell & tube exchangers, plate coolers, aerial fin-fan coolers, reboilers, condensers (e.g. E-301, HE-102, AC-201).
- PIG TRAPS / SCRAPERS: Pig launchers, pig receivers, scraper barrels (e.g. L-510, L-520, L-100, L-110, PL-101, PR-101, M-900).
- PACKAGED UNITS / SKIDS: Tagged packages, injection skids, metering skids (e.g. PK-101, SK-201, Y-6450, S-100).
- WELLHEADS / CHRISTMAS TREES: ONLY if the physical Christmas tree valve-assembly symbol is drawn on THIS sheet (e.g. BO-101, WH-101).

======================================================================
3. CRITICAL RULES TO AVOID FALSE POSITIVES (STRICT EXCLUSIONS)
======================================================================
- NEVER EXTRACT OFF-PAGE CONNECTORS OR PROCESS LINE ROUTING LABELS:
  * In P&ID drawings, piping lines at sheet borders have arrows/boxes with reference text like:
    "10\"-PG-121-01A10 GASLIFT TO WELLHEAD BO-123 | SHT 01"
    "TO WELLHEAD BO-124"
    "FROM SEPARATOR V-101 (DWG 05-BODP-...)"
    "TO FLARE HEADER"
    "OVERFLOW TO SUMP TANK"
  * NEVER extract any tag that appears inside an off-page connector arrow, boundary flag, or line routing description! These refer to equipment on OTHER drawings, NOT equipment on this page.
- DO NOT EXTRACT VALVES:
  * Exclude all manual valves, check valves (NRV), control valves (FCV, PCV, LCV, TCV), shutdown valves (XV, SDV, BDV, ESDV), safety valves (PSV, PZV, TSV), motor valves (MOV), and restriction orifices (RO).
- DO NOT EXTRACT INSTRUMENTS:
  * Exclude all instrument bubble circles & transmitters (PT, PIT, TT, TIT, LT, LIT, FT, FIT, PI, TI, LI, FI, AT, PDT, PIC, TIC, LIC, FIC, ZS, ESD tags).
- DO NOT EXTRACT PIPING & LINES:
  * Exclude pipe line size/spec numbers (e.g. 42-P-1500-1CS2P1, 6\"-STM-2002-B2B).
- DO NOT EXTRACT ELECTRICAL / PANELS:
  * Exclude junction boxes (JB), MCCs, PLC cabinets, control panels.

======================================================================
4. HOW TO FIND EVERY REAL EQUIPMENT (AVOID FALSE NEGATIVES)
======================================================================
- INSPECT INSIDE AND NEAR EQUIPMENT GRAPHICS:
  * Equipment tags are often written directly INSIDE the body silhouette of the vessel/tank/drum (e.g., "V-6450" inside a horizontal capsule, "R-0101" inside a reactor shape) or directly below/above the symbol. Look closely across all 4 quadrants!
- CROSS-REFERENCE THE EQUIPMENT DATA TABLE:
  * Check the Equipment Design Summary Table (typically located along the top, bottom, or side margin of the drawing).
  * Use the full official service description from the Equipment Table (e.g. "1st Stage Suction Scrubber", "Production Separator", "Wellhead BO-101", "Closed Drain Vessel").
- STANDBY / TWIN SPLITTING:
  * If a tag is written as twin/standby (e.g. "T-6550A/B", "P-101A/B", "05-K-1101A/B"), list each unit as a separate entry ("T-6550A" and "T-6550B").

======================================================================
OUTPUT JSON SCHEMA
======================================================================
Return ONLY valid JSON matching this exact structure:
{
  "pnid_drawing_number": "<exact drawing number from title block>",
  "sheet_is_legend_or_index": false,
  "equipments": [
    {
      "equipment_name": "<exact tag e.g. V-6450, R-0101, P-101A>",
      "equipment_description": "<full equipment description/service e.g. Closed Drain Vessel>",
      "status": "EXISTING"
    }
  ]
}
"""

PROMPT_PASS_1_DISCOVERY = PROMPT_SINGLE_PASS_EXPERT

PROMPT_PASS_2_AUDIT = """You are a Lead QA/QC P&ID Audit Specialist reviewing and refining the extracted equipment list against the P&ID drawing.

### PREVIOUS EXTRACTION (PASS 1):
{pass1_json}

### YOUR AUDIT INSTRUCTIONS:
1. PURGE OFF-PAGE REFERENCES & LINE DESTINATIONS: Delete any tag that only appears in off-page connector flags, border arrows, or line destination annotations (e.g., 'TO WELLHEAD BO-xxx', 'FROM V-xxx'). Keep ONLY items whose physical equipment symbol is drawn on this page.
2. PURGE VALVES & INSTRUMENTS: Remove any valves (HV, XV, SDV, BDV, PSV, RO), instruments (PT, TT, LT, FT, PI, TI, AT), electrical panels/JBs, pipe lines, or drawing numbers.
3. FIND MISSED EQUIPMENT: Check inside vessel symbols (e.g. horizontal/vertical drums, reactors like R-0101, vessels like V-6450) and cross-reference the Equipment Design Table.
4. SPLIT COMBINED TAGS: Split twin tags like "P-101A/B" into "P-101A" and "P-101B".
5. VERIFY DRAWING NUMBER: Confirm the exact `pnid_drawing_number` from the title block.

### OUTPUT FORMAT (Valid JSON only, no markdown explanations):
{{
  "pnid_drawing_number": "<verified drawing number or UNKNOWN>",
  "sheet_is_legend_or_index": false,
  "equipments": [
    {{
      "equipment_name": "<exact tag>",
      "equipment_description": "<full service description>",
      "status": "EXISTING"
    }}
  ]
}}
"""

PROMPT_PASS_3_CONSENSUS = """You are a Principal Engineering Consultant delivering the final verified major equipment register for this P&ID drawing.

### PASS 1 (DISCOVERY):
{pass1_json}

### PASS 2 (AUDIT):
{pass2_json}

### FINAL CONSENSUS INSTRUCTIONS:
1. STRICT PHYSICAL SYMBOL VERIFICATION: Ensure every item in the final list corresponds to a real physical equipment symbol on this drawing. Drop all off-page connector references, valves, instruments, line labels, and hallucinations.
2. RECONCILE & MERGE: Combine valid items confirmed in Pass 1 and Pass 2.
3. DISCRETE TAGS & COMPLETE DESCRIPTIONS: Ensure every item is individually split (e.g. A/B pairs) and has its full professional description from the Equipment Design Table.
4. FINAL DRAWING NUMBER: Lock in the accurate `pnid_drawing_number`.

### OUTPUT FORMAT (Valid JSON only, no markdown explanations):
{{
  "pnid_drawing_number": "<final drawing number or UNKNOWN>",
  "sheet_is_legend_or_index": false,
  "equipments": [
    {{
      "equipment_name": "<exact tag>",
      "equipment_description": "<full service description>",
      "status": "EXISTING"
    }}
  ]
}}
"""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Strips reasoning blocks (<think>...</think>), markdown code fences, and parses raw string into a Python dict.
    Uses json_repair and regex heuristics for automatic recovery from missing delimiters or syntax errors.
    """
    if not raw_text:
        return {}
    
    text = raw_text.strip()
    
    # Strip DeepSeek / Qwen reasoning <think> ... </think> blocks
    text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()
    
    # Strategy 1: json_repair automatic recovery on raw text
    if HAS_JSON_REPAIR:
        try:
            parsed = json_repair.repair_json(text, return_objects=True)
            if isinstance(parsed, dict) and ("equipments" in parsed or "pnid_drawing_number" in parsed):
                return parsed
        except Exception:
            pass

    # Strategy 2: Extract content between ```json and ``` or ``` and ```
    code_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    for block in code_blocks:
        block = block.strip()
        start = block.find("{")
        end = block.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = block[start:end+1]
            try:
                return json.loads(candidate)
            except Exception:
                if HAS_JSON_REPAIR:
                    try:
                        parsed = json_repair.repair_json(candidate, return_objects=True)
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass
                candidate_fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
                try:
                    return json.loads(candidate_fixed)
                except Exception:
                    pass

    # Strategy 3: Find outermost '{' and '}' in the cleaned text
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end+1]
        try:
            return json.loads(candidate)
        except Exception:
            if HAS_JSON_REPAIR:
                try:
                    parsed = json_repair.repair_json(candidate, return_objects=True)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
            candidate_fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate_fixed)
            except Exception as exc:
                logger.warning(f"Failed to parse standard JSON: {exc}. Attempting heuristic extraction...")

    # Strategy 4: Direct regex recovery for equipment items
    equipments = []
    matches = re.findall(r'\{\s*"equipment_name"\s*:\s*"([^"]+)"\s*,\s*"equipment_description"\s*:\s*"([^"]*)"', text)
    for name, desc in matches:
        equipments.append({
            "equipment_name": name.strip(),
            "equipment_description": desc.strip(),
            "status": "EXISTING"
        })
    if equipments:
        dwg_match = re.search(r'"pnid_drawing_number"\s*:\s*"([^"]+)"', text)
        dwg_num = dwg_match.group(1) if dwg_match else "UNKNOWN"
        return {
            "pnid_drawing_number": dwg_num,
            "sheet_is_legend_or_index": False,
            "equipments": equipments
        }
                
    return {}


# -----------------------------------------------------------------------------
# Post-extraction guard: drop anything that is clearly not tagged equipment
# -----------------------------------------------------------------------------
_BAD_NAMES = {
    "TAG", "TAG_1", "TAG_2", "N/A", "NA", "-", "EQUIPMENT", "VESSEL",
    "DESCRIPTION_1", "DESCRIPTION_2", "VERIFIED_DRAWING_NUMBER",
    "FINAL_DRAWING_NUMBER", "EXACT_DRAWING_NUMBER",
}
# Class prefixes that mean valve / instrument / instrument-loop / control-gear
_BAD_CLASSES = {
    # valves
    "HV", "HCV", "FCV", "FV", "PCV", "PV", "LCV", "LV", "TCV", "TV", "XV", "XCV",
    "SDV", "MOV", "BDV", "EBV", "ADV", "DLV", "SV", "PSV", "PVSV", "TSV", "PZV",
    "NRV", "BSV", "RO", "FO", "CV", "SB",
    # instruments / loops
    "PT", "PIT", "PIC", "PI", "PG", "PSH", "PSL", "PSHH", "PSLL",
    "TT", "TIT", "TIC", "TI", "TG", "TW", "TSH", "TSL",
    "LT", "LIT", "LIC", "LI", "LG", "LS", "LSH", "LSL", "LSHH", "LSLL", "LSU",
    "FT", "FIT", "FIC", "FI", "FE", "FQ", "FQI", "FG", "FSL",
    "AT", "AIT", "AI", "AE", "AIC",
    "ZS", "ZSH", "ZSL", "ZT", "ZI",
    "HS", "XA", "XS", "XL", "UA", "UY", "US", "UV",
    "PDT", "PDIT", "PDI", "PDIC", "PDG", "PDSH", "PDSL",
    # control / electrical hardware
    "LCP", "LCB", "JB", "MCC", "SIS", "PLC", "DCS", "UPS", "RIO", "WHCP", "PDG",
}
_BAD_PREFIXES = ("05-BODP", "05-BOCPP", "BODP", "BODA", "BOCPP", "DWG", "SHT", "SHEET", "PG-", "CI-")
_DRAWING_PATTERNS = [
    re.compile(r"^(?:05-)?BOD[PA]-", re.IGNORECASE),
    re.compile(r"^B-\d{4}$", re.IGNORECASE),  # Drawing sheet references like B-1024, B-1021
    re.compile(r"^BOD[PA]\d*$", re.IGNORECASE),
    re.compile(r"^BOCPP\d*$", re.IGNORECASE),
    re.compile(r"^DWG", re.IGNORECASE),
    re.compile(r"^SHT", re.IGNORECASE),
]
_MANY_DIGITS = re.compile(r"\d{6,}")           # line / pipe-spec numbers
_TOK_SPLIT = re.compile(r"[\s./\-]+")
_CLASS_TOK = re.compile(r"^(\d{0,4})([A-Z]{1,5})(\d{0,4})$")


def is_real_equipment(name: str, pnid_number: str = "") -> bool:
    """True only if `name` looks like a genuine tagged equipment identifier."""
    n = (name or "").strip()
    if not n or n.upper() in _BAD_NAMES:
        return False
    if pnid_number and n.upper() == str(pnid_number).strip().upper():
        return False
    if len(n) > 24:
        return False
    if not (re.search(r"[A-Za-z]", n) and re.search(r"\d", n)):
        return False                      # must contain both a letter and a digit
    if _MANY_DIGITS.search(n):
        return False                      # line number / pipe-spec, not a tag
    
    # Exclude drawing sheet references and drawing number fragments (e.g. B-1024, BODP01, DWG-101)
    for pat in _DRAWING_PATTERNS:
        if pat.search(n):
            return False

    for tok in _TOK_SPLIT.split(n.upper()):
        m = _CLASS_TOK.match(tok)
        if m and m.group(2) in _BAD_CLASSES:
            return False                  # a valve / instrument / control-gear token
    return True


def split_standby_tags(tag: str) -> List[str]:
    """
    Splits combined/standby tags like 'P-101A/B', '05-K-1101 A/B', 'V-101A,B' into discrete tags:
    ['P-101A', 'P-101B'].
    """
    t = (tag or "").strip()
    if not t:
        return []

    match = re.search(r"^(.*?)([A-Za-z])(?:\s*[/,&\-]\s*([A-Za-z]))+(.*)$", t)
    if match:
        prefix = match.group(1).rstrip()
        suffix = match.group(4).lstrip()
        sub_part = t[len(match.group(1)):len(t)-len(suffix) if suffix else len(t)]
        letters = re.findall(r"[A-Za-z]", sub_part)
        if len(letters) > 1 and all(len(l) == 1 for l in letters):
            return [f"{prefix}{l}{suffix}".strip() for l in letters]

    return [t]


def _pdf_to_pil_images_pymupdf(pdf_path: str, dpi: int) -> List[Image.Image]:
    """Render a PDF to PIL Images using PyMuPDF (no external binary required)."""
    images: List[Image.Image] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
    return images


def pdf_to_pil_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    """
    Converts a PDF file into a list of PIL Images (one per page).
    Prefers PyMuPDF; falls back to pdf2image/Poppler if needed.
    """
    if not HAS_PYMUPDF and not HAS_PDF2IMAGE:
        raise ImportError(
            "A PDF renderer is required. Install one of: pip install pymupdf (or) pip install pdf2image + Poppler"
        )

    try:
        if HAS_PYMUPDF:
            return _pdf_to_pil_images_pymupdf(pdf_path, dpi)
        return convert_from_path(pdf_path, dpi=dpi)
    except Exception as exc:
        logger.warning(f"PDF conversion at {dpi} DPI failed for {pdf_path}: {exc}")
        if dpi > 150:
            logger.info("Retrying conversion at 150 DPI...")
            if HAS_PYMUPDF:
                return _pdf_to_pil_images_pymupdf(pdf_path, 150)
            return convert_from_path(pdf_path, dpi=150)
        raise exc


# =============================================================================
# VISION EXTRACTOR CLASS
# =============================================================================

class PNIDEquipmentExtractor:
    """
    Extractor class using Google Gemini Vision, vLLM OpenAI-compatible Vision AI,
    or AWS Bedrock Vision AI (via ARN) to perform single-pass or multi-pass equipment extraction from P&ID diagrams.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: str = "auto",
        aws_region: Optional[str] = None,
    ):
        gemini_api_key = api_key or os.getenv("gemini_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        # Determine default model and provider auto-detection
        if provider == "auto":
            if model_name:
                if (
                    model_name.startswith("arn:aws:bedrock") 
                    or "anthropic.claude" in model_name 
                    or "amazon.nova" in model_name
                    or "meta.llama" in model_name
                ):
                    self.provider = "bedrock"
                elif "gemini" in model_name.lower():
                    self.provider = "gemini"
                else:
                    self.provider = "vllm"
            elif os.getenv("BEDROCK_MODEL_ARN"):
                self.provider = "bedrock"
            elif gemini_api_key and not os.getenv("VLLM_BASE_URL"):
                self.provider = "gemini"
            else:
                self.provider = "vllm"
        else:
            self.provider = provider.lower()

        if self.provider == "gemini":
            default_model = os.getenv("GEMINI_MODEL") or "gemini-3.1-pro-preview"
        elif self.provider == "bedrock":
            default_model = os.getenv("BEDROCK_MODEL_ARN") or "anthropic.claude-3-5-sonnet-20241022-v2:0"
        else:
            default_model = os.getenv("VLLM_MODEL") or "Qwen/Qwen3.6-35B-A3B-FP8"

        self.model_name = model_name or default_model
        self.temperature = 0.0

        if self.provider == "gemini":
            if not HAS_GOOGLE_GENAI:
                raise ImportError("google-generativeai SDK is required for Gemini. Run: pip install google-generativeai")
            key = gemini_api_key
            if not key:
                raise ValueError(
                    "Missing Gemini API key. Please set 'gemini_key' or 'GEMINI_API_KEY' in your .env file."
                )
            genai.configure(api_key=key)
            clean_model = self.model_name
            if clean_model.startswith("models/"):
                clean_model = clean_model.replace("models/", "")
            self.gemini_model = genai.GenerativeModel(clean_model)
            logger.info(
                f"Initialized Google Gemini Vision Extractor | Model: {clean_model}"
            )
        elif self.provider == "bedrock":
            if not HAS_BOTO3:
                raise ImportError("boto3 SDK is required for AWS Bedrock. Run: pip install boto3")
            region = aws_region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
            self.bedrock_client = boto3.client("bedrock-runtime", region_name=region)
            logger.info(
                f"Initialized AWS Bedrock Vision Extractor | ARN/Model: {self.model_name} | Region: {region}"
            )
        else:
            if not HAS_OPENAI:
                raise ImportError("openai SDK is required for vLLM. Run: pip install openai")
            base_url = base_url or os.getenv("VLLM_BASE_URL")
            if not base_url:
                raise ValueError(
                    "Missing vLLM base URL. Please set VLLM_BASE_URL in your environment or .env file (or set gemini_key for Gemini)."
                )
            key = api_key or os.getenv("VLLM_API_KEY") or "dummy"
            self.client = OpenAI(base_url=base_url, api_key=key)
            self.max_tokens = 8192
            logger.info(
                f"Initialized vLLM Vision Extractor | Model: {self.model_name} | Endpoint: {base_url}"
            )

    def _call_vlm(self, pil_img: Image.Image, prompt_text: str) -> str:
        """
        Sends PIL Image + prompt to Google Gemini, AWS Bedrock, or vLLM OpenAI-compatible endpoint.
        """
        # --- PATH 1: Google Gemini API ---
        if self.provider == "gemini":
            for attempt in range(1, 4):
                try:
                    response = self.gemini_model.generate_content(
                        [pil_img, prompt_text],
                        generation_config={"temperature": self.temperature}
                    )
                    if response and response.text:
                        return response.text
                    logger.warning(f"Empty response from Gemini on attempt {attempt}, retrying...")
                    time.sleep(2)
                except Exception as exc:
                    logger.error(f"Gemini API error on attempt {attempt}: {exc}")
                    if attempt == 3:
                        raise exc
                    time.sleep(3)
            return ""

        img_byte_arr = io.BytesIO()
        pil_img.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # --- PATH 2: AWS Bedrock Converse API ---
        if self.provider == "bedrock":
            for attempt in range(1, 4):
                try:
                    response = self.bedrock_client.converse(
                        modelId=self.model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"image": {"format": "png", "source": {"bytes": img_bytes}}},
                                    {"text": prompt_text}
                                ]
                            }
                        ],
                        inferenceConfig={
                            "temperature": self.temperature,
                            "maxTokens": 4096
                        }
                    )
                    content_list = response.get("output", {}).get("message", {}).get("content", [])
                    if content_list and "text" in content_list[0]:
                        return content_list[0]["text"]
                    logger.warning(f"Empty response from AWS Bedrock on attempt {attempt}, retrying...")
                    time.sleep(2)
                except Exception as exc:
                    logger.error(f"AWS Bedrock API error on attempt {attempt}: {exc}")
                    if attempt == 3:
                        raise exc
                    time.sleep(3)
            return ""

        # --- PATH 3: vLLM OpenAI-Compatible API ---
        b64 = base64.b64encode(img_bytes).decode("utf-8")
        data_uri = f"data:image/png;base64,{b64}"

        messages = [
            {
                "role": "system",
                "content": "You are an expert Lead Process & Mechanical P&ID Engineer. Return ONLY a valid JSON object starting with { and ending with }. Never output any reasoning, preamble, markdown text, or explanations outside the JSON."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": data_uri}},
                ],
            }
        ]

        for attempt in range(1, 4):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                text = response.choices[0].message.content if response.choices else None
                if text:
                    return text
                logger.warning(f"Empty response on attempt {attempt}, retrying...")
                time.sleep(2)
            except Exception as exc:
                logger.error(f"vLLM API error on attempt {attempt}: {exc}")
                if attempt == 3:
                    raise exc
                time.sleep(3)
        return ""

    def process_page_multipass(
        self, 
        pil_img: Image.Image, 
        num_passes: int = 1
    ) -> Dict[str, Any]:
        """
        Executes 1 (fast single-pass) or multi-pass extraction on a single P&ID image.
        """
        # --- PASS 1: Discovery & Single-Pass Analysis ---
        raw_pass1 = self._call_vlm(pil_img, PROMPT_PASS_1_DISCOVERY)
        pass1_data = clean_json_response(raw_pass1)

        if num_passes <= 1:
            return pass1_data

        # --- PASS 2: Verification & Audit ---
        pass2_prompt = PROMPT_PASS_2_AUDIT.format(
            pass1_json=json.dumps(pass1_data, indent=2)
        )
        raw_pass2 = self._call_vlm(pil_img, pass2_prompt)
        pass2_data = clean_json_response(raw_pass2)

        if num_passes == 2:
            return pass2_data if pass2_data.get("equipments") else pass1_data

        # --- PASS 3: Consensus ---
        pass3_prompt = PROMPT_PASS_3_CONSENSUS.format(
            pass1_json=json.dumps(pass1_data, indent=2),
            pass2_json=json.dumps(pass2_data, indent=2)
        )
        raw_pass3 = self._call_vlm(pil_img, pass3_prompt)
        pass3_data = clean_json_response(raw_pass3)

        return pass3_data if pass3_data.get("equipments") else (pass2_data or pass1_data)


# =============================================================================
# CHECKPOINT / RESUME SUPPORT
# =============================================================================

CHECKPOINT_FILENAME = "_checkpoint.json"


class CheckpointManager:
    """
    Thread-safe, JSON-backed log of per-file processing status, stored as
    ``<output_dir>/_checkpoint.json``. Lets a run be interrupted (crash, Ctrl+C,
    API outage) and resumed later without redoing files that already succeeded.
    Entries are written atomically (temp file + replace) after every file so the
    log is always consistent even if the process is killed mid-run.
    """

    def __init__(self, output_dir: Path):
        self.path = output_dir / CHECKPOINT_FILENAME
        self._lock = threading.Lock()
        self._data: Dict[str, Any] = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning(f"Could not read checkpoint file {self.path}: {exc}. Starting fresh.")
                self._data = {}

    def status(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._data.get(key)
            return entry.get("status") if entry else None

    def should_skip(self, key: str, overwrite: bool) -> bool:
        """Skip only files already marked 'success'; errored files are retried automatically."""
        if overwrite:
            return False
        return self.status(key) == "success"

    def record(self, key: str, status: str, **fields) -> None:
        entry = {"status": status, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), **fields}
        with self._lock:
            self._data[key] = entry
            tmp_path = self.path.with_suffix(".json.tmp")
            tmp_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            tmp_path.replace(self.path)

    def summary(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for entry in self._data.values():
                s = entry.get("status", "unknown")
                counts[s] = counts.get(s, 0) + 1
            return counts

    def all_records(self) -> List[Dict[str, Any]]:
        """Flatten the per-file 'records' stashed by run_directory_tree's --merge_only mode."""
        with self._lock:
            out: List[Dict[str, Any]] = []
            for entry in self._data.values():
                out.extend(entry.get("records", []) or [])
            return out

    def records_for(self, key: str) -> List[Dict[str, Any]]:
        with self._lock:
            entry = self._data.get(key)
            return list(entry.get("records", [])) if entry else []


# =============================================================================
# MAIN ORCHESTRATION & PARALLEL PROCESSING
# =============================================================================

def process_pdf_or_image(
    file_path: Path, 
    extractor: PNIDEquipmentExtractor, 
    num_passes: int = 1
) -> List[Dict[str, Any]]:
    """
    Processes a PDF or image file and returns structured records for Excel output.
    """
    records = []
    file_name = file_path.name

    if file_path.suffix.lower() == ".pdf":
        pil_images = pdf_to_pil_images(str(file_path), dpi=300)
    elif file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        pil_images = [Image.open(file_path)]
    else:
        logger.warning(f"Skipping unsupported file format: {file_path}")
        return []

    for page_idx, img in enumerate(pil_images, start=1):
        pg_num_str = f"Page {page_idx}"

        try:
            result = extractor.process_page_multipass(img, num_passes=num_passes)
            pnid_number = result.get("pnid_drawing_number", "UNKNOWN")
            raw_equipments = result.get("equipments", []) or []
            is_legend = bool(result.get("sheet_is_legend_or_index"))

            # Post-extraction guard: drop valves / instruments / placeholders / non-tags / duplicates
            if is_legend:
                equipments = []
            else:
                equipments = []
                seen_tags = set()
                for eq in raw_equipments:
                    raw_tag = eq.get("equipment_name", "").strip()
                    desc = eq.get("equipment_description", "").strip()
                    status = (eq.get("status") or "EXISTING").strip().upper()
                    
                    # Split twin/standby tags like P-101A/B into ['P-101A', 'P-101B']
                    for split_tag in split_standby_tags(raw_tag):
                        tag_key = split_tag.strip().upper()
                        if tag_key not in seen_tags and is_real_equipment(split_tag, pnid_number):
                            seen_tags.add(tag_key)
                            equipments.append({
                                "equipment_name": split_tag,
                                "equipment_description": desc,
                                "status": status,
                            })

            dropped = len(raw_equipments) - len(equipments)
            eq_names = [e["equipment_name"] for e in equipments]
            eq_preview = f" -> {', '.join(eq_names)}" if eq_names else " (None)"
            logger.info(
                f"  [{file_name} | {pg_num_str}] Drawing: '{pnid_number}' | "
                f"Found {len(equipments)} major equipment(s){eq_preview}"
            )

            # Only add records if real major equipment was found
            for eq in equipments:
                records.append({
                    "pdf name": file_name,
                    "pg number": pg_num_str,
                    "pnid drawing number": pnid_number,
                    "Equipment name": eq.get("equipment_name", "").strip(),
                    "Equipment Description": eq.get("equipment_description", "").strip(),
                    "Equipment Status": eq.get("status", "EXISTING"),
                })
        except Exception as exc:
            logger.error(f"Error processing page {page_idx} of {file_name}: {exc}")
            records.append({
                "pdf name": file_name,
                "pg number": pg_num_str,
                "pnid drawing number": "ERROR",
                "Equipment name": "ERROR",
                "Equipment Description": f"Error: {exc}",
                "Equipment Status": "ERROR",
            })

    return records


OUTPUT_COLUMNS = [
    "pdf name",
    "pg number",
    "pnid drawing number",
    "Equipment name",
    "Equipment Description",
    "Equipment Status",
]

SUPPORTED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def records_to_df(records: List[Dict[str, Any]]) -> "pd.DataFrame":
    """Build a DataFrame with the exact requested column set / order."""
    df = pd.DataFrame(records)
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[OUTPUT_COLUMNS]


def save_df_to_excel(df: "pd.DataFrame", out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(out_path, index=False, engine="openpyxl")


def process_single_file_wrapper(
    f: Path,
    extractor: PNIDEquipmentExtractor,
    num_passes: int,
    file_idx: int,
    total_files: int,
    output_dir: Path,
    checkpoint: "CheckpointManager",
    overwrite: bool = False,
) -> List[Dict[str, Any]]:
    """Thread-safe worker function to process a single PDF/image file, save its individual Excel, and report exact time taken."""
    key = f.name
    single_out_path = output_dir / f"{f.stem}.xlsx"

    # Checkpoint: skip files already recorded as successful (unless --overwrite);
    # previously errored files fall through and are retried automatically.
    if checkpoint.should_skip(key, overwrite) and single_out_path.exists():
        logger.info(f"[{file_idx}/{total_files}] Skipping (checkpointed done): '{f.name}'")
        try:
            return pd.read_excel(single_out_path).to_dict("records")
        except Exception as exc:
            logger.warning(f"Could not re-read existing Excel for '{f.name}': {exc}")
            return []

    logger.info(f"[{file_idx}/{total_files}] [START] Processing: '{f.name}'...")
    start_t = time.time()
    try:
        recs = process_pdf_or_image(f, extractor, num_passes=num_passes)
        elapsed = time.time() - start_t
        eq_count = len([r for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")])
        eq_names = [r.get("Equipment name") for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")]
        eq_preview = f" -> {', '.join(eq_names)}" if eq_names else " (None)"

        # Save individual Excel per PDF
        single_df = records_to_df(recs)
        save_df_to_excel(single_df, single_out_path)

        logger.info(
            f"[{file_idx}/{total_files}] [DONE] '{f.name}' | "
            f"Time Taken: {elapsed:.1f}s | "
            f"Extracted: {eq_count} equipment(s){eq_preview}"
        )
        logger.info(f"  -> Saved: {single_out_path.resolve()}")
        checkpoint.record(key, "success", equipment_count=eq_count, elapsed_sec=round(elapsed, 1))
        return recs
    except Exception as exc:
        elapsed = time.time() - start_t
        logger.error(f"[{file_idx}/{total_files}] [FAILED] '{f.name}' | Time Taken: {elapsed:.1f}s | Error: {exc}")
        err_recs = [{
            "pdf name": f.name,
            "pg number": "Page 1",
            "pnid drawing number": "ERROR",
            "Equipment name": "ERROR",
            "Equipment Description": f"Error: {exc}",
            "Equipment Status": "ERROR",
        }]
        save_df_to_excel(records_to_df(err_recs), single_out_path)
        checkpoint.record(key, "error", error=str(exc), elapsed_sec=round(elapsed, 1))
        return err_recs


def run_directory_tree(
    input_dir: Path,
    output_dir: Path,
    extractor: "PNIDEquipmentExtractor",
    num_passes: int = 1,
    limit: Optional[int] = None,
    overwrite: bool = False,
    max_workers: int = 10,
    merge_only: bool = False,
    merge_output: Optional[Path] = None,
) -> None:
    """
    Recursively process every supported file under ``input_dir`` in parallel.

    By default writes one .xlsx per input file under ``output_dir``, mirroring the
    folder structure. If ``merge_only`` is True, the per-file Excels are skipped and
    a single combined Excel for the whole folder is written instead (to
    ``merge_output``, default: ``output_dir/<input_dir.name>.xlsx``). Extracted
    records are always cached inside the checkpoint log, so resuming an
    interrupted --merge_only run still produces a complete combined file.
    """
    files = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )
    if limit is not None:
        files = files[:limit]

    total_files = len(files)
    logger.info(f"Found {total_files} file(s) under '{input_dir}' to process with {max_workers} worker threads.")

    checkpoint = CheckpointManager(output_dir)
    prior = checkpoint.summary()
    if prior:
        logger.info(f"Loaded checkpoint '{checkpoint.path.name}' | Prior status: {prior}")

    def process_tree_file(idx_src):
        idx, src = idx_src
        rel = src.relative_to(input_dir)
        key = rel.as_posix()
        out_path = output_dir / rel.with_suffix(".xlsx")

        # Checkpoint: skip files already recorded as successful (unless --overwrite);
        # previously errored files fall through and are retried automatically.
        # In merge_only mode there's no per-file .xlsx to sanity-check against, so
        # the checkpoint status alone decides.
        already_done = checkpoint.should_skip(key, overwrite)
        if already_done and (merge_only or out_path.exists()):
            logger.info(f"[{idx}/{total_files}] Skipping (checkpointed done): {rel}")
            return

        logger.info(f"[{idx}/{total_files}] [START] Processing: '{rel}'...")
        start_t = time.time()
        try:
            # Per-file isolation: an exception here (corrupt PDF, render failure, etc.)
            # is caught and recorded so it can't abort the rest of the batch.
            recs = process_pdf_or_image(src, extractor, num_passes=num_passes)
            elapsed = time.time() - start_t

            if not merge_only:
                save_df_to_excel(records_to_df(recs), out_path)

            eq_count = len([r for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")])
            eq_names = [r.get("Equipment name") for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")]
            eq_preview = f" -> {', '.join(eq_names)}" if eq_names else " (None)"
            logger.info(
                f"[{idx}/{total_files}] [DONE] '{rel}' | "
                f"Time Taken: {elapsed:.1f}s | "
                f"Extracted: {eq_count} equipment(s){eq_preview}"
            )
            if not merge_only:
                logger.info(f"  -> Saved: {out_path.resolve()}")
            checkpoint.record(key, "success", equipment_count=eq_count, elapsed_sec=round(elapsed, 1), records=recs)
        except Exception as exc:
            elapsed = time.time() - start_t
            logger.error(f"[{idx}/{total_files}] [FAILED] '{rel}' | Time Taken: {elapsed:.1f}s | Error: {exc}")
            err_recs = [{
                "pdf name": src.name,
                "pg number": "Page 1",
                "pnid drawing number": "ERROR",
                "Equipment name": "ERROR",
                "Equipment Description": f"Error: {exc}",
                "Equipment Status": "ERROR",
            }]
            if not merge_only:
                save_df_to_excel(records_to_df(err_recs), out_path)
            checkpoint.record(key, "error", error=str(exc), elapsed_sec=round(elapsed, 1), records=err_recs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_tree_file, enumerate(files, start=1)))

    logger.info(f"Checkpoint summary: {checkpoint.summary()}")

    if merge_only:
        all_records = checkpoint.all_records()
        combined_path = merge_output or (output_dir / f"{input_dir.name}.xlsx")
        save_df_to_excel(records_to_df(all_records), combined_path)
        total_eq = len([r for r in all_records if r.get("Equipment name") not in ("N/A", "ERROR")])
        logger.info(f"Saved combined Excel for '{input_dir.name}' -> {combined_path.resolve()} | Total equipment: {total_eq}")


def run_directory_tree_per_folder(
    input_dir: Path,
    output_dir: Path,
    extractor: "PNIDEquipmentExtractor",
    num_passes: int = 1,
    limit: Optional[int] = None,
    overwrite: bool = False,
    max_workers: int = 10,
) -> None:
    """
    Point this at one top-level folder (e.g. "FIP") containing several subfolders of
    PDFs. Every file under it is processed in a single shared parallel pool (for max
    throughput), then results are grouped by each file's immediate subfolder and one
    combined Excel is written per subfolder (e.g. FIP/BOCPP-A PNID/*.pdf ->
    output_dir/BOCPP-A PNID.xlsx). No per-PDF Excel files are written. Files sitting
    directly in input_dir (no subfolder) are grouped under input_dir's own name.
    Fully resumable via the shared checkpoint log, same as run_directory_tree.
    """
    files = sorted(
        p for p in input_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    )
    if limit is not None:
        files = files[:limit]

    total_files = len(files)
    logger.info(f"Found {total_files} file(s) under '{input_dir}' to process with {max_workers} worker threads.")

    checkpoint = CheckpointManager(output_dir)
    prior = checkpoint.summary()
    if prior:
        logger.info(f"Loaded checkpoint '{checkpoint.path.name}' | Prior status: {prior}")

    def group_of(src: Path) -> str:
        rel = src.relative_to(input_dir)
        return rel.parts[0] if len(rel.parts) > 1 else input_dir.name

    def process_one(idx_src):
        idx, src = idx_src
        rel = src.relative_to(input_dir)
        key = rel.as_posix()

        if checkpoint.should_skip(key, overwrite):
            logger.info(f"[{idx}/{total_files}] Skipping (checkpointed done): {rel}")
            return

        logger.info(f"[{idx}/{total_files}] [START] Processing: '{rel}'...")
        start_t = time.time()
        try:
            # Per-file isolation: an exception here (corrupt PDF, render failure, etc.)
            # is caught and recorded so it can't abort the rest of the batch.
            recs = process_pdf_or_image(src, extractor, num_passes=num_passes)
            elapsed = time.time() - start_t
            eq_count = len([r for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")])
            eq_names = [r.get("Equipment name") for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")]
            eq_preview = f" -> {', '.join(eq_names)}" if eq_names else " (None)"
            logger.info(
                f"[{idx}/{total_files}] [DONE] '{rel}' | "
                f"Time Taken: {elapsed:.1f}s | "
                f"Extracted: {eq_count} equipment(s){eq_preview}"
            )
            checkpoint.record(key, "success", equipment_count=eq_count, elapsed_sec=round(elapsed, 1), records=recs)
        except Exception as exc:
            elapsed = time.time() - start_t
            logger.error(f"[{idx}/{total_files}] [FAILED] '{rel}' | Time Taken: {elapsed:.1f}s | Error: {exc}")
            err_recs = [{
                "pdf name": src.name,
                "pg number": "Page 1",
                "pnid drawing number": "ERROR",
                "Equipment name": "ERROR",
                "Equipment Description": f"Error: {exc}",
                "Equipment Status": "ERROR",
            }]
            checkpoint.record(key, "error", error=str(exc), elapsed_sec=round(elapsed, 1), records=err_recs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_one, enumerate(files, start=1)))

    logger.info(f"Checkpoint summary: {checkpoint.summary()}")

    # Group every processed file's cached records by its immediate subfolder and
    # write one combined Excel per subfolder.
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for src in files:
        rel = src.relative_to(input_dir)
        groups.setdefault(group_of(src), []).extend(checkpoint.records_for(rel.as_posix()))

    for group_name, recs in sorted(groups.items()):
        out_path = output_dir / f"{group_name}.xlsx"
        save_df_to_excel(records_to_df(recs), out_path)
        eq_count = len([r for r in recs if r.get("Equipment name") not in ("N/A", "ERROR")])
        logger.info(f"Saved combined Excel for folder '{group_name}' -> {out_path.resolve()} | Total equipment: {eq_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract Major Equipment from P&ID PDF/image files using a vLLM-served vision model into separate individual Excel files."
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to a single P&ID PDF or Image file."
    )
    parser.add_argument(
        "--pdf_dir",
        type=str,
        help="Path to a directory containing P&ID PDF/Image files."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        help="Root directory to scan recursively. One .xlsx is written per input file under --output_dir, mirroring folder structure.",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="extracted_excels",
        help="Directory to save individual .xlsx files (one per PDF). Default: extracted_excels",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="With --pdf/--pdf_dir: also generate a combined master Excel file in addition to individual Excels.",
    )
    parser.add_argument(
        "--merge_only",
        action="store_true",
        help="With --input_dir: skip writing one .xlsx per PDF and write a single combined Excel for the whole "
             "folder instead (default name: <output_dir>/<input folder name>.xlsx, override with --output_merged).",
    )
    parser.add_argument(
        "--merge_per_folder",
        action="store_true",
        help="With --input_dir pointed at a top-level folder containing several subfolders (e.g. 'FIP'): process "
             "every PDF across all subfolders in one parallel run, then write one combined Excel per immediate "
             "subfolder into --output_dir (e.g. FIP/BOCPP-A PNID/*.pdf -> output_dir/BOCPP-A PNID.xlsx). "
             "No per-PDF Excel files are written. Takes priority over --merge_only.",
    )
    parser.add_argument(
        "--output_merged",
        type=str,
        default=None,
        help="File path for the combined Excel (used with --merge, or --merge_only under --input_dir). "
             "Default: 'master_all_equipments.xlsx' for --merge, or '<output_dir>/<input folder name>.xlsx' for --merge_only.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="Number of concurrent worker threads for parallel processing. Default: 10",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N files. Useful for quick tests.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Reprocess files whose output .xlsx already exists.",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Number of AI extraction passes (1=Fast Single Pass, 2 or 3=Multi-pass). Default: 1"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="auto",
        choices=["auto", "vllm", "bedrock", "gemini"],
        help="AI Provider to use: 'auto' (detects based on ARN/URL/key), 'gemini', 'vllm', or 'bedrock'. Default: auto"
    )
    parser.add_argument(
        "--aws_region",
        type=str,
        default=None,
        help="AWS Region for Bedrock (e.g. us-east-1, ap-southeast-1). Default: $AWS_REGION or us-east-1"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name or AWS Bedrock Model/Inference-Profile ARN (e.g. arn:aws:bedrock:us-east-1:...)."
    )

    args = parser.parse_args()

    if not args.pdf and not args.pdf_dir and not args.input_dir:
        parser.error("You must specify --pdf <file>, --pdf_dir <directory>, or --input_dir <directory>.")

    # Initialize Extractor (auto-supports vLLM and AWS Bedrock via ARN)
    extractor = PNIDEquipmentExtractor(
        model_name=args.model,
        provider=args.provider,
        aws_region=args.aws_region,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    start_total_time = time.time()

    # --- Recursive, folder-structure-preserving mode ---
    if args.input_dir:
        in_dir = Path(args.input_dir)
        if not in_dir.is_dir():
            logger.error(f"Directory not found: {in_dir}")
            return

        if args.merge_per_folder:
            run_directory_tree_per_folder(
                in_dir,
                out_dir,
                extractor,
                num_passes=args.passes,
                limit=args.limit,
                overwrite=args.overwrite,
                max_workers=args.workers,
            )
            total_elapsed = time.time() - start_total_time
            logger.info("=================================================================")
            logger.info(f"All processing complete in {total_elapsed:.1f}s.")
            logger.info(f"One combined Excel per subfolder saved in: {out_dir.resolve()}")
            logger.info("=================================================================")
            return

        merge_output = Path(args.output_merged) if args.output_merged else None
        run_directory_tree(
            in_dir,
            out_dir,
            extractor,
            num_passes=args.passes,
            limit=args.limit,
            overwrite=args.overwrite,
            max_workers=args.workers,
            merge_only=args.merge_only,
            merge_output=merge_output,
        )
        total_elapsed = time.time() - start_total_time
        logger.info("=================================================================")
        logger.info(f"All processing complete in {total_elapsed:.1f}s.")
        if args.merge_only:
            logger.info(f"Combined Excel saved in: {out_dir.resolve()}")
        else:
            logger.info(f"Individual Excel files saved in: {out_dir.resolve()}")
        logger.info("=================================================================")
        return

    # --- Single / Batch PDF Directory mode ---
    files_to_process: List[Path] = []
    if args.pdf:
        p = Path(args.pdf)
        if not p.exists():
            logger.error(f"File not found: {p}")
            return
        files_to_process.append(p)

    if args.pdf_dir:
        d = Path(args.pdf_dir)
        if not d.exists() or not d.is_dir():
            logger.error(f"Directory not found: {d}")
            return
        for ext in ["*.pdf", "*.png", "*.jpg", "*.jpeg"]:
            files_to_process.extend(d.glob(ext))

    if args.limit:
        files_to_process = files_to_process[:args.limit]

    total_files = len(files_to_process)
    logger.info(f"Found {total_files} file(s) to process with {args.workers} parallel worker(s)...")
    logger.info(f"Saving separate individual Excel per PDF to: {out_dir.resolve()}")

    checkpoint = CheckpointManager(out_dir)
    prior = checkpoint.summary()
    if prior:
        logger.info(f"Loaded checkpoint '{checkpoint.path.name}' | Prior status: {prior}")

    all_records = []

    if total_files == 1:
        recs = process_single_file_wrapper(
            files_to_process[0],
            extractor,
            num_passes=args.passes,
            file_idx=1,
            total_files=1,
            output_dir=out_dir,
            checkpoint=checkpoint,
            overwrite=args.overwrite,
        )
        all_records.extend(recs)
    else:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_file = {
                executor.submit(
                    process_single_file_wrapper,
                    f,
                    extractor,
                    args.passes,
                    idx,
                    total_files,
                    out_dir,
                    checkpoint,
                    args.overwrite,
                ): f
                for idx, f in enumerate(files_to_process, start=1)
            }
            for future in as_completed(future_to_file):
                recs = future.result()
                if recs:
                    all_records.extend(recs)

    total_elapsed = time.time() - start_total_time
    total_eq = len([r for r in all_records if r.get("Equipment name") not in ("N/A", "ERROR")])

    # Optional merged output only if --merge was explicitly requested
    if args.merge and all_records:
        merged_path = Path(args.output_merged) if args.output_merged else Path("master_all_equipments.xlsx")
        df_merged = records_to_df(all_records)
        save_df_to_excel(df_merged, merged_path)
        logger.info(f"Saved optional combined master Excel to: {merged_path.resolve()}")

    logger.info("=================================================================")
    logger.info(f"Processed all {total_files} file(s) in {total_elapsed:.1f}s (Average: {total_elapsed/max(1, total_files):.1f}s/file).")
    logger.info(f"Total major equipment extracted across all files: {total_eq}")
    logger.info(f"Individual Excel files saved under: {out_dir.resolve()}")
    logger.info(f"Checkpoint summary: {checkpoint.summary()}")
    logger.info("=================================================================")


if __name__ == "__main__":
    main()
