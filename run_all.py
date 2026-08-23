"""
Single executable script reproducing all reported numerical tables.

    python run_all.py                 # every module, in order
    python run_all.py --module 1      # one module
    python run_all.py --list          # show modules without running
    python run_all.py --skip-llm      # modules 1-4 only (no API credentials)

Modules must run in order: each writes the CSV/JSON artifacts the next reads.
Execution stops at the first failure so a partial pipeline is never mistaken
for a completed one.
"""

import argparse
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CODE_DIR = os.path.join(REPO_ROOT, "Code")
DATA_FILE = os.path.join(
    REPO_ROOT, "data", "Customer_Segmentation&Sales_Forecasting_Dataset.csv")

MODULES = [
    (1, "01_customer_segmentation.ipynb",
     "LRFMV clustering, cluster validity, segmentation XAI"),
    (2, "02_product_recommendation.ipynb",
     "cluster-based / CF / association-rule recommenders + XAI"),
    (3, "03_product_level_sales_prediction.ipynb",
     "product-level sales prediction + XAI"),
    (4, "04_daily_sales_forecasting.ipynb",
     "temporal features, five forecasting models, forecasting XAI"),
    (5, "05_llm_decision_report.ipynb",
     "structured context, prompts, LLaMA-3.3-70B decision reports"),
]

LLM_MODULE = 5


def run_notebook(filename):
    path = os.path.join(CODE_DIR, filename)
    if not os.path.exists(path):
        print("   SKIPPED - not found: %s" % filename)
        return 0.0

    cmd = [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--inplace",
        "--ExecutePreprocessor.timeout=-1",
        path,
    ]
    started = time.time()
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    elapsed = time.time() - started

    if result.returncode != 0:
        print("\nFAILED after %.1fs: %s" % (elapsed, filename))
        print("Later modules read files this one produces, so the run stops here.")
        sys.exit(result.returncode)

    print("   completed in %.1fs" % elapsed)
    return elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", type=int, help="run a single module by number")
    ap.add_argument("--list", action="store_true", help="list modules and exit")
    ap.add_argument("--skip-llm", action="store_true",
                    help="run modules 1-4 only (no API credentials needed)")
    args = ap.parse_args()

    if args.list:
        for num, fn, desc in MODULES:
            state = "present" if os.path.exists(os.path.join(CODE_DIR, fn)) else "missing"
            print("  %d  %-42s %-9s %s" % (num, fn, state, desc))
        return

    if not os.path.exists(DATA_FILE):
        sys.exit("Dataset not found:\n   %s\nSee data/README.md."
                 % os.path.relpath(DATA_FILE, REPO_ROOT))

    selected = [m for m in MODULES
                if (args.module is None or m[0] == args.module)
                and not (args.skip_llm and m[0] == LLM_MODULE)]
    if not selected:
        sys.exit("Nothing to run. Use --list to see the options.")

    # Module 5 needs a credential; fail before spending time on 1-4.
    if any(m[0] == LLM_MODULE for m in selected) and not os.environ.get("GROQ_API_KEY"):
        print("NOTE: GROQ_API_KEY is not set, so module 5 will fail.")
        print("      Export it, or use --skip-llm to run modules 1-4 only.")
        print("      All quantitative tables come from modules 1-4.\n")

    print("=" * 74)
    print("REPRODUCING ALL REPORTED RESULTS")
    print("=" * 74)

    total = 0.0
    for num, filename, desc in selected:
        print("\n[module %d] %s" % (num, desc))
        print("           %s" % filename)
        total += run_notebook(filename)

    print("\n" + "=" * 74)
    print("Finished in %.1fs" % total)
    print("Figures   -> figures/")
    print("Artifacts -> outputs/")
    print("\nVerify the segmentation tables:")
    print("   python src/check_tables.py")


if __name__ == "__main__":
    main()
