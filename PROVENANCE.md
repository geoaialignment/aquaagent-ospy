# Provenance and publication hygiene

This repository is an allowlisted companion to the AquaAgent-OSPy manuscript. It was
assembled by copying from a private research working tree; that source tree was read
only and never modified, staged, or committed from.

## Source of truth

Final clean manuscript identified by content comparison, not filename:
`revision/package/01_Revised_Manuscript_AquaAgent_OSPy.docx` (2026-07-11 16:08).
It supersedes the otherwise byte-similar `Park et al., COMPAG, 2026.docx` copies by two
substantive hunks: a trimmed keyword list and an expanded competing-interest disclosure.

## Code scope actually published

Verified by inspection of the committed tree, not by intent:

- 13 Python scripts are included: acquisition (`fetch_weather_nasa_power.py`,
  `fetch_open_access_pdfs.py`), site selection and GIS inventory
  (`select_korea_candidate_sites.py`, `inventory_gis_korea_geodata.py`), GEE verification
  (`run_gee_extended_validation.py`), memo generation and evaluation
  (`generate_action_memo.py`, `evaluate_memo_faithfulness.py`,
  `run_memo_adversarial_audit.py`), sensitivity and benchmark analyses
  (`run_pm_eto_sensitivity.py`, `run_nebraska_maize_benchmark.py`), figure generation
  (`make_figures.py`, `make_graphical_abstract.py`), and an import gate
  (`check_aquacrop_ospy_import.py`).
- `AquaCropModel` is called only by `run_pm_eto_sensitivity.py` and
  `run_nebraska_maize_benchmark.py`.
- **No included script imports `pymoo`**, and no NSGA-II optimizer implementation is
  present. `generate_action_memo.py` reads pre-computed Pareto fronts.
- The primary Korean scenario harness is not present either. A search of the source
  working tree found no `pymoo` import anywhere in it, so the optimizer source lives
  outside the tree this repository was assembled from; it was not withheld selectively.

The README and `scripts/README.md` were corrected on 2026-08-01 to state this scope
explicitly after an independent review found they implied a runnable harness and
optimizer were included.

## What is intentionally absent

No manuscript or submission documents (DOCX/PDF), cover or reply letters, journal
decision files, reviewer correspondence, private reference PDFs, internal coordination
notes, task plans, agent transcripts, credentials, or `.git` history from the source
tree. No license or DOI is asserted, because neither has been chosen or issued.

## Modifications made for publication

Only private absolute paths were changed. No algorithmic code was altered.

- `scripts/fetch_weather_nasa_power.py` — 3 replacement(s): private absolute path constants replaced with repo-relative defaults (AQUAAGENT_PROJECT_ROOT / KOREA_GEODATA_ROOT overrides); no algorithmic code altered
- `scripts/inventory_gis_korea_geodata.py` — 3 replacement(s): private absolute path constants replaced with repo-relative defaults (AQUAAGENT_PROJECT_ROOT / KOREA_GEODATA_ROOT overrides); no algorithmic code altered
- `scripts/run_nebraska_maize_benchmark.py` — 1 replacement(s): private absolute path constants replaced with repo-relative defaults (AQUAAGENT_PROJECT_ROOT / KOREA_GEODATA_ROOT overrides); no algorithmic code altered
- `scripts/run_pm_eto_sensitivity.py` — 1 replacement(s): private absolute path constants replaced with repo-relative defaults (AQUAAGENT_PROJECT_ROOT / KOREA_GEODATA_ROOT overrides); no algorithmic code altered
- `scripts/select_korea_candidate_sites.py` — 5 replacement(s): private absolute path constants replaced with repo-relative defaults (AQUAAGENT_PROJECT_ROOT / KOREA_GEODATA_ROOT overrides); no algorithmic code altered
- `scripts/README.md` — 1 replacement(s): local interpreter absolute path replaced with a generic instruction

Scripts now resolve paths from the repository root, with optional overrides
`AQUAAGENT_PROJECT_ROOT` and `KOREA_GEODATA_ROOT`.

## Exclusions

**contains a private absolute local path** (13)
- `data/processed/geodata_inventory.csv`
- `data/processed/input_provenance.json`
- `data/processed/memo_evaluation_case2_r3.csv`
- `data/processed/memo_evaluation_r3_clean.csv`
- `data/processed/memo_evaluation_r4_fixed.csv`
- `data/processed/memo_evaluation_r5_strict.csv`
- `revision/research/rebuild/outputs/t1_scenario_harness/T-REBUILD-1_scenario_harness_report.md`
- `revision/research/rebuild/outputs/t2_sensitivity_gate/T-REBUILD-2_sensitivity_gate_report.md`
- `revision/research/rebuild/outputs/t2a_missing_weather_gimje/t_rebuild_2a_missing_weather_gimje.csv`
- `revision/research/rebuild/outputs/t2a_missing_weather_gimje/t_rebuild_2a_missing_weather_gimje.md`
- `revision/research/rebuild/outputs/t2c_six_site_year_extension/t_rebuild_2c_six_site_year_extension.md`
- `revision/research/rebuild/outputs/t5_numeric_site_consistency/t_rebuild_5_numeric_site_consistency.md`
- `revision/research/rebuild/outputs/t_rebuild_2a_missing_weather_gimje.csv`

**embeds ~29,099 characters of manuscript prose (including the abstract and the corresponding-author line); manuscript content in code form** (1)
- `scripts/build_paper_docx.py`

**excluded by the authors' own .gitignore (raw weather pulls)** (4)
- `data/processed/weather_nasa_power_case1_chungnam_2019.csv`
- `data/processed/weather_nasa_power_case1_chungnam_2022.csv`
- `data/processed/weather_nasa_power_case2_jeonnam_2019.csv`
- `data/processed/weather_nasa_power_case2_jeonnam_2022.csv`

**explicitly superseded revision output** (2)
- `revision/research/rebuild/outputs/t2c_six_site_year_extension_superseded_20260709/t_rebuild_2c_level_verdicts.csv`
- `revision/research/rebuild/outputs/t2c_six_site_year_extension_superseded_20260709/t_rebuild_2c_sensitivity_extension_report.md`

**superseded/rejected site material per the authors' .gitignore** (10)
- `data/processed/pareto_front_case1_chungnam_2019.csv`
- `data/processed/pareto_front_case2_jeonnam_2022.csv`
- `data/processed/scenario_results_case3_spain_cotton.csv`
- `data/processed/scenario_results_case3_tunis_wheat.csv`
- `data/processed/tool_trace_case1_chungnam_2019.json`
- `data/processed/tool_trace_case2_jeonnam_2022.json`
- `data/processed/weather_aquacrop_case1_chungnam_2019.csv`
- `data/processed/weather_aquacrop_case1_chungnam_2022.csv`
- `data/processed/weather_aquacrop_case2_jeonnam_2019.csv`
- `data/processed/weather_aquacrop_case2_jeonnam_2022.csv`

## Secret and privacy scan resolutions

- **email address egpark@knu.ac.kr** — file removed from the repository (manuscript prose embedded); finding no longer present
- **email address open-access-fetch@example.com** — benign placeholder contact in a polite HTTP User-Agent; example.com is an RFC 2606 reserved domain and is not a private address; retained

## Inclusion summary

- allowlisted files copied: 89
- files sanitized before copying: 6
- files excluded: 30

Rejected-site weather and Pareto CSVs are omitted in line with the authors' own
`.gitignore`, which marks them as old rejected site data. The corresponding action
memos are retained because the site-correction episode is part of the paper's
Google Earth Engine verification result (Sec. 5.1).

