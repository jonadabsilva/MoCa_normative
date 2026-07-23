# MoCA Normative Calculator (Streamlit Version)

This is a web application built in Python using Streamlit, designed to calculate normalized Z-scores and percentiles for the Montreal Cognitive Assessment (MoCA).

The normative data driving this calculator is strictly sourced from:
**Rossetti, H. C., Lacritz, L. H., Cullum, C. M., & Weiner, M. F. (2011). Normative data for the Montreal Cognitive Assessment (MoCA) in a population-based sample. *Neurology*, 77(13), 1272-1275.** ([doi:10.1212/WNL.0b013e318230208a](https://doi.org/10.1212/WNL.0b013e318230208a))

## Features
* **Individual Assessment**: Enter a patient's exact age (18–85), education tier, and MoCA raw score. The app maps the age to the correct normative bracket automatically and calculates the expected mean/SD, Z-score, percentile, and descriptive classification, along with a probability-density plot.
* **Batch Processing**: Upload a CSV of raw scores to score an entire dataset at once. Rows can specify either an `Age_Bracket` (e.g. `60-70`) or a numeric `Age` (mapped to the nearest bracket automatically). Rows that cannot be scored are flagged individually in a `Note` column instead of failing silently, and the results are exportable as CSV.

### Age brackets
The source table uses overlapping 10-year age bins, each centered on a midpoint. The app resolves an exact age to the single nearest bracket, so you never have to guess which overlapping bin applies:

| Bracket | Center age |
|---------|-----------|
| `<35`   | 30 |
| `30-40` | 35 |
| `35-45` | 40 |
| `40-50` | 45 |
| `45-55` | 50 |
| `50-60` | 55 |
| `55-65` | 60 |
| `60-70` | 65 |
| `65-75` | 70 |
| `70-80` | 75 |

Education tiers are `<12`, `12`, and `>12` years completed.

## Usage (Local)
To run this app locally, ensure you have Python 3.9+ installed.

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```
4. Streamlit will open the app in your browser (default: http://localhost:8501).

## Disclaimer
This tool is intended for research and educational use. Norm-referenced scores support, but do not replace, clinical judgment and are not diagnostic. As Rossetti et al. (2011) note, the conventional `<26` cutoff has a high false-positive rate in the general population; this calculator reports demographically adjusted percentiles to aid interpretation.
