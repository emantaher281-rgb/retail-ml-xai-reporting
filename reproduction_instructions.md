# Reproduction Instructions

Follow these steps to reproduce every table and figure reported in the paper.

---

## 1. Environment

The reported results were produced with Python 3.11. Use the pinned
environment; `shap` and `scikit-learn` have both changed default behaviour
between minor releases, and a different `shap` version can alter the shape of
the returned SHAP array and therefore the per-class aggregation.

```bash
# option A - conda (recommended: pins the Python version too)
conda env create -f environment.yml
conda activate retail-xai

# option B - pip
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Verify:

```bash
python -c "import numpy, pandas, sklearn, shap, lime, skfuzzy, xgboost; print('ok')"
```

---

## 2. Dataset

Place the file at:

```
data/Customer_Segmentation&Sales_Forecasting_Dataset.csv
```

The permanent identifier, expected SHA-256 digest and licence terms are in
`data/README.md`. Every run recomputes the digest and writes it to
`outputs/run_manifest_*.json`, so a changed input file is detected before it
can silently alter the reported numbers.

---

## 3. LLM access (module 5 only)

Module 5 calls LLaMA-3.3-70B through a hosted API. **Credentials are not
stored in this repository.** Export them in your shell before running it:

```bash
# Linux / macOS
export GROQ_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"     # optional fallback provider

# Windows (PowerShell)
$env:GROQ_API_KEY = "your-key"

# Windows (persistent)
setx GROQ_API_KEY "your-key"
```

Modules 1–4 do not require any credential and reproduce every quantitative
table on their own. Module 5 produces the written decision reports.

Because LLM decoding is stochastic and providers update model snapshots, the
generated report text will not be byte-identical between runs. The structured
inputs and the prompt templates are fixed and versioned in `prompts/`, so the
*inputs* to the model are fully reproducible even though its output text is
not. Reference reports from the run used in the paper are in
`results/expected_results.md`.

---

## 4. Run

```bash
# everything, in order
python run_all.py

# a single module
python run_all.py --module 1

# list modules without running them
python run_all.py --list
```

Modules must run in order: each writes CSV/JSON artifacts the next one reads.
`run_all.py` stops at the first failure so a partial pipeline is never
mistaken for a completed one.

You can also open any notebook directly in Jupyter — the setup cell resolves
all paths relative to the repository, so no path editing is needed.

---

## 5. Where results appear

| Location | Contents |
|---|---|
| `figures/<module>/` | 300-DPI PNG and vector PDF, named from each figure's title |
| `outputs/` | All CSV and JSON artifacts, shared between modules |
| `outputs/run_manifest_*.json` | Seed, package versions, platform, dataset digest |
| `outputs/split_indices_segmentation.json` | Exact train/test indices |

---

## 6. Verify

```bash
python src/check_tables.py
```

This reconstructs the customer-weighted global mean from the exported
per-cluster table, recomputes each deviation, and asserts that every sign
agrees with the raw profile. It exits non-zero on any mismatch, so it can be
wired into CI. Compare the printed values with `results/expected_results.md`.

---

## 7. Known limits on exact reproduction

- **Floating-point non-determinism across platforms.** BLAS threading and
  reduction order can shift the last decimal places of silhouette,
  Davies-Bouldin and Calinski-Harabasz scores. Cluster memberships and all
  values at manuscript precision are stable. Set `OMP_NUM_THREADS=1` for
  tighter agreement.
- **Agglomerative clustering** is deterministic and takes no seed.
- **LLM output text** varies between runs, as explained in section 3.
- **Memory.** The `K = 2…10` agglomerative sweep computes a full linkage over
  all customers and is the heaviest step in module 1.
