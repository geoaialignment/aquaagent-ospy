#!/usr/bin/env python3
"""Penman-Monteith ETo sensitivity comparison for Gimje 2019 (primary case).

Replaces Hargreaves-Samani ETo with FAO-56 PM ETo and re-runs the 5-strategy
AquaCrop-OSPy scenario comparison. Reports whether strategy rankings change.
"""

from __future__ import annotations
import csv
import math
import pandas as pd
import os
from pathlib import Path

PROJ = Path(os.environ.get("AQUAAGENT_PROJECT_ROOT",
                           Path(__file__).resolve().parents[1]))
DATA = PROJ / "data" / "processed"

LAT = 35.754  # Gimje
YEAR = 2019

# ── Ra (extraterrestrial radiation) ─────────────────────────────────────────
def _ra_mj(lat_deg: float, doy: int) -> float:
    lat = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(-math.tan(lat) * math.tan(decl))
    return (24*60/math.pi) * 0.0820 * dr * (
        ws * math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.sin(ws)
    )

# ── Hargreaves-Samani ────────────────────────────────────────────────────────
def eto_hs(tmax: float, tmin: float, ra_mj: float) -> float:
    tmean = (tmax + tmin) / 2
    return max(0, 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0)) * 0.408 * ra_mj)

# ── FAO-56 Penman-Monteith ──────────────────────────────────────────────────
def eto_pm(tmax: float, tmin: float, rs_mj: float, ws2: float,
           rh_mean: float, ra_mj: float) -> float:
    tmean = (tmax + tmin) / 2

    # Saturation vapour pressure
    es = (0.6108 * math.exp(17.27 * tmax / (tmax + 237.3)) +
          0.6108 * math.exp(17.27 * tmin / (tmin + 237.3))) / 2  # kPa
    ea = max(0.001, rh_mean / 100 * es)  # actual vapour pressure kPa

    # Slope of es curve
    delta = 4098 * 0.6108 * math.exp(17.27 * tmean / (tmean + 237.3)) / (tmean + 237.3)**2

    # Psychrometric constant (kPa/°C) — approximate at sea level
    gamma = 0.0665

    # Net shortwave radiation
    rns = (1 - 0.23) * rs_mj  # grass albedo 0.23

    # Net longwave (FAO-56 Eq 39)
    sigma = 4.903e-9  # MJ m-2 K-4 d-1
    # Cloud fraction from Rs/Ra (cap at 1)
    cloud_ratio = min(rs_mj / (0.75 * ra_mj + 1e-9), 1.0)
    rnl = sigma * ((tmax + 273.16)**4 + (tmin + 273.16)**4) / 2 * \
          (0.34 - 0.14 * math.sqrt(ea)) * (1.35 * cloud_ratio - 0.35)

    rn = rns - rnl
    g = 0  # soil heat flux negligible at daily step

    num = 0.408 * delta * (rn - g) + gamma * (900 / (tmean + 273)) * ws2 * (es - ea)
    den = delta + gamma * (1 + 0.34 * ws2)
    return max(0.0, num / den)

