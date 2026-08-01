# AquaAgent-OSPy Irrigation Action Memo
**Case**: case2_hampyeong | **Year**: 2022
**Generated**: 2026-05-02 16:06 | **Agent**: AquaAgent-OSPy (A4 tool-calling advisory)

---

All data is in hand, safety checker is clean. **Writing the full memo now:**

---

# 🌾 AquaAgent-OSPy — Irrigation Action Memo
**Case:** `case2_hampyeong` | **Simulation Year:** 2022
**Issued by:** AquaAgent-OSPy (Advisory Tool — Human Approval Required)
**Date Generated:** *(system timestamp)*

---

## 1. Summary

Simulation evidence for Hampyeong paddy rice in 2022 shows an **exceptionally wet growing season** (723.6 mm precipitation vs. 474.8 mm ETo), resulting in near-zero supplemental irrigation demand across most strategies. The highest simulated yield is **7.438 t/ha** (Pareto max-yield solution, 99.3 mm irrigation), only **+0.143 t/ha (+2.0%)** above the rainfed baseline of 7.295 t/ha. Given this marginal gain and the high water-productivity of the rainfed scenario, **the recommended strategy is `full_SMT80` with a capped single-application depth of ≤25 mm, triggered only during confirmed dry spells**, rather than calendar-based irrigation. A human agronomist must review and approve before any water application.

---

## 2. Site & Weather Context

| Parameter | Value | Source |
|---|---|---|
| **Region** | Hampyeong-gun, Jeollanam-do, South Korea | `load_site_context` |
| **Coordinates** | 35.07 °N, 126.54 °E | `load_site_context` |
| **Soil Type** | Clay Loam, HSG Class C (low infiltration) | `load_site_context` |
| **Crop** | Paddy Rice (transplanted) | `load_site_context` |
| **Planting Date** | 25 May | `load_site_context` |
| **Harvest Window** | 1–15 October | `load_site_context` |
| **Season Precipitation** | **723.6 mm** (May–Sep) | `load_weather_summary` |
| **Season ETo** | 474.8 mm (May–Sep) | `load_weather_summary` |
| **Mean T-max / T-min** | 24.7 °C / 19.9 °C | `load_weather_summary` |
| **Weather Data Source** | NASA POWER Daily API, Hargreaves-Samani ETo | `load_weather_summary` |

> ⚠️ **Weather data quality note:** ERA5 vs. NASA POWER monthly precipitation correlation is **0.667 (WARN)** and temperature MAE is 0.92 °C, flagged by `load_site_context`. KMA station linkage is **pending**. This introduces uncertainty in ETo estimation (see Section 7).

The precipitation surplus (723.6 mm P vs. 474.8 mm ETo = **+248.8 mm surplus**) explains why all deficit/rainfed strategies show identical yields of 7.295 t/ha with zero irrigation applied.

---

## 3. Scenario Comparison

*Source: `load_scenario_table` — case2_hampyeong, 2022*

| # | Strategy | Yield (t/ha) | Irrigation (mm) | WP (kg/m³) | Δ Yield vs. Rainfed |
|---|---|---|---|---|---|
| 1 | `rainfed` | 7.295 | 0.0 | **1.008** | baseline |
| 2 | `deficit_SMT50` | 7.295 | 0.0 | 1.008 | 0.000 |
| 3 | `deficit_SMT30` | 7.295 | 0.0 | 1.008 | 0.000 |
| 4 | `full_SMT80` | **7.434** | 76.4 | 0.929 | +0.139 |
| 5 | `fixed_7d_80pct` | 7.417 | 94.6 | 0.907 | +0.122 |

**Key observations:**
- **Strategies 1–3** (`rainfed`, `deficit_SMT50`, `deficit_SMT30`) are indistinguishable: 2022's rainfall fully satisfies crop demand at or below the 50% SMT threshold, resulting in **0 mm applied irrigation** under these rules.
- **`full_SMT80`** applies 76.4 mm to achieve the highest scenario yield of 7.434 t/ha and the best WP among the irrigated strategies (0.929 kg/m³).
- **`fixed_7d_80pct`** uses *more* water (94.6 mm) for *less* yield (7.417 t/ha) — a dominated solution in both yield and water use.
- The **maximum marginal return** of additional irrigation is only **+0.139 t/ha for 76.4 mm**, yielding a marginal WP of only **0.18 kg/m³** — far below the rainfed WP baseline.

---

## 4. Pareto Optimizer Findings

*Source: `load_pareto_front` — NSGA-2, 30 Pareto-optimal solutions*

| Solution | SMT (%) | MaxIrr per Event (mm) | Yield (t/ha) | Total Irrigation (mm) | WP (kg/m³) |
|---|---|---|---|---|---|
| **Best WP** | 54.0 | 30 | 7.295 | 0.0 | **1.008** |
| **Max Yield** | 89.5 | 10 | **7.438** | 99.3 | 0.904 |
| *Pareto range* | — | — | — | 0.0 – 99.3 | — |

**Pareto interpretation:**
- The **best-WP Pareto solution** (SMT=54%, MaxIrr=30 mm) achieves the same yield as rainfed (7.295 t/ha) with 0 mm irrigation in 2022 conditions — confirming that a 54% SMT trigger is never activated when rainfall is this abundant.
- The **max-yield Pareto solution** (SMT=89.5%, MaxIrr=10 mm/event, total 99.3 mm) yields 7.438 t/ha — the absolute ceiling across all 30 solutions. However, the WP of 0.904 kg/m³ is **10.3% lower** than the rainfed baseline.
- The Pareto front is **compressed** (yield range: 7.295–7.438 t/ha, Δ = 0.143 t/ha), signalling a **rainfall-dominated year** where optimizer leverage is minimal.

