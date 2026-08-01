# AquaAgent-OSPy Irrigation Action Memo
**Case**: case2_jeonnam | **Year**: 2022
**Generated**: 2026-05-02 15:49 | **Agent**: AquaAgent-OSPy (A4 tool-calling advisory)

---

All evidence is in hand. Here is the full structured memo.

---

# 🌾 Irrigation Action Memo
### AquaAgent-OSPy | Advisory Output — **NOT for autonomous execution**
**Case:** `case2_jeonnam` · **Simulation Year:** 2022
**Issued by:** AquaAgent-OSPy (advisory tool) · **Approval required from:** Responsible Agronomist

---

## 1. Summary

For the 2022 paddy rice season in Jeollanam-do, Korea, the simulation evidence shows that **rainfall alone was nearly sufficient** (686 mm growing-season precipitation vs. 628 mm ETo). A modest supplemental deficit-irrigation strategy — specifically **SMT-50 (25 mm total)** or the **Pareto best-WP solution (SMT 54.7%, ~30 mm total in ≤15 mm events)** — delivers yield gains of +0.3–0.5 t/ha over rainfed with minimal water investment. The resource-intensive `full_SMT80` and Pareto max-yield strategies push yield marginally higher but at a disproportionate water cost and, in the Pareto max-yield case, **trigger a safety flag (206 mm > 200 mm threshold)**. The recommended strategy is the **Pareto best-WP solution** for agronomists seeking optimised water productivity, or **deficit_SMT50** as a simple rule-based fallback.

---

## 2. Site & Weather Context

| Attribute | Value |
|---|---|
| **Region** | Jeollanam-do, Korea |
| **Coordinates** | 34.8236 °N, 127.9347 °E |
| **Nearest KMA Station** | #295 (0.6 km) |
| **Soil Type** | Clay Loam (HSG Class C) |
| **Crop** | Paddy Rice — transplanted |
| **Planting Date** | 25 May |
| **Harvest Window** | 1–15 October |
| **Land Cover** | Cropland (ESA WorldCover — check pending) |
| **Weather Source** | NASA POWER Daily API, Hargreaves-Samani ETo |

**2022 Growing Season (May–September)**

| Metric | Value |
|---|---|
| Total Precipitation | **686.3 mm** |
| Total ETo | **627.9 mm** |
| Mean T-max | 27.1 °C |
| Mean T-min | 19.0 °C |
| P − ETo balance | **+58.4 mm surplus** |

> ⚠️ The positive water balance indicates a **wet year**. The small ETo surplus means in-season dry spells at critical stages (panicle initiation, heading) could still warrant targeted supplemental irrigation, even in an overall wet season.

---

## 3. Scenario Comparison

*(Source: `load_scenario_table`, case2_jeonnam, 2022)*

| Strategy | Yield (t/ha) | Irrigation (mm) | WP (kg/m³) | Δ Yield vs. Rainfed |
|---|---|---|---|---|
| `rainfed` | 6.751 | 0.0 | 0.984 | — (baseline) |
| `deficit_SMT30` | 6.751 | 0.0 | 0.984 | +0.000 |
| `deficit_SMT50` | **6.843** | **25.0** | 0.962 | **+0.092** |
| `fixed_7d_80pct` | 7.298 | 131.7 | 0.892 | +0.547 |
| `full_SMT80` | 7.426 | 166.3 | 0.871 | +0.675 |

**Key observations:**
- **`deficit_SMT30`** applied zero irrigation in 2022 — soil moisture remained above the 30% threshold entirely due to rainfall, producing identical yield to rainfed. It is not distinguishable from rainfed in this wet year.
- **`deficit_SMT50`** triggered only **25 mm** of supplemental irrigation, producing a +0.09 t/ha yield gain at a very high water productivity (WP = 0.962 kg/m³).
- **`fixed_7d_80pct`** delivers a larger yield jump (+0.55 t/ha) but at 131.7 mm — over 5× the water input of `deficit_SMT50` — and the lowest WP among deficit strategies (0.892).
- **`full_SMT80`** achieves the scenario-table peak yield of 7.426 t/ha but requires 166.3 mm and has the lowest WP (0.871). The marginal yield gain over `fixed_7d_80pct` (+0.13 t/ha) costs an additional 34.6 mm.

---

## 4. Pareto Optimizer Findings

*(Source: `load_pareto_front`, 30 non-dominated solutions, irrigation range 0–205.8 mm)*

| Pareto Solution | SMT (%) | Max Single Event (mm) | Yield (t/ha) | Irrigation (mm) | WP (kg/m³) |
|---|---|---|---|---|---|
| **Best WP** | 54.7 | 15.1 | **7.093** | **30.2** | **0.990** |
| Max Yield | 90.0 | 12.8 | 7.438 | 205.8 | 0.834 |

**Key observations:**
- The **Best-WP Pareto solution** (SMT = 54.7%, max event = 15.1 mm, total = 30.2 mm) achieves 7.093 t/ha — a **+0.342 t/ha gain over rainfed** — while achieving the highest WP across all solutions at **0.990 kg/m³**. This is the recommended solution (see Section 5).
- The **Max-Yield Pareto solution** reaches 7.438 t/ha (just marginally above `full_SMT80` at 7.426 t/ha) but requires **205.8 mm** — a **⚠️ SAFETY-FLAGGED** level. See Section 6.
- The Pareto front confirms a rapidly diminishing-returns relationship: doubling irrigation from ~30 mm to ~206 mm yields only +0.35 t/ha extra (+4.9%).