# ── Load weather and compute both ETo ───────────────────────────────────────
def load_weather_with_pm(lat: float, year: int, site: str) -> pd.DataFrame:
    wfile = DATA / f"weather_aquacrop_{site}_{year}.csv"
    df = pd.read_csv(wfile)
    df.columns = ["Year", "Month", "Day", "MinTemp", "MaxTemp", "Precipitation", "ReferenceET"]

    # Load original NASA POWER file with additional vars
    raw_file = DATA / f"nasa_power_{site}_{year}_full.csv"
    if raw_file.exists():
        raw = pd.read_csv(raw_file)
        df["WS2M"] = raw["WS2M"].values
        df["RH2M"] = raw["RH2M"].values
        df["RS_MJ"] = raw["ALLSKY_SFC_SW_DWN"].values
    else:
        # Reconstruct RS from HS formula: HS uses Ra, we need Rs
        # Rs ≈ Ra * (0.16 to 0.19) * sqrt(tmax-tmin) for humid climates
        # Or: since we have HS ETo, back-calculate Rs from it
        # Simpler: use ALLSKY_SFC_SW_DWN from the weather fetch — already in wfile? No.
        # Fall back: use Rs from Ra scaling (Angstrom)
        print(f"  No full NASA POWER file for {site} {year} — fetching WS2M+RH2M")
        import urllib.request
        import urllib.parse
        import json as json_lib

        coords = {"case1_gimje": (35.754, 126.898), "case2_hampyeong": (35.07, 126.54)}
        la, lo = coords.get(site, (lat, 126.898))
        params = "T2M_MAX,T2M_MIN,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN"
        url = (f"https://power.larc.nasa.gov/api/temporal/daily/point?"
               f"parameters={params}&community=AG&longitude={lo}&latitude={la}"
               f"&start={year}0101&end={year}1231&format=JSON")
        req = urllib.request.Request(url, headers={"User-Agent": "AquaAgent-OSPy/0.1"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            payload = json_lib.loads(resp.read().decode("utf-8"))
        pd_data = payload["properties"]["parameter"]
        dates = sorted(next(iter(pd_data.values())).keys())
        df["WS2M"] = [float(pd_data["WS2M"].get(d, 2.0) or 2.0) for d in dates]
        df["RH2M"] = [float(pd_data["RH2M"].get(d, 70.0) or 70.0) for d in dates]
        df["RS_MJ"] = [float(pd_data["ALLSKY_SFC_SW_DWN"].get(d, 15.0) or 15.0) for d in dates]

    # Compute both ETo versions
    eto_hs_list, eto_pm_list = [], []
    for _, row in df.iterrows():
        doy = int(pd.Timestamp(year=int(row["Year"]), month=int(row["Month"]), day=int(row["Day"])).day_of_year)
        ra = _ra_mj(lat, doy)
        eto_hs_list.append(eto_hs(row["MaxTemp"], row["MinTemp"], ra))
        eto_pm_list.append(eto_pm(row["MaxTemp"], row["MinTemp"],
                                   row.get("RS_MJ", 15.0),
                                   row.get("WS2M", 2.0),
                                   row.get("RH2M", 70.0),
                                   ra))
    df["ETo_HS"] = eto_hs_list
    df["ETo_PM"] = eto_pm_list
    return df


def run_aquacrop_with_eto(df_base: pd.DataFrame, eto_col: str, year: int, site: str) -> list[dict]:
    from aquacrop import AquaCropModel, Soil, Crop, InitialWaterContent, IrrigationManagement

    # Write a temp CSV with the ETo column replaced, then use prepare_weather
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
    tmp.write("Day Month Year MinTemp MaxTemp Precipitation ReferenceET\n")
    for _, row in df_base.iterrows():
        eto_val = max(0.1, float(row[eto_col]))
        tmp.write(f"{int(row['Day'])} {int(row['Month'])} {int(row['Year'])} "
                  f"{row['MinTemp']:.4f} {row['MaxTemp']:.4f} "
                  f"{row['Precipitation']:.4f} {eto_val:.6f}\n")
    tmp.close()
    from aquacrop.utils import prepare_weather
    df = prepare_weather(tmp.name)
    os.unlink(tmp.name)

    # Use default ClayLoam for valid HS-vs-PM comparison (same soil, different ETo)
    # Note: this uses AquaCrop default th_fc=0.390, NOT SoilGrids-corrected values
    # The comparison is valid for showing ETo method effect only — absolute yields differ
    soil = Soil("ClayLoam")

    crop = Crop("PaddyRice", planting_date="05/25")
    init_wc = InitialWaterContent(value=["FC"])

    strategies = [
        ("rainfed",        IrrigationManagement(irrigation_method=0)),
        ("deficit_SMT30",  IrrigationManagement(irrigation_method=1, SMT=[30]*4, MaxIrr=25)),
        ("deficit_SMT50",  IrrigationManagement(irrigation_method=1, SMT=[50]*4, MaxIrr=25)),
        ("full_SMT80",     IrrigationManagement(irrigation_method=1, SMT=[80]*4, MaxIrr=25)),
        ("fixed_7d_80pct", IrrigationManagement(irrigation_method=2, IrrInterval=7, NetIrrSMT=80)),
    ]

    results = []
    for name, irr in strategies:
        m = AquaCropModel(
            sim_start_time=f"{year}/01/01", sim_end_time=f"{year}/10/15",
            weather_df=df.copy(), soil=soil, crop=crop,
            initial_water_content=init_wc, irrigation_management=irr,
        )
        m.run_model(till_termination=True)
        r = m.get_simulation_results()
        y = float(r["Dry yield (tonne/ha)"].iloc[-1])
        irr_mm = float(r["Seasonal irrigation (mm)"].iloc[-1])
        wp = y * 100 / irr_mm if irr_mm > 0.5 else y * 100 / 0.1
        results.append({"strategy": name, "yield_t_ha": round(y,3),
                        "irrigation_mm": round(irr_mm,1), "WP_kg_m3": round(wp,3),
                        "eto_method": eto_col})
    return results


def main():
    site = "case1_gimje"
    year = YEAR

    print(f"Loading weather + computing HS and PM ETo for {site} {year}...")
    df = load_weather_with_pm(LAT, year, site)

    # Growing-season stats
    gs = df[(df["Month"] >= 5) & (df["Month"] <= 9)]
    print(f"  Growing-season ETo: HS={gs['ETo_HS'].sum():.1f}mm  PM={gs['ETo_PM'].sum():.1f}mm")
    ratio = gs["ETo_PM"].sum() / gs["ETo_HS"].sum()
    print(f"  PM/HS ratio: {ratio:.3f} ({'PM higher' if ratio>1 else 'HS higher'})")

    print("\nRunning scenarios with HS ETo...")
    hs_results = run_aquacrop_with_eto(df, "ETo_HS", year, site)

    print("Running scenarios with PM ETo...")
    pm_results = run_aquacrop_with_eto(df, "ETo_PM", year, site)

    # Compare
    print("\n=== Strategy rankings: HS vs PM ===")
    print(f"{'Strategy':20s}  {'HS yield':10s}  {'PM yield':10s}  {'HS irr':8s}  {'PM irr':8s}")
    for hs, pm in zip(hs_results, pm_results):
        diff_irr = pm["irrigation_mm"] - hs["irrigation_mm"]
        flag = "⚠️" if abs(diff_irr) > 20 else ""
        print(f"{hs['strategy']:20s}  {hs['yield_t_ha']:10.3f}  {pm['yield_t_ha']:10.3f}  "
              f"{hs['irrigation_mm']:8.1f}  {pm['irrigation_mm']:8.1f}  {diff_irr:+.1f}mm {flag}")

    # Check if strategy rankings change
    hs_rank = sorted(hs_results, key=lambda r: -r["WP_kg_m3"])
    pm_rank = sorted(pm_results, key=lambda r: -r["WP_kg_m3"])
    hs_best_wp = hs_rank[0]["strategy"]
    pm_best_wp = pm_rank[0]["strategy"]
    ranking_stable = [h["strategy"] for h in hs_rank] == [p["strategy"] for p in pm_rank]

    print(f"\nBest-WP strategy: HS={hs_best_wp}  PM={pm_best_wp}")
    print(f"Strategy WP rankings: {'IDENTICAL' if ranking_stable else 'CHANGED'}")

    # Save
    all_rows = hs_results + pm_results
    out = DATA / "eto_sensitivity_hs_vs_pm_gimje2019.csv"
    pd.DataFrame(all_rows).to_csv(out, index=False)
    print(f"\nSaved to {out.name}")

    # Write summary for manuscript
    summary_path = PROJ / "communication/research/aquaagent_8h_20260502/eto_pm_sensitivity.md"
    with open(summary_path, "w") as f:
        f.write("# PM vs HS ETo Sensitivity — Gimje 2019\n\n")
        f.write(f"Growing-season ETo: HS={gs['ETo_HS'].sum():.1f}mm  PM={gs['ETo_PM'].sum():.1f}mm  "
                f"ratio={ratio:.3f}\n\n")
        f.write(f"Best-WP strategy: HS={hs_best_wp}  PM={pm_best_wp}\n")
        f.write(f"Rankings: {'STABLE' if ranking_stable else 'CHANGED'}\n\n")
        f.write("| Strategy | HS yield | PM yield | HS irr | PM irr | Δirr |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for hs, pm in zip(hs_results, pm_results):
            f.write(f"| {hs['strategy']} | {hs['yield_t_ha']:.3f} | {pm['yield_t_ha']:.3f} | "
                    f"{hs['irrigation_mm']:.1f} | {pm['irrigation_mm']:.1f} | "
                    f"{pm['irrigation_mm']-hs['irrigation_mm']:+.1f} |\n")
    print(f"Summary: {summary_path.name}")
    return ranking_stable


if __name__ == "__main__":
    main()
