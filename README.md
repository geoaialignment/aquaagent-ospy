# AquaAgent-OSPy

Companion code and reproducibility artifacts for:

> **AquaAgent-OSPy: An Auditable LLM Tool-Agent System for Simulation-Grounded Irrigation Decision Support**
> Eungyu Park, Taeyu Kim, Jangwon Park
> School of Earth System Sciences, Kyungpook National University · GeoAI Alignment, Inc.
> Submitted to *Computers and Electronics in Agriculture* (manuscript COMPAG-D-26-04013).

This repository is **private** and holds the code and processed artifacts behind the
paper. It does not contain the manuscript, submission package, or correspondence.

> **Scope of this repository.** It contains *selected* acquisition, memo, evaluation,
> sensitivity, and benchmark scripts plus the processed scenario and Pareto outputs they
> consume or produce. The primary Korean scenario harness and the NSGA-II optimizer
> source are **not included** — see "What is not included" below.

## What the system is

AquaAgent-OSPy is an **A4-class code-executing LLM tool-agent** for irrigation decision
support. The table below describes the *system as reported in the paper*; not every
component's source is in this repository. It orchestrates four capabilities and emits an
auditable *action memo* carrying full tool provenance:

| Capability | Role in the paper |
|---|---|
| AquaCrop-OSPy scenario harness | irrigation strategy simulation (Sec. 4.2) |
| NSGA-II multi-objective optimizer | yield/water trade-off Pareto fronts (Sec. 4.3) |
| Google Earth Engine site verification | land cover + Sentinel-1 SAR phenology check (Sec. 4.4) |
| Illustrative seasonal-irrigation safety checker | flags high-irrigation strategies (Sec. 4.5) |

It is explicitly **not** an A5 irrigation-control agent. The agent recommends; a human
agronomist approves and executes. Nothing here actuates irrigation.

## Study design

Two confirmed Korean paddy rice sites — Gimje (Jeollabuk-do) and Hampyeong
(Jeollanam-do) — across three contrasting climate years spanning 403–824 mm
May–September growing-season precipitation. Memo faithfulness was scored with a
five-item binary rubric (F1–F5). The rubric result reported in the paper is a **pilot
unit-audit of memo traceability, not a statistical reliability estimate for LLM
behavior**.

## Repository layout

```
scripts/                 13 selected scripts: data acquisition, site selection, GEE
                         verification, memo generation, memo faithfulness evaluation and
                         adversarial audit, ETo sensitivity, and the Nebraska benchmark
experiments/
  case_registry.yml      canonical case definitions (Sec. 3.3)
  memos/                 generated LLM action memos (Sec. 5.4)
data/processed/          weather forcing, scenario results, Pareto fronts, tool traces,
                         memo evaluations, adversarial audit inputs
results/revision_rebuild/ independent rebuild/verification outputs from the revision round
requirements.txt         pinned dependencies
PROVENANCE.md            what was included, excluded, and modified for publication
```

Of the included scripts, only `run_pm_eto_sensitivity.py` (Gimje ETo sensitivity) and
`run_nebraska_maize_benchmark.py` (Nebraska generalization benchmark) call
`AquaCropModel` directly; both are auxiliary analyses rather than the primary Korean
scenario runs.

## What is not included

- **The primary Korean scenario harness.** The batch runner that produced the main
  Gimje/Hampyeong scenario tables is not in this repository. Its outputs are included
  under `data/processed/` (`scenario_results_*.csv`).
- **The NSGA-II optimizer source.** No optimizer implementation is present and `pymoo`
  is not imported by any included script. The optimizer's outputs are included as
  `data/processed/pareto_front_*.csv`, and `generate_action_memo.py` *reads* those
  pre-computed Pareto fronts rather than computing them.
- Manuscript, submission package, correspondence, and internal coordination material.

These omissions are deliberate and are recorded in `PROVENANCE.md`. Reproducing the
primary scenario and optimization steps from this repository alone is therefore not
currently possible; the released artifacts support inspection of the inputs, the memo
and evaluation pipeline, the sensitivity/benchmark analyses, and the reported outputs.

Weather forcing tables follow the AquaCrop-OSPy input structure
(`Year, Month, Day, MinTemp, MaxTemp, Precipitation, ReferenceET`).

## Environment

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Core pins: `aquacrop==3.0.12`, `pymoo==0.6.1.6`, plus `anthropic`, `earthengine-api`,
`numpy`, `pandas`, `matplotlib`, `pyproj`, `requests`, `pyyaml`.

Two scripts read optional environment overrides instead of hard-coded paths:

- `AQUAAGENT_PROJECT_ROOT` — defaults to the repository root
- `KOREA_GEODATA_ROOT` — local GIS layer directory, not redistributed here

Google Earth Engine steps require your own authenticated Earth Engine project.
Memo generation requires your own LLM API credentials. No credentials are stored in
this repository.

## Data sources

Public open-access datasets only: NASA POWER Daily API, the Google Earth Engine data
catalog, Sentinel-1/Sentinel-2 derived products, ISRIC SoilGrids v2.0, and published
literature benchmarks. Processed tables are included here; raw third-party archives are
not redistributed.

## Scope and limitations

- Advisory system for agronomist review; it does not authorize or actuate irrigation.
- The Thailand comparison (Veerakachen and Raksapatcharawong, 2020) is a plausibility
  check, not Korean field validation.
- Strategy comparisons hold under shared AquaCrop-OSPy modelling assumptions.
- The safety checker threshold is illustrative, not a regulatory standard.

## Citation

See `CITATION.cff`. The paper is under review; no DOI is assigned yet.
