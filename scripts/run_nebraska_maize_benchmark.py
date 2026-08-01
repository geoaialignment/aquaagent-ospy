#!/usr/bin/env python3
"""Nebraska maize generalization benchmark for AquaAgent-OSPy.

Applies the same scenario harness as the Korea rice block to irrigated maize in
Lancaster County, Nebraska (41.0°N, 96.7°W) as a cross-crop, cross-region
transferability test.

Target: rough USDA NASS Nebraska irrigated corn orientation ~200 bu/acre ≈ 12.5 t/ha.
Do not treat this as a verified Lancaster practice-specific calibration target.
Soil:   SiltLoam (SSURGO dominant texture for eastern Nebraska Platte Valley)
Years:  2015, 2019, 2022  (same years as Korea block for comparability)
"""

from __future__ import annotations

import csv
import json
import math
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import os
from pathlib import Path

import pandas as pd

PROJ = Path(os.environ.get("AQUAAGENT_PROJECT_ROOT",
                           Path(__file__).resolve().parents[1]))
DATA = PROJ / "data" / "processed"
COMMS = PROJ / "communication" / "research" / "aquaagent_8h_20260502"

# ── Site ────────────────────────────────────────────────────────────────────
SITE = {
    "id": "case3_nebraska_maize",
    "lat": 41.0,
    "lon": -96.7,
    "name": "Lancaster County Nebraska (irrigated maize benchmark)",
    "crop": "Maize",
    "planting_date": "05/01",
    "sim_end_date": "10/20",
    "soil_type": "SiltLoam",
    "soil_source": "SSURGO dominant texture eastern Nebraska Platte Valley; AquaCrop SiltLoam defaults",
    "nass_target_irrigated_t_ha": 12.5,
    "nass_target_rainfed_t_ha": 9.5,
    "nass_note": "USDA NASS NE irrigated ~200 bu/acre (2015-22 avg); rainfed ~150 bu/acre",
    "years": [2015, 2019, 2022],
}

# ── Hargreaves-Samani ETo ────────────────────────────────────────────────────
def _ra_mj(lat_deg: float, doy: int) -> float:
    lat = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(-math.tan(lat) * math.tan(decl))
    ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.sin(ws)
    )
    return ra


def eto_hs(tmax: float, tmin: float, ra_mj: float) -> float:
    tmean = (tmax + tmin) / 2.0
    return max(0.0, 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * 0.408 * ra_mj)


# ── NASA POWER fetch ─────────────────────────────────────────────────────────
PARAMS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "WS2M", "RH2M", "ALLSKY_SFC_SW_DWN"]


def fetch_nasa_power(lat: float, lon: float, year: int) -> list[dict]:
    start = f"{year}0101"
    end = f"{year}1231"
    query = {
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "longitude": str(lon),
        "latitude": str(lat),
        "start": start,
        "end": end,
        "format": "JSON",
    }
    url = "https://power.larc.nasa.gov/api/temporal/daily/point?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers={"User-Agent": "AquaAgent-OSPy/0.1"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    params_data = payload["properties"]["parameter"]
    dates = sorted(next(iter(params_data.values())).keys())
    rows = []
    for day_str in dates:
        yr, mo, dy = int(day_str[:4]), int(day_str[4:6]), int(day_str[6:])
        doy = datetime(yr, mo, dy).timetuple().tm_yday
        tmax = float(params_data["T2M_MAX"].get(day_str, 0) or 0)
        tmin = float(params_data["T2M_MIN"].get(day_str, 0) or 0)
        precip = float(params_data["PRECTOTCORR"].get(day_str, 0) or 0)
        ra_mj = _ra_mj(lat, doy)
        eto = eto_hs(tmax, tmin, ra_mj)
        rows.append({
            "Year": yr, "Month": mo, "Day": dy,
            "MinTemp": round(tmin, 3), "MaxTemp": round(tmax, 3),
            "Precipitation": round(precip, 4),
            "ReferenceET": round(eto, 6),
        })
    return rows


def save_weather(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["Year", "Month", "Day", "MinTemp", "MaxTemp",
                                           "Precipitation", "ReferenceET"])
        w.writeheader()
        w.writerows(rows)