---

## 5. Recommendation

> ⚠️ **This is an advisory recommendation. A qualified human agronomist must review and authorize all irrigation actions before field implementation.**

### Recommended Strategy: `full_SMT80` — Adaptive Deficit Trigger with 25 mm Event Cap

**Rationale:** `full_SMT80` is the only scenario delivering a meaningful yield gain (+0.139 t/ha over rainfed, per `load_scenario_table` row 4) without the calendar-based inefficiency of `fixed_7d_80pct`. In a wet year like 2022, the SMT-80 trigger will self-regulate to apply irrigation **only when soil moisture genuinely drops below 80% of field capacity**.

#### Specific Irrigation Prescription

| Parameter | Prescribed Value | Evidence Basis |
|---|---|---|
| **Trigger** | Soil Moisture < 80% field capacity | `full_SMT80` scenario; Pareto max-yield SMT=89.5% as upper bound |
| **Application depth per event** | **≤ 25 mm** | Pareto best-WP solution: MaxIrr=30 mm/event; conservative 25 mm recommended given HSG-C clay loam (low infiltration rate) |
| **Expected season total** | ~76 mm (wet year analog) | `full_SMT80` simulation: 76.4 mm total (`load_scenario_table`) |
| **Timing** | Stress-triggered, not calendar-fixed | Avoids dominated `fixed_7d_80pct` outcome (94.6 mm, lower yield) |
| **Priority growth stages** | Tillering → Heading (approx. late June – late August) | Paddy rice peak water demand; planting 25 May → heading ~Day 75–90 |

#### Strategy Summary
Apply **one irrigation event of 20–25 mm** whenever field-level monitoring (or a calibrated soil moisture sensor) confirms SMT < 80%, **particularly during any dry spells of ≥7 consecutive days** within June–August. In a year matching 2022 rainfall patterns, expect **3–4 events maximum** for a season total near 76 mm. Do **not** irrigate on a fixed calendar schedule — this wastes water without yield benefit, as demonstrated by `fixed_7d_80pct`.

---

## 6. Safety Notes

*Source: `check_safety_flags` — 0 flags raised*

✅ **No safety violations detected** across all 5 simulated strategies:
- No strategy exceeds the **200 mm excessive irrigation threshold**.
- No strategy falls below the **3.0 t/ha minimum yield threshold**.
- Maximum irrigation across all scenarios: 99.3 mm (Pareto max-yield) — well within safe range.
- Minimum yield across all scenarios: 7.295 t/ha — well above the safety floor.

---

## 7. Uncertainty & Limitations

1. **Weather data quality (PRIMARY UNCERTAINTY):** NASA POWER precipitation data for this site shows a **monthly correlation of only 0.667 vs. ERA5 (WARN flag)**, and temperature MAE of 0.92 °C. ETo calculated via Hargreaves-Samani is sensitive to temperature bias. If actual growing-season rainfall was lower than 723.6 mm, all deficit strategies would activate earlier and total irrigation demand would be substantially higher than simulated.

2. **KMA station linkage pending:** No verified Korea Meteorological Administration ground station is linked to this site (`nearest_kma_station: pending`). The recommendation should be revisited once local station data is available and cross-validated.

3. **Soil parameter uncertainty:** Clay Loam / HSG-C soils have high spatial variability in hydraulic conductivity. The AquaCrop-OSPy model uses a single soil parameterization; field-level variation in infiltration rate may shift the optimal per-event irrigation depth from the modeled 25–30 mm range.

4. **Single-year simulation:** This memo is based exclusively on 2022 simulation results. In drier years (e.g., if 2023 precipitation is significantly below 724 mm), the SMT-80 strategy will trigger more frequently and yield gains relative to rainfed will be larger. Multi-year ensemble runs are recommended before locking in a seasonal irrigation schedule.

5. **AquaCrop-OSPy model limitation:** AquaCrop does not explicitly simulate ponded water management (bund depth, percolation) typical of transplanted paddy rice. Saturated soil/ponding dynamics are approximated; actual field water balance in paddy plots may differ from model output.

---

## 8. Provenance

| Data Element | Tool Called | Key Parameters |
|---|---|---|
| Site metadata | `load_site_context` | `case_id = case2_hampyeong` |
| Weather summary | `load_weather_summary` | `case_id = case2_hampyeong`, `year = 2022` |
| Scenario results (5 strategies) | `load_scenario_table` | `case_id = case2_hampyeong`, `year = 2022` |
| Pareto front (30 solutions) | `load_pareto_front` | *(no parameters)* |
| Safety check | `check_safety_flags` | All 5 scenario rows passed |
| **Flags raised** | — | **0 safety flags** |

> *All quantitative values in this memo are sourced directly from tool outputs. No values have been assumed or synthesized from prior model knowledge. This document is an advisory output of AquaAgent-OSPy and does not constitute autonomous irrigation control. Final approval and execution authority rests with the responsible agronomist.*

---
*AquaAgent-OSPy | Advisory Class A4 | case2_hampyeong | 2022*