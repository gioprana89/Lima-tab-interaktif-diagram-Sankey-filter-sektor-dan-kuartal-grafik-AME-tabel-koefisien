# BEI Profit–Loss Research Dashboard v1.1 (model results, read-only)

## Operating scope
This application is a **display-only** research dashboard built from prior audits and the post-exploratory model specification freeze. It neither re-fits regressions nor performs model selection. All inputs are included in `data/` (existing IDX-derived data only). **No new financial observations** have been collected.

- Default is issuer-level baseline, excluding GOTOM, with 4,463 pairs, 425 recoveries, 388 loss onsets, 7 zero-related pairs.
- Filter sectors and transition endpoint quarters on the sidebar. **Only descriptive tabs 1–3** change with those filters; tab 4 shows full audit; tab 5 always shows locked regression outputs irrespective of filters.
- Baseline bootstrap confidence intervals are shown only with the full issuer-level dataset. They are not re-used for filtered subsets.
- `Excel hasil model` downloads the **fixed 10-sheet, print-ready Excel** used for the paper. For filtered observations, use `CSV pasangan terfilter` and open it in Excel.
- Tabs: Ringkasan (Sankey); Kuartal & Sektor; Ketahanan Recovery; Audit & Sensitivitas; Model Ekonometrika (OR, AME, all sensitivity scenarios).

## Local launch

In the extracted dashboard directory:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. Streamlit is not installed in the creation environment, so the graphical UI has **not** been tested end-to-end here. Pure-Python data audit and syntax checks were performed on the packaged files.

## Inferential boundaries

- `Profit for Period` is treated as YTD, which has **not been independently confirmed across all original statements**.
- P-values are nominal **post-exploratory**, with no causal identification.
- Recovery refers to an accounting-profit sign change, not financial distress or solvency recovery.
- The risk-set outcomes, denominators, and standard-deviation units are different; no direct cross-risk-set OR comparison.
- The short panel, Q4 comparability, source-vintage differences, coverage, and near-zero profits require cautious interpretation.