# ── AquaCrop-OSPy scenario run ───────────────────────────────────────────────
def run_scenarios(weather_path: Path, year: int) -> list[dict]:
    from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement

    wdf = pd.read_csv(weather_path)
    wdf.columns = ["Year", "Month", "Day", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET"]

    # Growing-season mask before dropping Month column
    _gs_mask = wdf["Month"].between(5, 9)

    # Mirror prepare_weather: create Date, drop Year/Month/Day, clip ETo
    wdf["Date"] = pd.to_datetime(wdf[["Year", "Month", "Day"]])
    wdf = wdf.drop(["Year", "Month", "Day"], axis=1)
    wdf["ReferenceET"] = wdf["ReferenceET"].clip(lower=0.1)

    soil = Soil("SiltLoam")
    crop = Crop(SITE["crop"], planting_date=SITE["planting_date"])
    init_wc = InitialWaterContent(value=["FC"])

    strategies = [
        ("rainfed",        IrrigationManagement(irrigation_method=0)),
        ("deficit_SMT30",  IrrigationManagement(irrigation_method=1, SMT=[30]*4, MaxIrr=25)),
        ("deficit_SMT50",  IrrigationManagement(irrigation_method=1, SMT=[50]*4, MaxIrr=25)),
        ("full_SMT80",     IrrigationManagement(irrigation_method=1, SMT=[80]*4, MaxIrr=25)),
        ("fixed_7d_80pct", IrrigationManagement(irrigation_method=2, IrrInterval=7, NetIrrSMT=80)),
    ]

    results = []
    for strat_name, irr_mgmt in strategies:
        model = AquaCropModel(
            sim_start_time=f"{year}/01/01",
            sim_end_time=f"{year}/10/20",
            weather_df=wdf,
            soil=soil,
            crop=crop,
            initial_water_content=init_wc,
            irrigation_management=irr_mgmt,
        )
        model.run_model(till_termination=True)
        final = model.get_simulation_results()
        yield_val = float(final["Dry yield (tonne/ha)"].iloc[-1])
        irr_val = float(final["Seasonal irrigation (mm)"].iloc[-1])
        wp = yield_val / (irr_val / 100 + 0.0001) if irr_val > 0 else 0.0
        # Compute growing-season precip (May-Sep)
        gs_precip = float(wdf.loc[_gs_mask, "Precipitation"].sum())
        results.append({
            "case": SITE["id"],
            "year": year,
            "strategy": strat_name,
            "yield_t_ha": round(yield_val, 3),
            "irrigation_mm": round(irr_val, 1),
            "grow_precip_mm": round(gs_precip, 1),
            "WP_kg_m3": round(wp, 3),
            "soil_type": SITE["soil_type"],
            "nass_irrigated_target": SITE["nass_target_irrigated_t_ha"],
            "nass_rainfed_target": SITE["nass_target_rainfed_t_ha"],
        })
    return results


# ── Main ─────────────────────────────────────────────────────────────────────
def main() -> None:
    all_results: list[dict] = []
    weather_stats: list[dict] = []

    for year in SITE["years"]:
        wfile = DATA / f"weather_aquacrop_nebraska_maize_{year}.csv"
        if wfile.exists():
            print(f"  Using cached weather: {wfile.name}")
        else:
            print(f"  Fetching NASA POWER {year} for Nebraska ({SITE['lat']}°N, {SITE['lon']}°W)...")
            rows = fetch_nasa_power(SITE["lat"], SITE["lon"], year)
            save_weather(rows, wfile)
            print(f"  Saved {len(rows)} rows to {wfile.name}")

        # Growing-season stats
        wdf = pd.read_csv(wfile)
        gs = wdf[(wdf["Month"] >= 5) & (wdf["Month"] <= 9)]
        gs_precip = round(float(gs["Precipitation"].sum()), 1)
        gs_eto = round(float(gs["ReferenceET"].sum()), 1)
        weather_stats.append({"year": year, "gs_precip_mm": gs_precip, "gs_eto_mm": gs_eto,
                               "ratio": round(gs_precip / gs_eto, 3)})
        print(f"  {year}: May-Sep precip={gs_precip}mm  ETo={gs_eto}mm  ratio={gs_precip/gs_eto:.2f}")

        print(f"  Running AquaCrop-OSPy scenarios for {year}...")
        rows_out = run_scenarios(wfile, year)
        all_results.extend(rows_out)
        for r in rows_out:
            flag = " ⚠️ HIGH_IRR" if r["irrigation_mm"] > 200 else ""
            print(f"    {r['strategy']:20s}  yield={r['yield_t_ha']:.3f} t/ha  "
                  f"irr={r['irrigation_mm']:.1f}mm  WP={r['WP_kg_m3']:.3f}{flag}")

    # Save scenario results
    out_csv = DATA / "scenario_results_nebraska_maize.csv"
    pd.DataFrame(all_results).to_csv(out_csv, index=False)
    print(f"\nScenarios saved: {out_csv}")

    # Benchmark check against NASS
    print("\n── NASS benchmark check ──")
    for year in SITE["years"]:
        year_rows = [r for r in all_results if r["year"] == year]
        rf = next((r for r in year_rows if r["strategy"] == "rainfed"), None)
        full = next((r for r in year_rows if r["strategy"] == "full_SMT80"), None)
        if rf and full:
            rf_delta = abs(rf["yield_t_ha"] - SITE["nass_target_rainfed_t_ha"])
            ir_delta = abs(full["yield_t_ha"] - SITE["nass_target_irrigated_t_ha"])
            rf_ok = "✅" if rf_delta < 3.0 else "⚠️"
            ir_ok = "✅" if ir_delta < 3.0 else "⚠️"
            print(f"  {year}: rainfed={rf['yield_t_ha']:.2f} t/ha (target~{SITE['nass_target_rainfed_t_ha']}) {rf_ok}  "
                  f"irrigated={full['yield_t_ha']:.2f} t/ha (target~{SITE['nass_target_irrigated_t_ha']}) {ir_ok}")

    # Write summary report
    report_path = COMMS / "nebraska_maize_benchmark_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Nebraska Maize Generalization Benchmark\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"Site: {SITE['name']}\n")
        f.write(f"Crop: {SITE['crop']} | Soil: {SITE['soil_type']} | Planting: {SITE['planting_date']}\n")
        f.write(f"NASS targets: irrigated ~{SITE['nass_target_irrigated_t_ha']} t/ha | rainfed ~{SITE['nass_target_rainfed_t_ha']} t/ha\n\n")
        f.write("## Weather Summary\n\n")
        f.write("| Year | May-Sep Precip (mm) | ETo (mm) | Precip/ETo |\n|---:|---:|---:|---:|\n")
        for ws in weather_stats:
            f.write(f"| {ws['year']} | {ws['gs_precip_mm']} | {ws['gs_eto_mm']} | {ws['ratio']:.2f} |\n")
        f.write("\n## Scenario Results\n\n")
        f.write("| Year | Strategy | Yield (t/ha) | Irrigation (mm) | WP (kg/m³) |\n|---:|---|---:|---:|---:|\n")
        for r in all_results:
            flag = " ⚠️" if r["irrigation_mm"] > 200 else ""
            f.write(f"| {r['year']} | {r['strategy']}{flag} | {r['yield_t_ha']:.3f} | "
                    f"{r['irrigation_mm']:.1f} | {r['WP_kg_m3']:.3f} |\n")
        f.write("\n## NASS Benchmark Check (±3 t/ha tolerance)\n\n")
        for year in SITE["years"]:
            year_rows = [r for r in all_results if r["year"] == year]
            rf = next((r for r in year_rows if r["strategy"] == "rainfed"), None)
            full = next((r for r in year_rows if r["strategy"] == "full_SMT80"), None)
            if rf and full:
                rf_ok = "PASS" if abs(rf["yield_t_ha"] - SITE["nass_target_rainfed_t_ha"]) < 3.0 else "WARN"
                ir_ok = "PASS" if abs(full["yield_t_ha"] - SITE["nass_target_irrigated_t_ha"]) < 3.0 else "WARN"
                f.write(f"- {year}: rainfed={rf['yield_t_ha']:.2f} t/ha vs NASS~{SITE['nass_target_rainfed_t_ha']} → {rf_ok}  |  "
                        f"irrigated={full['yield_t_ha']:.2f} vs NASS~{SITE['nass_target_irrigated_t_ha']} → {ir_ok}\n")
        f.write("\n## Workflow Transferability\n\n")
        f.write("Same AquaAgent-OSPy scenario harness (NASA POWER -> Hargreaves-Samani ETo -> AquaCrop-OSPy -> safety checks) "
                "applied to Nebraska maize with the same five scheduling strategies. "
                "This script does not run NSGA-II/Pareto optimization or memo generation.\n\n")
        f.write("**Claim level**: `benchmark_generalization_limited` — scenario-harness transferability only; not field-calibrated.\n")
    print(f"\nBenchmark report: {report_path}")


if __name__ == "__main__":
    main()
