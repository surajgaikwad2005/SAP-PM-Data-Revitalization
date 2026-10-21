"""
SCE Governance Agent (Agent E) - runs the full pipeline and writes the two evaluation workbooks
(Group_A_Output_for_Evaluation.xlsx, Pain Points 1-4; Group_B_Output_for_Evaluation.xlsx, Pain Points 5-8).

    python run_sce_agent.py --with-llm             # full run, including the three LLM steps (needs .env)
    python run_sce_agent.py                        # reuses the saved LLM results in "Data exploration/output"
    python run_sce_agent.py --skip-extraction      # reuses the extracted knowledge base
    python run_sce_agent.py --in-progress          # also runs the checks of the pain points still in progress
    python run_sce_agent.py --out <folder>         # where to write the two workbooks

Input data: the "SAP PM Data Revitalization" data folder, copied into SAP_Data_New/.
Output: "Data exploration/output" (knowledge base, one D*.xlsx per check, the two workbooks).
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXTRACTION = ROOT / "code" / "extraction"
AGENT = ROOT / "code" / "agent"
OUT = ROOT / "Data exploration" / "output"

# (script, arguments, needs an LLM)
EXTRACTION_STEPS = [
    ("extract_sce_register.py", [], False),             # approved SCE identification register -> sce_register.db
    ("extract_gops4_sce_groups.py", [], False),         # GOPS4.0: the 45 SCE Groups
    ("extract_hse_case_sce_matrix.py", [], False),      # HSE Case 2020 Book 2, Part 3A.1: SCE matrix
    ("extract_ssps_requirements.py", [], False),        # Bokor SSPS: assurance tasks per SCE Group
    ("extract_ptg_12_05_04.py", [], False),             # PTG 12.05.04: valid Catalog Profiles
    ("extract_tips3.py", [], True),                     # TIPS3 Appendix D: registration level per SCE Group
    ("extract_gops4_functionality_llm.py", [], True),   # GOPS4.0: assurance tasks per SCE Group
]
CHECK_STEPS = [
    ("check_gops4_currency.py", [], False),             # PP1: SCE Group codes not in GOPS4.0
    ("check1_sce_identification.py", [], False),        # PP1: FL SCE assignment against the register
    ("check1b_equipment_sce_identification.py", [], False),  # PP1: the same findings per equipment
    ("check2_structure_tips3.py", [], False),           # PP2: structure against TIPS3
    ("check5_parent_fl_status.py", [], False),          # PP3: equipment and parent FL SCE status
    ("check3_mic_vs_ssps_gops4.py", [], False),         # PP5: MIC against SSPS and GOPS4.0
    ("check9_ssps_vs_gops4.py", [], False),             # PP5: SSPS documents that contradict GOPS4.0
    ("check8b_mic_result_vs_specification.py", [], False),  # PP8 interim: accepted results outside the specification
]
CHECK7_LLM = ("check7_mic_ps_llm_matching.py", [], True)                        # PP6: MIC to assurance task (LLM)
CHECK7_SAVED = ("check7_mic_ps_llm_matching.py", ["--gops4-rule-only"], False)  # PP6 from the saved LLM result
IN_PROGRESS_STEPS = [
    ("check6_class_completeness.py", [], False),        # PP4: SCE class fields
    ("check4_rbi_vs_maintenance_interval.py", [], False),  # PP7: RBI interval
    ("check8_inspection_lot_notification_mapping.py", [], False),  # PP8: lot to notification mapping
]
# results of the LLM steps, needed when they are not re-run
SAVED_LLM_RESULTS = ["tips3_extraction.xlsx", "gops4_functionality_tasks.xlsx", "D6_MIC_TaskList_PS_Matching.xlsx"]


def run(folder, script, args):
    print(f"\n=== {script} {' '.join(args)}".rstrip(), flush=True)
    t0 = time.time()
    subprocess.run([sys.executable, str(folder / script), *args], cwd=ROOT, check=True)
    print(f"--- done in {time.time() - t0:.0f}s", flush=True)


def main():
    p = argparse.ArgumentParser(description="Run the SCE Governance Agent (Agent E)")
    p.add_argument("--with-llm", action="store_true", help="run the LLM steps (TIPS3, GOPS4.0 tasks, PP6 matching)")
    p.add_argument("--skip-extraction", action="store_true", help="reuse the knowledge base already extracted")
    p.add_argument("--in-progress", action="store_true", help="also run the checks of the pain points in progress")
    p.add_argument("--out", help="folder for the Group A and Group B workbooks")
    a = p.parse_args()

    data = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization"
    if not data.exists():
        sys.exit(f"Input data not found: {data}\nCopy the 'SAP PM Data Revitalization' data folder into SAP_Data_New/.")
    OUT.mkdir(parents=True, exist_ok=True)
    missing = [f for f in SAVED_LLM_RESULTS if not (OUT / f).exists()]
    if missing and not a.with_llm:
        sys.exit(f"No saved LLM results ({', '.join(missing)}) in {OUT}.\nRun with --with-llm (needs .env).")

    t0 = time.time()
    if not a.skip_extraction:
        for script, args, llm in EXTRACTION_STEPS:
            if llm and not a.with_llm:
                print(f"\n=== {script}: skipped (LLM step; the saved result is used)")
                continue
            run(EXTRACTION, script, args)
    for script, args, _ in CHECK_STEPS + [CHECK7_LLM if a.with_llm else CHECK7_SAVED]:
        run(AGENT, script, args)
    if a.in_progress:
        for script, args, _ in IN_PROGRESS_STEPS:
            run(AGENT, script, args)
    if a.out:
        Path(a.out).mkdir(parents=True, exist_ok=True)
    run(AGENT, "build_group_evaluation_workbooks.py", [str(Path(a.out).resolve())] if a.out else [])
    print(f"\nSCE Agent finished in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
