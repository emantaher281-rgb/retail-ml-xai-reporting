"""
verify_package.py - self-audit of the reproducibility package.

Checks that this repository satisfies every item required by the review:
datasets, code, configurations, evaluation procedures, prompts, environment
specifications, and the materials needed to reproduce the reported results.
It also confirms that no execution outputs and no credentials have been
committed.

    python verify_package.py

Exits non-zero if any required item is missing, so it can be run before every
push and wired into CI. Run this before resubmitting: it is the fastest way to
confirm a reviewer cloning the repository will find a complete package.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# --- credential patterns -----------------------------------------------------
# Broad on purpose: a false positive costs one look, a miss costs a live key.
SECRET_RE = re.compile(
    r"(gsk_[A-Za-z0-9_\-]{15,}"          # Groq
    r"|sk-or-v1-[A-Za-z0-9_\-]{15,}"     # OpenRouter
    r"|sk-[A-Za-z0-9]{20,}"              # OpenAI-style
    r"|hf_[A-Za-z0-9]{20,}"              # Hugging Face
    r"|AIza[A-Za-z0-9_\-]{25,}"          # Google
    r"|ghp_[A-Za-z0-9]{30,})"            # GitHub PAT
)

DATASET = "data/Customer_Segmentation&Sales_Forecasting_Dataset.csv"

# Required item -> paths that satisfy it (any one is enough)
REQUIRED = [
    ("Dataset",                    [DATASET]),
    ("Dataset provenance",         ["data/README.md"]),
    ("Module 1 - segmentation",    ["Code/01_customer_segmentation.ipynb"]),
    ("Module 2 - recommendation",  ["Code/02_product_recommendation.ipynb"]),
    ("Module 3 - product-level",   ["Code/03_product_level_sales_prediction.ipynb"]),
    ("Module 4 - forecasting",     ["Code/04_daily_sales_forecasting.ipynb"]),
    ("Module 5 - LLM reporting",   ["Code/05_llm_decision_report.ipynb"]),
    ("Seeds / shared repro layer", ["src/repro.py"]),
    ("Table-consistency check",    ["src/check_tables.py"]),
    ("Clustering config",          ["configuration/segmentation.yaml"]),
    ("Recommender config",         ["configuration/recommendation.yaml"]),
    ("Forecasting config",         ["configuration/forecasting.yaml"]),
    ("LLM config",                 ["configuration/llm_reporting.yaml"]),
    ("LLM prompts",                ["prompts/decision_report_prompt.md"]),
    ("Environment (pip)",          ["requirements.txt"]),
    ("Environment (conda)",        ["environment.yml"]),
    ("Single executable entry",    ["run_all.py"]),
    ("README",                     ["README.md"]),
    ("Reproduction instructions",  ["docs/reproduction_instructions.md"]),
    ("Reproducibility checklist",  ["docs/reproducibility_checklist.md"]),
    ("Cluster-label derivation",   ["docs/cluster_labels.md"]),
    ("Expected results",           ["results/expected_results.md"]),
    ("Reproducibility manifest",   ["MANIFEST.md"]),
    ("Licence",                    ["LICENSE"]),
    ("Citation metadata",          ["CITATION.cff"]),
]

failures = []
warnings = []

print("=" * 74)
print("REPRODUCIBILITY PACKAGE AUDIT")
print("=" * 74)

# -----------------------------------------------------------------------------
# 1. Required items present
# -----------------------------------------------------------------------------
print("\n1. Required contents")
for label, paths in REQUIRED:
    hit = next((p for p in paths if os.path.exists(os.path.join(ROOT, p))), None)
    if hit:
        print("   [ok]      %-28s %s" % (label, hit))
    else:
        print("   [MISSING] %-28s %s" % (label, " | ".join(paths)))
        failures.append("missing: %s" % label)

# -----------------------------------------------------------------------------
# 2. Notebooks carry no stored outputs
# -----------------------------------------------------------------------------
# Committed outputs are the usual way a repository leaks stale results: a
# reader sees numbers that no longer match the code that produced them.
print("\n2. Notebooks free of stored execution output")
code_dir = os.path.join(ROOT, "Code")
if os.path.isdir(code_dir):
    for fname in sorted(os.listdir(code_dir)):
        if not fname.endswith(".ipynb"):
            continue
        nb = json.load(open(os.path.join(code_dir, fname), encoding="utf-8"))
        cells = nb.get("cells", [])
        n_out = sum(len(c.get("outputs", [])) for c in cells)
        n_exec = sum(1 for c in cells if c.get("execution_count") is not None)
        n_attach = sum(1 for c in cells if c.get("attachments"))
        has_widgets = "widgets" in nb.get("metadata", {})
        if n_out or n_exec or n_attach or has_widgets:
            print("   [FAIL]    %-46s outputs=%d exec=%d attach=%d widgets=%s"
                  % (fname, n_out, n_exec, n_attach, has_widgets))
            failures.append("stored output in %s" % fname)
        else:
            print("   [ok]      %-46s clean" % fname)

# -----------------------------------------------------------------------------
# 3. No credentials anywhere in the tree
# -----------------------------------------------------------------------------
print("\n3. No credentials committed")
SKIP_DIRS = {".git", "__pycache__", ".ipynb_checkpoints", "outputs", "figures"}
found_secret = False
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fname in filenames:
        path = os.path.join(dirpath, fname)
        if path.endswith((".png", ".pdf", ".zip", ".csv", ".pkl", ".joblib")):
            continue
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for hit in SECRET_RE.findall(text):
            rel = os.path.relpath(path, ROOT)
            print("   [FAIL]    credential-like string in %s (%s...)"
                  % (rel, hit[:10]))
            failures.append("credential in %s" % rel)
            found_secret = True
if not found_secret:
    print("   [ok]      no credential patterns found")

# -----------------------------------------------------------------------------
# 4. Generated artifacts not committed
# -----------------------------------------------------------------------------
print("\n4. Generated artifacts excluded")
for d in ("outputs", "figures"):
    p = os.path.join(ROOT, d)
    if not os.path.isdir(p):
        continue
    stray = [f for f in os.listdir(p) if f != ".gitkeep"]
    if stray:
        print("   [warn]    %s/ contains %d generated file(s): %s"
              % (d, len(stray), ", ".join(stray[:4])))
        warnings.append("%s/ not empty" % d)
    else:
        print("   [ok]      %s/ empty apart from .gitkeep" % d)

# -----------------------------------------------------------------------------
# 5. Placeholders still awaiting real values
# -----------------------------------------------------------------------------
# These are legitimate before submission but must not survive into the
# published version, so they are reported as warnings rather than failures.
print("\n5. Unfilled placeholders")
placeholder = re.compile(r"<fill in[^>]*>|<username>|<Author list>|YOUR-USERNAME")
n_ph = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fname in filenames:
        if not fname.endswith((".md", ".yaml", ".yml", ".cff", ".py")):
            continue
        if fname == os.path.basename(__file__):
            continue          # this file defines the patterns; skip itself
        path = os.path.join(dirpath, fname)
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        hits = placeholder.findall(text)
        if hits:
            rel = os.path.relpath(path, ROOT)
            print("   [warn]    %-44s %d placeholder(s)" % (rel, len(hits)))
            n_ph += len(hits)
            warnings.append("placeholders in %s" % rel)
if n_ph == 0:
    print("   [ok]      none")

# -----------------------------------------------------------------------------
# Verdict
# -----------------------------------------------------------------------------
print("\n" + "=" * 74)
if failures:
    print("FAILED - %d blocking issue(s):" % len(failures))
    for f in failures:
        print("   - %s" % f)
    if warnings:
        print("\nAlso %d warning(s)." % len(warnings))
    sys.exit(1)

print("PASSED - every required item is present, no outputs, no credentials.")
if warnings:
    print("\n%d warning(s) to resolve before the published version:" % len(warnings))
    for w in warnings:
        print("   - %s" % w)
print("=" * 74)
