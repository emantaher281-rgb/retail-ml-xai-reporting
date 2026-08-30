# Leveraging Machine Learning and Explainable AI for Enhanced Business Decision-Making in Retail

This repository provides the reproducibility materials for the paper:

**Leveraging Machine Learning and Explainable AI for Enhanced Business Decision-Making in Retail**

The framework combines customer segmentation, product recommendation,
product-level and daily sales forecasting, explainable AI (SHAP and LIME), and
an LLM reporting layer that converts model outputs and explanations into
written decision reports. The repository supports full reproduction of every
reported table and figure: preprocessing and feature engineering, split
indices, random seeds, clustering and recommender configurations,
hyperparameter settings, evaluation metrics, SHAP/LIME evaluation code, and
the exact structured inputs and prompts supplied to LLaMA-3.3-70B.

## Repository Contents

```
Retail-ML-XAI-LLM/
│
├── README.md
├── MANIFEST.md                    # claim-to-file index for the paper
├── CITATION.cff
├── LICENSE
├── requirements.txt
├── environment.yml
├── run_all.py                     # single entry point: reproduces all tables
├── verify_package.py              # audits the package before every push
│
├── Code/
│   ├── 01_customer_segmentation.ipynb
│   ├── 02_product_recommendation.ipynb
│   ├── 03_product_level_sales_prediction.ipynb
│   ├── 04_daily_sales_forecasting.ipynb
│   └── 05_llm_decision_report.ipynb
│
├── src/
│   ├── repro.py                   # seeds, paths, environment manifest, figure export
│   └── check_tables.py            # automated table-consistency verification
│
├── configuration/
│   ├── segmentation.yaml
│   ├── recommendation.yaml
│   ├── forecasting.yaml
│   └── llm_reporting.yaml
│
├── prompts/
│   └── decision_report_prompt.md  # exact system and user prompt templates
│
├── data/
│   ├── Customer_Segmentation&Sales_Forecasting_Dataset.csv   # included
│   └── README.md                  # provenance, digest, licence, schema
│
├── results/
│   └── expected_results.md        # reference values for verifying a run
│
├── figures/                       # generated on run
├── outputs/                       # generated on run
│
└── docs/
    ├── reproduction_instructions.md
    ├── reproducibility_checklist.md
    └── cluster_labels.md
```

## Pipeline

The five modules must be run in order. Each writes the CSV and JSON files that
the next one reads.

| Module | Notebook | Produces |
|---|---|---|
| 1 | `01_customer_segmentation.ipynb` | LRFMV features, PCA, K-Means / Agglomerative / Fuzzy C-Means / Hybrid clustering, cluster validity tests, segmentation SHAP and LIME |
| 2 | `02_product_recommendation.ipynb` | Cluster-based, user-user CF, item-item CF, and association-rule recommenders with XAI comparison |
| 3 | `03_product_level_sales_prediction.ipynb` | Product-level sales prediction and its SHAP/LIME explanations |
| 4 | `04_daily_sales_forecasting.ipynb` | Lag / rolling / EMA features, five forecasting models, forecasting XAI |
| 5 | `05_llm_decision_report.ipynb` | Structured per-customer context, prompts, and LLaMA-3.3-70B decision reports |

## Quick Start

```bash
git clone https://github.com/<username>/Retail-ML-XAI-LLM.git
cd Retail-ML-XAI-LLM

# environment (conda pins the Python version as well)
conda env create -f environment.yml
conda activate retail-xai
# or:  pip install -r requirements.txt

# the dataset is already in data/ - nothing to download

# reproduce everything (modules 1-4 need no API credentials)
python run_all.py --skip-llm

# verify the reported tables
python src/check_tables.py

# audit the package itself
python verify_package.py
```

Full instructions, including LLM credential setup for module 5, are in
`docs/reproduction_instructions.md`.

## Reproducibility

A single seed (`SEED = 42`) governs every stochastic component and is passed
explicitly to PCA, K-Means, Fuzzy C-Means, the stratified split, the Random
Forest, XGBoost, and the LIME explainers. The dataset is pinned by SHA-256
digest, recomputed on every run and written to `outputs/run_manifest_*.json`
together with the resolved package versions.

Figures are written automatically to `figures/<module>/` as 300-DPI PNG and
vector PDF, named after each figure's own title.

`docs/reproducibility_checklist.md` maps every item requested in review to the
file that satisfies it.

## Data Availability

The dataset is committed to this repository at
`data/Customer_Segmentation&Sales_Forecasting_Dataset.csv`, so cloning gives you
everything needed to reproduce the reported results with no download step. Its
provenance, SHA-256 digest, licence, and schema are documented in
`data/README.md`. Every run recomputes the digest into
`outputs/run_manifest_*.json`, so a modified input file is detected before it
can silently change the results.

## Verifying the Package

```bash
python verify_package.py
```

Checks that every required item is present, that no notebook carries stored
execution output, and that no credential appears anywhere in the tree. Exits
non-zero on failure, so it can be wired into CI. `MANIFEST.md` maps each claim
in the paper's reproducibility statement to the file that supports it.

## Citation

If you find this work helpful in your research, please cite our paper:

```bibtex
@article{retail_ml_xai_2026,
  author  = {<Author list>},
  title   = {Leveraging Machine Learning and Explainable AI for Enhanced
             Business Decision-Making in Retail},
  journal = {The International Journal of Intelligent Engineering and Systems},
  year    = {2026},
  doi     = {Pending}
}
```

## License

Released under the MIT License (see `LICENSE`). The dataset carries its own
terms of use.
