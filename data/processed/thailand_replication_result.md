# Thailand Replication — Veerakachen 2020 RiceSAP

Date: 2026-05-02
Purpose: External validation of AquaCrop-OSPy PaddyRice parameters
Reference: Veerakachen et al. (2020) RiceSAP, doi:10.3390/agronomy10060858

## Setup
- Site: Suphan Buri Province, Thailand (14.47°N, 100.13°E)
- Weather: NASA POWER Daily (2015, wet season Jul-Oct)
- Soil: SandyLoam (Thailand central plain alluvial)
- Crop: PaddyRice, planting_date='07/01', default parameters
- Season: Jul 1 – Nov 30

## Results
| Strategy | Yield (t/ha) | Irrigation (mm) |
|---|---|---|
| Rainfed | 4.766 | 0 |
| Fixed 7d 80pct | 6.880 | 140.1 |
| Deficit SMT50 | 6.529 | 100.0 |

## Comparison to Veerakachen 2020
- Paper reported rainfed yield range: ~3-5 t/ha (estimated from their results section)
- Our simulation: 4.766 t/ha rainfed — WITHIN REPORTED RANGE ✅
- Wet season Jul-Oct precipitation: 692mm (plausible for Suphan Buri)

## Interpretation
The default AquaCrop-OSPy PaddyRice parameters produce agronomically plausible yields
for transplanted Asian monsoon rice (Thailand context). This supports the external
validity of using the same parameters for Korean paddy rice under similar
transplanting management.

**Caveat**: This is a qualitative range comparison, not a formal R² validation.
Point-by-point calibration would require the original RiceSAP dataset.
