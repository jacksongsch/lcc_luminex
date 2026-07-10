# Soluble immune factor profiles in blood and CSF associated with LRRK2 mutations and Parkinson's disease

Jaffery R, Zhao Y, Ahmed S, Schumacher JG, Ahn J, Shi L, Wang Y, Tan Y,
Chen K, Tawbi H, Wang J, Schwarzschild MA, Peng W, Chen X.
*npj Parkinson's Disease.* 2025;11:365.

**Published article:** [doi:10.1038/s41531-025-01215-5](https://doi.org/10.1038/s41531-025-01215-5)

---

## Overview

Mutations in *LRRK2*, a leading genetic cause of Parkinson's disease
(PD), are linked to immune dysregulation, but peripheral and central
immune profiles remain incompletely defined. Using serum samples (n=651)
and matched CSF samples (n=129) from *LRRK2* mutation carriers and
non-carriers with and without PD, we assessed 65 cytokines, chemokines,
growth factors, and soluble receptors by Luminex immunoassay.

*LRRK2* mutations were associated with significantly elevated serum
levels of SDF-1α and TNF-RII after correction for multiple comparisons,
while CSF markers such as BAFF, CD40L, and IL-27 were nominally reduced.
PD was associated with nominally lower levels of inflammatory analytes
in CSF regardless of *LRRK2* status, with minimal changes in serum.
Correlation analyses revealed distinct immune profiles between serum and
CSF, suggesting compartmentalized immune responses.

A systematic literature review using GPT-4o-assisted extraction from
PubMed was performed to contextualize cytokine–LRRK2–PD associations
across the published literature.

## Repository Structure

```
lrrk2_immune/
├── README.md
├── LICENSE                                Apache License 2.0
├── CITATION.cff
├── .gitignore
│
└── analysis/
    ├── lrrk2_parkinson_extraction.py      PubMed search + GPT-4o extraction pipeline
    ├── gpt_prompt.py                      Prompt engineering for cytokine extraction
    ├── post_analysis.py                   Post-processing and visualization (Python)
    └── bubble_plot.R                      Bubble plot figure generation (R)
```

## Analysis Overview

**lrrk2_parkinson_extraction.py** — automated PubMed literature search
and GPT-4o-assisted extraction of cytokine–LRRK2–PD associations from
full-text articles. Queries PubMed via Entrez, retrieves full text from
PMC, and uses structured GPT-4o prompts to extract cytokine name,
disease type, host, measurement site, LRRK2 association direction,
variant, and statistical significance.

**gpt_prompt.py** — prompt engineering module defining the system prompt,
user prompt template, and structured JSON output schema for GPT-4o
extraction.

**post_analysis.py** — post-processing of LLM outputs: filtering by
article type, computing association counts, and generating bubble plots
of cytokine–PD associations across all hosts and human-only studies.

**bubble_plot.R** — R script for LCC serum/CSF Luminex data
visualization.

## Requirements

- Python ≥ 3.10 with: openai, pandas, biopython, seaborn, matplotlib
- R with: ggplot2 (for bubble_plot.R)
- OpenAI API key (set as `OPENAI_API_KEY` environment variable)
- NCBI Entrez email (set as `ENTREZ_EMAIL` environment variable)

## Data Sources

- **LRRK2 Cohort Consortium (LCC):** Serum and CSF Luminex data.
  Available at [michaeljfox.org](https://www.michaeljfox.org)
  (RRID: SCR_020044).
- **PubMed/PMC:** Literature search via NCBI Entrez API.

## Citation

```bibtex
@article{jaffery2025lrrk2,
  title   = {Soluble immune factor profiles in blood and {CSF}
             associated with {LRRK2} mutations and {Parkinson's}
             disease},
  author  = {Jaffery, Roshni and Zhao, Yuhang and Ahmed, Sarfraz
             and Schumacher, Jackson G. and Ahn, Jae and Shi, Leilei
             and Wang, Yujia and Tan, Yukun and Chen, Ken
             and Tawbi, Hussein and Wang, Jian
             and Schwarzschild, Michael A. and Peng, Weiyi
             and Chen, Xiqun},
  journal = {npj Parkinson's Disease},
  volume  = {11},
  pages   = {365},
  year    = {2025},
  doi     = {10.1038/s41531-025-01215-5}
}
```

## Acknowledgements

This research was funded in part by Aligning Science Across Parkinson's
ASAP-000312 through the Michael J. Fox Foundation for Parkinson's
Research (MJFF) and NIH grant R01NS102735. Data were obtained from the
LRRK2 Cohort Consortium (LCC) via the Michael J. Fox Foundation.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE).

## Contact

Jackson G. Schumacher — [jgschumacher@mgh.harvard.edu](mailto:jgschumacher@mgh.harvard.edu)
