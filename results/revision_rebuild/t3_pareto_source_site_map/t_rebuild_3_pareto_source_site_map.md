# T-REBUILD-3 Pareto Source-Site Map (data-only)

Worker: claude-1. Date: 2026-07-09. Phase: data-only characterization. No manuscript prose. No fabricated convergence history or hypervolume (not saved).

## Scope and method
- Confirmed-site fronts only for interpretation: `pareto_front_case1_gimje_2015`, `pareto_front_case1_gimje_2019_soilcorrected`, `pareto_front_case2_hampyeong_2015`, `pareto_front_case2_hampyeong_2022`. Legacy `chungnam_2019`/`jeonnam_2022` fronts are NOT used (uncited; T2B site audit).
- Each saved front read directly and characterized (range, best-WP row, near-optimal SMT band). Section 5.3 prose quoted exactly from the submitted manuscript and mapped to saved-front value, scenario-table value, site traced to, and corrected front-consistent value.
- Full row-level mapping in `t_rebuild_3_pareto_source_site_map.csv`.

## Fixed optimizer settings (documented, §4.3)
- Decision vars: SMT 10-90%, MaxIrr 10-80 mm. Objectives: f1 = -yield, f2 = seasonal irrigation.
- NSGA-II, population 30, generations 30 -> 900 function evaluations. Four site-years.
- Each saved front CSV holds 30 rows (final population), consistent with pop=30.
- `save_history` was NOT enabled; no hypervolume/convergence trajectory exists. Per instruction, this map does NOT fabricate one. (Consistent with the earlier T2 NSGA diagnostic BLOCKER.)

## Best-WP SMT band localization (data-only)
| site-year | best-WP SMT | best-WP (MaxIrr, yield, irr, WP) | within-2%-of-maxWP SMT band |
|---|---:|---|---|
| Gimje 2015 | 40.0 | 39.5, 6.200, 116.2, 1.195 | 40.0-61.5 (n=6) |
| Gimje 2019 | 40.1 | 16.5, 6.740, 49.4, 0.930 | 25.6-60.5 (n=17) |
| Hampyeong 2015 | 57.7 | 12.4, 6.961, 61.9, 1.088 | 32.6-66.2 (n=14) |
| Hampyeong 2022 | 54.0 | 30.0, 7.295, 0.0, 1.008 | 50.4-66.6 (n=9) |

- The §5.3 claim "best-WP fell in the SMT 40-60% range" HOLDS for the best-WP POINTS (40.0/40.1/57.7/54.0 all lie in 40-60).
- Scope note (not an error): the near-optimal band within 2% of max WP is WIDER than 40-60% at three of four sites (down to 25.6% at Gimje 2019, up to 66.6% at Hampyeong 2022). So "40-60%" is a best-WP-point statement, not a claim that all near-optimal solutions are confined to 40-60%.

## Section 5.3 numeric-claim map (anomalies)

### Gimje 2015 — SCENARIO EXTREMA MIXED INTO FRONT RANGE
- §5.3: "Pareto front spanned 0-287 mm ... and 3.856-7.168 t/ha."
- Saved front actual range: irrigation 35.3-267.2 mm; yield 4.475-7.179 t/ha.
- The narrated 0 mm / 287 mm / 3.856 t/ha are SCENARIO-table extrema (Gimje 2015 rainfed irr 0 / yield 3.856; full_SMT80 irr 286.9 / yield 7.168), not Pareto-front extrema.
- best-WP row (SMT 40, MaxIrr 39.5, 6.2, 116.2, WP 1.195) matches the saved front exactly.
- Corrected front-consistent range: 35.3-267.2 mm; 4.475-7.179 t/ha. Site: CONFIRMED Gimje.

### Gimje 2019 — CLEAN
- §5.3 range 0-212.8 mm; 6.142-7.332 t/ha; best-WP SMT 40.1/MaxIrr 16.5/6.740/49.4/0.930; max-yield 7.332/212.8 all MATCH the saved SoilGrids-corrected front. Site: CONFIRMED Gimje. No change.

### Hampyeong 2015 — FRONT-ROW VALUE MISQUOTED
- §5.3 best-WP: "SMT = 57.7% and MaxIrr = 25 mm, producing 6.4 t/ha yield, 61.9 mm irrigation, WP = 1.088."
- Saved front best-WP row: SMT 57.7, MaxIrr 12.4, yield 6.961, irr 61.9, WP 1.088.
- SMT / irrigation (61.9) / WP (1.088) / range (0-138.4) match. MaxIrr 25 vs saved 12.4 and yield 6.4 vs saved 6.961 do NOT match (6.4 is not a rounding of 6.961).
- Corrected front-consistent: MaxIrr = 12.4 mm, yield = 6.961 t/ha. Site: CONFIRMED Hampyeong.

### Hampyeong 2022 — SCENARIO VALUE MIXED INTO FRONT ROW
- §5.3 best-WP: "SMT = 54% and MaxIrr = 30 mm with 7.233 t/ha yield, 0.0 mm irrigation, WP = 1.000."
- Saved front best-WP row: SMT 54.0, MaxIrr 30.0, yield 7.295, irr 0.0, WP 1.008.
- SMT / MaxIrr / irrigation / range (0-99.3) match the front; the narrated yield 7.233 and WP 1.000 are the SCENARIO-table values (Hampyeong 2022 rainfed/deficit_SMT50 = 7.233, WP 1.000).
- Corrected: report the front row as yield 7.295 / WP 1.008, OR explicitly label 7.233/1.000 as the scenario-table value — but do not present 7.233/1.000 as the Pareto-front row. Site: CONFIRMED Hampyeong.

## Site-identity summary (from T2B, re-confirmed here by min-yield anchor)
- All four §5.3-cited fronts trace to CONFIRMED sites: Gimje 2015 (min yield 4.475; 2015 has no Chungnam candidate), Gimje 2019 soilcorrected (min 6.142 = SoilGrids Gimje rainfed), Hampyeong 2015 (min 6.016 = scenario Hampyeong 2015 rainfed), Hampyeong 2022 (min 7.295; Jeonnam-2022 front min is 6.751, so site = Hampyeong).
- No §5.3 Pareto claim traces to an initial Chungnam/Jeonnam front. Legacy chungnam_2019/jeonnam_2022 fronts exist but are uncited.

## Net disposition
- Site identity of all §5.3 fronts: CLEAN (confirmed).
- Three narration anomalies in §5.3 best-WP/range prose (Gimje 2015 range, Hampyeong 2015 MaxIrr/yield, Hampyeong 2022 yield/WP). All are source-mixing / misquote of saved-front vs scenario-table values, NOT site contamination and NOT Table 4/5 core values. They are §5.3-prose corrections to be applied in a later writing phase (not this data-only phase), using the corrected front-consistent values above.
- pop=30/gen=30/900-eval fixed settings documented; no convergence/hypervolume fabricated.

## Residual risk / limits
- Front site identity is inferred from the rainfed-yield (min-yield) anchor cross-match, not from re-running the optimizer (optimizer reconstruction is out of scope). Anchors are unambiguous (confirmed vs initial rainfed yields differ >0.3 t/ha).
- The Gimje 2015 saved front minimum irrigation is 35.3 mm (not 0), so the front does not itself contain a true rainfed (0 mm) point; the manuscript's "0 mm" endpoint is a scenario-table artifact. Any Figure-5-family plotting must use 35.3-267.2 as the Gimje 2015 front span.
- Retained human-locked theta-WP (0.306/0.18, 0.322/0.19) underlies the soilcorrected Gimje 2019 front; not revisited.
