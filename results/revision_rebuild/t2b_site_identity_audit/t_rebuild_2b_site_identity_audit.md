# T-REBUILD-2B Site-Identity Audit

Worker: claude-1. Date: 2026-07-09. Phase: research/audit only (no manuscript writing).
Method: empirical numeric cross-match + independent AquaCrop reproduction (read-only). Filenames were NOT trusted as evidence.

## Headline verdict

**Table 4/5 core (the scenario answer key) is CLEAN — it traces to the confirmed Gimje/Hampyeong sites, not the initial Chungnam/Jeonnam candidates. The 2B hard-stop condition (a mismatch touching Table 4/5 core values) is NOT triggered.**

The only site-identity contamination found is the missing-weather stress test (`stress_test_missing_weather.csv`, manuscript Section 5.5.2), which is reproduced by legacy **Chungnam 2019** weather. This was already identified in the prior STOP report and does not touch any Table 4/5 value; it is remediated by the T-REBUILD-2A Gimje recomputation.

## Evidence

### 1. Scenario table = Table 4/5 core -> CONFIRMED (decisive)
The scenario CSV records `grow_precip_mm`, which equals the growing-season (May-Sep) precipitation of the weather actually used. For all six site-years the value matches the confirmed weather file exactly (to 0.1 mm) and differs sharply from the initial candidate weather:

| site-year | scenario grow_precip | confirmed (Gimje/Hampyeong) May-Sep | initial (Chungnam/Jeonnam) May-Sep | traces to |
|---|---:|---:|---:|---|
| Gimje 2015 | 402.6 | 402.6 | (no 2015 candidate) | CONFIRMED |
| Gimje 2019 | 675.0 | 675.0 | 512.9 | CONFIRMED |
| Gimje 2022 | 736.1 | 736.1 | 1278.3 | CONFIRMED |
| Hampyeong 2015 | 577.9 | 577.9 | (no 2015 candidate) | CONFIRMED |
| Hampyeong 2019 | 823.8 | 823.8 | 1105.2 | CONFIRMED |
| Hampyeong 2022 | 723.6 | 723.6 | 686.3 | CONFIRMED |

Corroboration: the verified T1 harness (`scripts/t_rebuild_1_scenario_harness.py`, line 103) reads `weather_aquacrop_{case1_gimje|case2_hampyeong}_{year}.csv` and passed 30/30 against this CSV. Both the input-side (precip identity) and the reproduction-side (T1 pass) agree.

### 2. Soil sensitivity -> CONFIRMED Gimje
Independent reproduction (AquaCrop 3.0.12, newproj): default-ClayLoam PaddyRice rainfed 2019 on **Gimje** weather = **6.3214** t/ha, which equals the saved `sensitivity_soil_params.csv` base rainfed 6.321. On Chungnam weather the same run gives 6.7040. So the soil sensitivity file is Gimje. (Section 5.5.1; not a Table 4/5 value.)

### 3. Missing-weather stress test -> INITIAL Chungnam (contaminated, but not Table 4/5)
Independent reproduction: default-ClayLoam rainfed 2019 on **Chungnam** weather = **6.7040** t/ha = saved `stress_test_missing_weather.csv` normal rainfed 6.704 (Gimje gives 6.321). The saved gapped-weather file is the same Chungnam series with Jul 15-28 removed. This is the exact finding of the prior STOP report and is confined to Section 5.5.2. Remediation = regenerate on true Gimje via T-REBUILD-2A.

### 4. Section 5.3 Pareto fronts -> CONFIRMED sites (site identity clean)
Fronts are assigned by their minimum (rainfed-equivalent) yield anchor:
- `gimje_2019_soilcorrected`: min yield 6.142 = SoilGrids Gimje 2019 rainfed -> CONFIRMED Gimje (this is the Section 5.3-cited front).
- `hampyeong_2015`: min yield 6.016 = scenario Hampyeong 2015 rainfed -> CONFIRMED Hampyeong.
- `hampyeong_2022`: min yield 7.295; the Jeonnam-2022 front min is 6.751, so site = Hampyeong. The 7.295/WP 1.008 vs scenario 7.233/WP 1.000 is a default-vs-SoilGrids soil-parameter nuance already documented in T-REBUILD-0, NOT a site mismatch.
- `gimje_2015`: no 2015 Chungnam candidate exists; site unambiguous.
- `chungnam_2019` (min 6.704) and `jeonnam_2022` (min 6.751): legacy INITIAL-site fronts that exist in the folder but are NOT cited by Section 5.3 (superseded by the confirmed fronts). No action beyond noting they are legacy.

## Mismatch summary

| output | mismatch | touches Table 4/5 core | disposition |
|---|---|---|---|
| scenario_results_soilgrids_corrected.csv | none | yes (is the core) | clean |
| sensitivity_soil_params.csv | none | no (5.5.1) | clean, Gimje |
| stress_test_missing_weather.csv | CHUNGNAM not Gimje | no (5.5.2) | already STOP'd; regenerate via 2A |
| Section 5.3 fronts (gimje_2019_soilcorrected, hampyeong_2015/2022, gimje_2015) | none (site) | no (5.3 prose) | clean; hampyeong_2022 has known soil-param caveat |
| chungnam_2019 / jeonnam_2022 fronts | legacy, uncited | no | ignore legacy |

## Recommendation

- Table 4/5 core is NOT contaminated -> the 2B hard-stop on Table 4/5 grounds is NOT triggered.
- The single contamination (`stress_test_missing_weather.csv`, Chungnam) is contained to Section 5.5.2 and is the exact item T-REBUILD-2A regenerates on the true Gimje site. It does not block 2C on Table 4/5 grounds.
- Proceeding to 2C is a codex-0/human sequencing decision and is conditional on 2A completing the Gimje missing-weather recomputation; 2B raises no new Table 4/5 blocker.

## Residual risk / limits
- Pareto front site identity is inferred from the rainfed-yield anchor (min-yield) cross-match, not from re-running the optimizer (optimizer reconstruction is out of scope per the plan). The anchor match is unambiguous here because confirmed vs initial rainfed yields differ by >0.3 t/ha, but this is a numeric cross-match, not a full front reproduction.
- The hampyeong_2022 front default-vs-SoilGrids 7.295/7.233 nuance is a pre-existing documented caveat, re-confirmed as non-site; if a reviewer treats Section 5.3 prose numbers strictly, that nuance (not site identity) is the item to reconcile in T-REBUILD-3.
- OM/soil for the confirmed-site scenario is the retained human-locked FC/WP (0.306/0.18, 0.322/0.19); not revisited here.
