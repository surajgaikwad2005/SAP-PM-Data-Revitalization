"""
Run the whole BOM Agent and write outputs/BOM_Agent_Output.xlsx

    python run.py                 # all four processes + floating list (P2 uses the LLM)
    python run.py --no-llm        # skip every AI pass (P2 near-duplicates and floating-material picks)
    python run.py --no-p2-llm     # count the P2 near-duplicate pairs but do not ask the AI about them
    python run.py --no-langfuse   # run the AI pass without tracing (not recommended)
    python run.py --workers 8     # threads for the P2 AI pass

Each process also runs on its own, e.g.  python -c "import p4_priority, json; print(json.dumps(p4_priority.run()[1], indent=2))"
"""
from __future__ import annotations
import argparse
import json
import time

import p1_category
import p2_duplicates
import p3_uom_qty
import p4_priority
import floating_materials
import draft_bom
import bom_structure
import report
import llm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="skip the P2 AI near-duplicate pass")
    ap.add_argument("--no-p2-llm", action="store_true",
                    help="P2 only: count the near-duplicate pairs but do not send them to the AI")
    ap.add_argument("--no-langfuse", action="store_true", help="run the AI pass without Langfuse tracing")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--demo", action="store_true", help="run in demo mode on a small representative sample")
    ap.add_argument("--demo-size", type=int, default=50, help="number of equipment assets to sample in demo mode")
    args = ap.parse_args()

    if args.demo:
        report.C.DEMO_MODE = True
        report.C.DEMO_SIZE = args.demo_size
        print(f"\n*** RUNNING IN DEMO MODE (sample size: {args.demo_size} equipment) ***\n")

    start = time.time()

    print("P4  building priority list ...")
    p4_df, p4_sum = p4_priority.run()

    print("P1  checking item categories ...")
    p1_df, p1_sum = p1_category.run()

    print("P3  checking UOM and quantity ...")
    p3_df, p3_sum = p3_uom_qty.run()

    print("Floating materials  linking to equipment ...")
    fl_df, fl_sum = floating_materials.run(
        use_llm=not args.no_llm, workers=args.workers, langfuse_required=not args.no_langfuse)

    print("Draft BOMs  building from the SPIR store ...")
    draft_df, draft_sum = draft_bom.run()

    print("BOM structure  checking how the parts lists are built ...")
    struct_df, struct_sum = bom_structure.run()

    print("P2  finding duplicate materials ...")
    p2_df, merge_map, p2_sum = p2_duplicates.run(
        use_llm=not (args.no_llm or args.no_p2_llm), workers=args.workers,
        langfuse_required=not args.no_langfuse)

    # A standing check on a source we hold but cannot yet use.  Reported so the
    # gap is visible to PCSB rather than quietly worked around.
    import data as _d
    _cls = _d.equipment_classification()
    _placeholder = {"?", "", "N/A", "NA", "-", "NONE", "TBA", "TBD", "NIL", "X", "."}
    _real = int((~_cls["value"].isin(_placeholder)).sum())
    classification = {
        "equipment_classified": int(_cls["key"].nunique()),
        "characteristic_values_held": int(len(_cls)),
        "characteristic_values_actually_filled": _real,
        "percent_filled": round(100 * _real / max(len(_cls), 1), 1),
    }

    results = {"p4": p4_sum, "p2": p2_sum, "p1": p1_sum, "p3": p3_sum,
               "floating": fl_sum, "draft_bom": draft_sum, "structure": struct_sum,
               "classification": classification}
    path = report.write(p4_df, p2_df, p1_df, p3_df, fl_df, results,
                        draft_df=draft_df, struct_df=struct_df)

    (report.C.OUT / "BOM_Agent_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (report.C.OUT / "P2_merge_map.json").write_text(json.dumps(merge_map, indent=1), encoding="utf-8")
    llm.flush()

    print(f"\nDone in {time.time() - start:.0f}s  ->  {path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
