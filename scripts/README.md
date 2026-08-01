# Scripts

Scripts in this directory should be runnable research steps, not one-off notebook fragments.

## Environment

Use:

```bash
python  # any environment satisfying requirements.txt
```

The default Homebrew Python 3.14 does not currently import `aquacrop`.

## Current Scripts

| script | purpose | status |
|---|---|---|
| `check_aquacrop_ospy_import.py` | Gate 0 diagnostic for `aquacrop` import and crop names | working |
| `inventory_gis_korea_geodata.py` | build `data/processed/geodata_inventory.csv` and Gate 1 inventory log | working |
| `select_korea_candidate_sites.py` | build seed candidate-site CSV and soil texture mapping; refuses to overwrite production case registry | working |
| `fetch_weather_nasa_power.py` | fetch NASA POWER daily weather with provenance for AquaCrop forcing bootstrap | working |
| `run_gee_extended_validation.py` | re-check retained/rejected sites with Dynamic World, WorldCover, Sentinel-2 NDVI, and JRC water occurrence | working |
| `fetch_open_access_pdfs.py` | reference acquisition helper | existing |

## Planned Scripts

| script | purpose |
|---|---|
| `build_aquacrop_case_inputs.py` | weather/soil/crop/management configs |
| `run_aquacrop_scenarios.py` | strategy/scenario batch runs |
| `evaluate_memo_faithfulness.py` | F1-F5 memo scoring and claim extraction |

## Script Contract

Each script should:

1. accept explicit input/output paths,
2. write a machine-readable output,
3. write or update a human-readable run log,
4. record software versions and source paths,
5. fail loudly when required data are missing.
