# Dataset

## File

```
data/Customer_Segmentation&Sales_Forecasting_Dataset.csv
```

**This file is committed to the repository.** No download or registration is
required: cloning the repository gives you everything needed to reproduce the
reported results.

Transaction-level retail records from the Global Superstore dataset, a widely
used public sample of retail order data covering orders, customers, products,
sales, quantity, discount, profit, and shipping.

## Version identity

The integrity of the file is pinned by digest rather than by a version label,
so any modification is detected automatically.

| Field | Value |
|---|---|
| File name | `Customer_Segmentation&Sales_Forecasting_Dataset.csv` |
| Encoding | `latin-1` |
| Source | A. Mahalingappa, "Global Super Store Dataset", Kaggle, 2020 |
| Original source URL | https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset |
| Retrieved | 30 July 2026 |
| Coverage | January 2014 - December 2017 |
| Records | 9,994 transactions, 793 customers, 17 product sub-categories |
| Licence | `<fill in - check the licence shown on the Kaggle page>` |
| SHA-256 | `<fill in from outputs/run_manifest_customer_segmentation.json>` |

Every run recomputes the SHA-256 and writes it to
`outputs/run_manifest_<module>.json`. Compare that value with the one recorded
above: if they differ, the input file has changed and the reported numbers no
longer correspond to it.

To read the digest after the first run:

```bash
python -c "import json;print(json.load(open('outputs/run_manifest_customer_segmentation.json'))['dataset_sha256'])"
```

## Licence note

Global Superstore is distributed as a sample dataset and is widely
redistributed in public teaching and research repositories. Confirm the terms
attached to the copy you obtained before redistributing it, and record them in
the table above. If redistribution is not permitted for your copy, remove the
CSV from the repository, restore the `data/*.csv` entry in `.gitignore`, and
replace the "file is committed" statement above with download instructions.

## Expected schema

Columns consumed by the pipeline:

| Column | Used for |
|---|---|
| `Customer ID` | customer-level aggregation key |
| `Customer Name`, `Segment`, `City`, `State`, `Region` | descriptive attributes carried into the profile export |
| `Order ID` | Frequency (count of distinct orders) |
| `Order Date`, `Ship Date` | Recency, Length, temporal split, lag/rolling/EMA features |
| `Sales` | Monetary; forecasting target |
| `Quantity` | Volume |
| `Profit`, `Discount` | profitability attributes, external validation |
| `Product ID`, `Product Name`, `Category`, `Sub-Category` | recommendation module |
| `Ship Mode` | derived shipping attributes |

## Preparation

None required. Date parsing, per-customer aggregation, LRFMV construction, and
daily aggregation are all performed inside the notebooks from the raw file.
