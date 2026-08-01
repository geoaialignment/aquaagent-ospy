# Scripts

Scripts in this directory should be runnable research steps, not one-off notebook fragments.

## Environment

Use:

```bash
python  # any environment satisfying requirements.txt
```

The default Homebrew Python 3.14 does not currently import `aquacrop`.

## Included Scripts

All 13 scripts below are present in this repository and pass a `--help` / syntax check.

| script | purpose |
|---|---|
| `check_aquacrop_ospy_import.py` | Gate 0 diagnostic for the `aquacrop` import and crop names |
| `inventory_gis_korea_geodata.py` | build `data/processed/geodata_inventory.csv` and the Gate 1 inventory log |
| `select_korea_candidate_sites.py` | build the seed candidate-site CSV and soil texture mapping; refuses to overwrite the production case registry |
| `fetch_weather_nasa_power.py` | fetch NASA POWER daily weather with provenance for AquaCrop forcing |
| `fetch_open_access_pdfs.py` | reference acquisition helper |
| `run_gee_extended_validation.py` | re-check retained/rejected sites with Dynamic World, WorldCover, Sentinel-2 NDVI, and JRC water occurrence |
| `generate_action_memo.py` | action memo generation; reads pre-computed Pareto fronts from `data/processed/` |
| `evaluate_memo_faithfulness.py` | F1-F5 memo faithfulness rubric scoring |
| `run_memo_adversarial_audit.py` | adversarial audit of the memo faithfulness rubric |
| `run_pm_eto_sensitivity.py` | Penman-Monteith vs Hargreaves-Samani ETo sensitivity (Gimje 2019); calls `AquaCropModel` |
| `run_nebraska_maize_benchmark.py` | Nebraska maize generalization benchmark; calls `AquaCropModel` |
| `make_figures.py` | quantitative figure generation from processed outputs |
| `make_graphical_abstract.py` | graphical abstract policy guard |

## Not Included

The primary Korean scenario harness (the batch runner behind
`data/processed/scenario_results_*.csv`) and the NSGA-II optimizer that produced
`data/processed/pareto_front_*.csv` are **not** in this repository. No included script
imports `pymoo`. Their outputs are included as data products; their source is not.

## Script Contract

Each script should:

1. accept explicit input/output paths,
2. write a machine-readable output,
3. write or update a human-readable run log,
4. record software versions and source paths,
5. fail loudly when required data are missing.
