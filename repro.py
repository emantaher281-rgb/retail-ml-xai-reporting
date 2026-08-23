"""
repro.py - shared reproducibility layer for all five modules.

Every notebook begins with:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.getcwd()), "src"))
    from repro import *
    init_module("01_customer_segmentation")

This single place fixes the seed, resolves paths, captures the environment,
pins the dataset by digest, and turns every plt.show() into a saved figure.
Keeping it out of the notebooks means the same guarantees apply to all
modules and cannot drift apart between them.
"""

import hashlib
import itertools
import json
import os
import platform
import random
import re
import sys

# =============================================================================
# 1. GLOBAL SEED
# =============================================================================
# One seed governs every stochastic component in the pipeline. It is also
# passed explicitly to each estimator, because a global seed alone does not
# make scikit-learn, skfuzzy, or LIME deterministic.
SEED = 42

os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)

import numpy as np  # noqa: E402

np.random.seed(SEED)

#: Module-level generator for any sampling that must be reproducible.
RNG = np.random.default_rng(SEED)

# =============================================================================
# 2. PATHS
# =============================================================================
# Notebooks live in Code/, so the repository root is one level up.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_THIS_DIR)

DATA_DIR = os.path.join(REPO_ROOT, "data")
FIG_ROOT = os.path.join(REPO_ROOT, "figures")
OUT_ROOT = os.path.join(REPO_ROOT, "outputs")

DATASET_NAME = "Customer_Segmentation&Sales_Forecasting_Dataset.csv"
DATA_FILE = os.path.join(DATA_DIR, DATASET_NAME)

for _d in (DATA_DIR, FIG_ROOT, OUT_ROOT):
    os.makedirs(_d, exist_ok=True)

# Populated by init_module()
MODULE_NAME = None
FIG_DIR = None
OUT_DIR = None

# =============================================================================
# 3. MATPLOTLIB
# =============================================================================
import matplotlib  # noqa: E402

_IN_NOTEBOOK = "ipykernel" in sys.modules
if not _IN_NOTEBOOK and not os.environ.get("DISPLAY") \
        and sys.platform not in ("win32", "darwin"):
    matplotlib.use("Agg")  # headless servers and CI

import matplotlib.pyplot as plt  # noqa: E402

SAVE_FIGURES = True
FIG_DPI = 300
FIG_FORMATS = ("png", "pdf")  # raster for Word, vector for the journal

_fig_counter = itertools.count(1)
_original_show = plt.show


def _slugify(text, maxlen=60):
    text = re.sub(r"[^\w\s-]", "", str(text)).strip().lower()
    text = re.sub(r"[\s_-]+", "_", text)
    return text[:maxlen] or "figure"


def _figure_stem(fig):
    """Name a figure after its own title so the folder is self-documenting."""
    sup = getattr(fig, "_suptitle", None)
    if sup is not None and sup.get_text().strip():
        return _slugify(sup.get_text())
    for ax in fig.get_axes():
        if ax.get_title().strip():
            return _slugify(ax.get_title())
    return "figure"


def save_current_figure(name=None):
    """Write the active figure to figures/<module>/ in every format."""
    fig = plt.gcf()
    if not fig.get_axes():
        return []
    stem = _slugify(name) if name else _figure_stem(fig)
    idx = next(_fig_counter)
    saved = []
    for ext in FIG_FORMATS:
        path = os.path.join(FIG_DIR, "%02d_%s.%s" % (idx, stem, ext))
        fig.savefig(path, dpi=FIG_DPI, bbox_inches="tight", facecolor="white")
        saved.append(path)
    print("   [figure saved] " + os.path.relpath(saved[0], REPO_ROOT))
    return saved


def _show_and_save(*args, **kwargs):
    fig = plt.gcf()
    if SAVE_FIGURES:
        save_current_figure()
    if _IN_NOTEBOOK:
        _original_show(*args, **kwargs)
    plt.close(fig)


plt.show = _show_and_save


def save_remaining_figures():
    """Catch figures that were created but never passed to plt.show()."""
    for num in plt.get_fignums():
        plt.figure(num)
        if plt.gcf().get_axes() and SAVE_FIGURES:
            save_current_figure()
    plt.close("all")


# Backwards-compatible alias used by the original notebooks.
_save_remaining_figures = save_remaining_figures

# =============================================================================
# 4. NOTEBOOK / SCRIPT COMPATIBILITY
# =============================================================================
try:
    from IPython.display import display
except ImportError:
    def display(obj):
        print(obj.to_string() if hasattr(obj, "to_string") else obj)


def _require_file(path, produced_by):
    """Fail early and say which module produces a missing input."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            "Required input file not found: %s\n"
            "Run %s first - it produces this file." % (path, produced_by))
    return path


def _section(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# =============================================================================
# 5. DATASET FINGERPRINT
# =============================================================================
def sha256_of(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _package_versions():
    versions = {}
    for pkg in ("numpy", "pandas", "scipy", "scikit-learn", "matplotlib",
                "seaborn", "statsmodels", "shap", "lime", "scikit-fuzzy",
                "xgboost", "mlxtend"):
        try:
            from importlib.metadata import version
            versions[pkg] = version(pkg)
        except Exception:
            versions[pkg] = "not installed"
    return versions


# =============================================================================
# 6. MODULE INITIALISATION
# =============================================================================
def init_module(module_name, needs_dataset=True):
    """
    Prepare directories, write the run manifest, and switch the working
    directory to outputs/ so the modules can exchange artifacts by plain
    file name while figures and data stay at absolute paths.
    """
    global MODULE_NAME, FIG_DIR, OUT_DIR

    MODULE_NAME = module_name
    short = module_name.split("_", 1)[-1]
    FIG_DIR = os.path.join(FIG_ROOT, short)
    OUT_DIR = OUT_ROOT  # one shared artifact directory across modules
    os.makedirs(FIG_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    _section("MODULE %s" % module_name)

    manifest = {
        "module": module_name,
        "seed": SEED,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": _package_versions(),
    }

    if needs_dataset:
        _require_file(DATA_FILE, "nothing - this is the raw dataset")
        manifest["dataset_file"] = DATASET_NAME
        manifest["dataset_sha256"] = sha256_of(DATA_FILE)
        manifest["dataset_bytes"] = os.path.getsize(DATA_FILE)

    print(json.dumps(manifest, indent=2))

    with open(os.path.join(OUT_ROOT, "run_manifest_%s.json" % short), "w") as fh:
        json.dump(manifest, fh, indent=2)

    print("\nFigures   -> " + os.path.relpath(FIG_DIR, REPO_ROOT))
    print("Artifacts -> " + os.path.relpath(OUT_DIR, REPO_ROOT))

    # Artifacts are exchanged between modules by bare file name.
    os.chdir(OUT_DIR)
    return manifest


def get_api_key(name):
    """
    Read an LLM credential from the environment.

    Keys are never stored in the repository. Set them in your shell before
    running module 05:

        export GROQ_API_KEY="..."          # Linux / macOS
        setx GROQ_API_KEY "..."            # Windows
    """
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            "%s is not set.\n"
            "Export it in your environment before running this module; "
            "credentials are deliberately not stored in this repository.\n"
            "See docs/reproduction_instructions.md, section 'LLM access'."
            % name)
    return value
