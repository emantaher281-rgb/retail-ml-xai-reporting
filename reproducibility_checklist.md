# Reproducibility Checklist

This document responds to the reproducibility package requested in review. Each
requested item is mapped to the file that provides it, so coverage can be
verified without reading the code first.

---

## 1. Requested items

| # | Requested item | Provided in |
|---|---|---|
| 1 | Exact dataset version / immutable identifier | `data/README.md` (source, version, SHA-256); digest recomputed each run into `outputs/run_manifest_*.json` |
| 2 | Preprocessing and feature-engineering code | `Code/01` (LRFMV aggregation), `Code/04` (temporal features) |
| 3 | Chronological and random split indices | `outputs/split_indices_segmentation.json` (stratified random); chronological cut-off declared in `configuration/forecasting.yaml` and printed by `Code/04` |
| 4 | Random seeds | `SEED = 42` in `src/repro.py`; applied globally and passed explicitly to every estimator |
| 5 | Clustering configuration | `configuration/segmentation.yaml` |
| 6 | Recommender configuration | `configuration/recommendation.yaml` |
| 7 | Hyperparameter search spaces and selected values | `configuration/*.yaml` → `hyperparameters` / `search_space` |
| 8 | Lag / rolling / EMA feature construction | `Code/04`; specification in `configuration/forecasting.yaml` → `feature_engineering` |
| 9 | Training-only aggregation procedures | `configuration/forecasting.yaml` → `leakage_controls`; lag and rolling features are computed on the ordered series and the split is chronological, so no test-window statistic enters a training row |
| 10 | Recommendation candidate and ground-truth generation | `Code/02`; specification in `configuration/recommendation.yaml` → `candidates` / `ground_truth` |
| 11 | Evaluation-metric implementations | Implemented inline in `Code/02` (Precision@K, Recall@K, coverage) and `Code/03`–`Code/04` (RMSE, MAE, R², MAPE); reference values in `results/expected_results.md` |
| 12 | SHAP / LIME evaluation code | `Code/01`, `Code/03`, `Code/04` — fidelity, stability (SNR), and cross-method Spearman rank correlation |
| 13 | Exact structured inputs and prompts for LLaMA-3.3-70B | `prompts/decision_report_prompt.md`; the rendered per-customer context is written to `outputs/` by `Code/05` |
| 14 | Environment specification | `environment.yml`, `requirements.txt`, and the resolved versions captured in every run manifest |
| 15 | Single executable script reproducing all tables | `run_all.py` |

---

## 2. Sources of randomness and how each is fixed

| Component | Mechanism | Value |
|---|---|---|
| Python hashing | `PYTHONHASHSEED` | 42 |
| Python `random` | `random.seed` | 42 |
| NumPy global RNG | `np.random.seed` | 42 |
| Ad-hoc sampling (LIME aggregation, stability) | `np.random.default_rng(SEED)` exposed as `RNG` | 42 |
| PCA | `random_state` | 42 |
| K-Means | `random_state`, `n_init=20` | 42 |
| Fuzzy C-Means | `seed` | 42 |
| Agglomerative clustering | deterministic | n/a |
| Train/test split | `random_state`, stratified | 42 |
| Random Forest | `random_state` | 42 |
| XGBoost | `random_state` | 42 |
| LIME explainers | `random_state` | 42 |
| LLaMA-3.3-70B decoding | provider-side; not controllable | see note below |

Two points worth stating explicitly:

- **`skfuzzy.cmeans` is not deterministic unless `seed=` is passed.** It
  initialises its membership matrix randomly. Any run that omits the seed will
  not reproduce the Fuzzy C-Means and Hybrid rows of the algorithm-comparison
  table exactly. The seed is now passed.
- **LLM output is not bit-reproducible.** Decoding is stochastic and hosted
  model snapshots change. The *inputs* — structured context and prompt
  templates — are fixed and versioned, which is the reproducible part of that
  stage. All quantitative tables come from modules 1–4 and do not depend on the
  LLM.

---

## 3. Verifying the segmentation tables

The per-cluster deviation table and the raw cluster profile table are two views
of the same group means, so their signs must agree. `src/check_tables.py`
reconstructs the customer-weighted global mean from the exported profile table
and asserts the sign of every deviation against it:

```bash
python src/check_tables.py
```

Cluster identity is assigned from the empirical centroids rather than from the
arbitrary integer label returned by K-Means. The derivation is documented in
`docs/cluster_labels.md`.

---

## 4. Credentials

No API keys, tokens, or credentials are stored in this repository. Module 5
reads them from environment variables and fails with an explicit message if
they are absent.