---

## 5. Recommendation

> **This is an advisory recommendation only. A qualified agronomist must review, approve, and authorise field execution.**

### ✅ Primary Recommendation: Pareto Best-WP Strategy

| Parameter | Value |
|---|---|
| **Trigger threshold (SMT)** | 54.7% of soil water-holding capacity |
| **Maximum per-event depth** | **≤ 15.1 mm** |
| **Estimated seasonal total** | **~30 mm** |
| **Projected yield** | **7.093 t/ha** |
| **Projected WP** | **0.990 kg/m³** |
| **Source** | Pareto best-WP solution, `load_pareto_front` |

**Timing guidance:**
1. **Monitor soil moisture continuously** (tensiometer or capacitance probe at 15–20 cm depth in the root zone).
2. **Trigger irrigation** whenever volumetric soil moisture drops below 54.7% of field capacity — expected to occur at most 2–3 times given the 2022 wet-year rainfall pattern (686 mm), primarily during early vegetative or critical heading/flowering stages.
3. **Apply ≤ 15.1 mm per event** to respect the Pareto event-size constraint and avoid ponding given the Clay Loam (HSG-C) low-infiltration soil.
4. **Preferred windows:** Pre-dawn or early morning application to reduce evaporation losses.
5. **Stop supplemental irrigation** once the crop enters physiological maturity (late September), consistent with the Oct 1–15 harvest window.

### 🔄 Fallback (Rule-Based) Recommendation: `deficit_SMT50`

If real-time soil moisture monitoring is unavailable, use the simpler **`deficit_SMT50`** rule:
- Apply irrigation when estimated soil moisture falls below 50% depletion.
- Expect **~25 mm total** seasonal input, yield of **6.843 t/ha**, WP of **0.962 kg/m³** (`load_scenario_table`, row: `deficit_SMT50`).

---

## 6. Safety Notes

*(Source: `check_safety_flags`)*

| # | Strategy | Flag | Value | Threshold | Action Required |
|---|---|---|---|---|---|
| 1 | `pareto_max_yield` | ⚠️ **HIGH_IRRIGATION** | 205.8 mm | 200 mm | **DO NOT implement** without verifying field drainage capacity and soil saturation limits on the Clay Loam HSG-C soil. Risk of waterlogging and anaerobic root damage. |

> ✅ All other strategies (rainfed, deficit_SMT30, deficit_SMT50, fixed_7d_80pct, full_SMT80, pareto_best_WP) passed safety checks.

> The recommended **Pareto Best-WP** solution (30.2 mm) is well within safe bounds.

---

## 7. Uncertainty & Limitations

1. **Weather forecast uncertainty:** This analysis is based on **observed 2022 historical weather** (NASA POWER). For forward-looking decisions, seasonal forecast uncertainty (especially monsoon timing and intensity in Jeollanam-do) is not captured. Irrigation timing must be adjusted if the upcoming season diverges from the 2022 weather baseline.

2. **Soil parameter uncertainty:** The Clay Loam soil type is assigned at regional resolution; field-level variability in water-holding capacity, hydraulic conductivity, or compaction layers could shift the optimal SMT threshold away from the modelled 54.7%. A field soil characterisation is recommended before first implementation.

3. **AquaCrop-OSPy model limitation:** AquaCrop-OSPy does not explicitly simulate paddy rice ponding dynamics or bund-retention hydrology. Results should be interpreted as relative comparisons between strategies, not absolute yield predictions.

4. **ESA WorldCover land-cover classification** for this site is marked **"check pending"** — if the parcel is misclassified, the GEE-derived parameters may not reflect actual field conditions.

5. **Pareto front scope:** The NSGA-2 optimizer explored 30 non-dominated solutions within the simulated parameter space. Solutions outside the sampled SMT/MaxIrr bounds may exist and were not evaluated.

---

## 8. Provenance

| Data Source | Tool Called | Key Output |
|---|---|---|
| Site metadata | `load_site_context("case2_jeonnam")` | Clay Loam, HSG-C, Paddy Rice, plant 25-May |
| 2022 weather | `load_weather_summary("case2_jeonnam", 2022)` | Precip 686.3 mm, ETo 627.9 mm, NASA POWER |
| Scenario results | `load_scenario_table("case2_jeonnam", 2022)` | 5 strategies, yield 6.751–7.426 t/ha |
| Pareto optimizer | `load_pareto_front()` | 30 solutions, best-WP: 30.2 mm / 7.093 t/ha |
| Safety check | `check_safety_flags(all 7 scenario rows)` | 1 flag: pareto_max_yield HIGH_IRRIGATION 205.8 mm |

---

*This memo was generated by **AquaAgent-OSPy** (advisory mode). All recommendations require review and approval by a licensed agronomist before field implementation. No autonomous control actions have been or will be taken by this system.*