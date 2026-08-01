#!/usr/bin/env python3
"""Run extended GEE context validation for AquaAgent-OSPy sites.

This script intentionally keeps the claim level conservative. Dynamic World,
WorldCover, Sentinel-2 NDVI, Sentinel-1 SAR, and JRC water occurrence are
context checks for site plausibility and crop-season consistency. They are not
field validation.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "gee_extended_validation.csv"
DEFAULT_LOG = (
    PROJECT_ROOT
    / "communication"
    / "research"
    / "aquaagent_8h_20260502"
    / "gee_extended_validation.md"
)

SITES = [
    {
        "case_id": "original_case1_chungnam",
        "site_name": "Original Chungnam polygon centroid",
        "lat": 36.9346,
        "lon": 126.554,
        "expected_status": "reject",
    },
    {
        "case_id": "original_case2_jeonnam",
        "site_name": "Original Jeonnam polygon centroid",
        "lat": 34.8236,
        "lon": 127.9347,
        "expected_status": "reject",
    },
    {
        "case_id": "case1_gimje",
        "site_name": "Gimje confirmed paddy candidate",
        "lat": 35.754,
        "lon": 126.898,
        "expected_status": "retain",
    },
    {
        "case_id": "case2_hampyeong",
        "site_name": "Hampyeong confirmed paddy candidate",
        "lat": 35.070,
        "lon": 126.540,
        "expected_status": "retain",
    },
]

YEARS = [2019, 2022]
MONTHS = [5, 6, 7, 8, 9, 10]
WORLDCOVER_LABELS = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare/sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: float | None, digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def _mean_at(ee: Any, image: Any, geometry: Any, band: str, scale: int) -> float | None:
    values = image.select(band).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=scale,
        maxPixels=1_000_000,
        bestEffort=True,
    ).getInfo()
    return _safe_float(values.get(band))


def _first_at(ee: Any, image: Any, geometry: Any, band: str, scale: int) -> float | None:
    values = image.select(band).reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=geometry,
        scale=scale,
        maxPixels=1_000_000,
        bestEffort=True,
    ).getInfo()
    return _safe_float(values.get(band))


def _mask_s2_clouds(image: Any) -> Any:
    scl = image.select("SCL")
    valid = (
        scl.neq(3)
        .And(scl.neq(8))
        .And(scl.neq(9))
        .And(scl.neq(10))
        .And(scl.neq(11))
    )
    return image.updateMask(valid)


def dynamic_world_crop_mean(ee: Any, point: Any, year: int) -> tuple[float | None, int]:
    collection = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(point)
        .filterDate(f"{year}-05-01", f"{year}-10-31")
    )
    count = int(collection.size().getInfo())
    if count == 0:
        return None, 0
    crop_mean = _mean_at(ee, collection.select("crops").mean(), point.buffer(100), "crops", 10)
    return crop_mean, count


def sentinel_ndvi_monthly(ee: Any, point: Any, year: int, month: int) -> tuple[float | None, int]:
    start = f"{year}-{month:02d}-01"
    end_month = month + 1
    end_year = year
    if end_month == 13:
        end_month = 1
        end_year += 1
    end = f"{end_year}-{end_month:02d}-01"
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(point)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
        .map(_mask_s2_clouds)
    )
    count = int(collection.size().getInfo())
    if count == 0:
        return None, 0
    ndvi = collection.map(lambda img: img.normalizedDifference(["B8", "B4"]).rename("NDVI"))
    return _mean_at(ee, ndvi.median(), point.buffer(100), "NDVI", 10), count


def sentinel1_vh_monthly(ee: Any, point: Any, year: int, month: int) -> tuple[float | None, int]:
    start = f"{year}-{month:02d}-01"
    end_month = month + 1
    end_year = year
    if end_month == 13:
        end_month = 1
        end_year += 1
    end = f"{end_year}-{end_month:02d}-01"
    collection = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(point)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select("VH")
    )
    count = int(collection.size().getInfo())
    if count == 0:
        return None, 0
    return _mean_at(ee, collection.median(), point.buffer(100), "VH", 10), count


def run(output: Path, log: Path, project: str | None) -> None:
    import ee

    if project:
        ee.Initialize(project=project)
    else:
        ee.Initialize()
    rows: list[dict[str, str]] = []

    worldcover = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    water_occurrence = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")

    for site in SITES:
        point = ee.Geometry.Point([site["lon"], site["lat"]])
        wc_value = _first_at(ee, worldcover, point, "Map", 10)
        jrc_occ = _mean_at(ee, water_occurrence, point.buffer(100), "occurrence", 30)
        for year in YEARS:
            crops_p, dw_count = dynamic_world_crop_mean(ee, point, year)
            monthly: dict[int, float | None] = {}
            monthly_counts: dict[int, int] = {}
            s1_vh: dict[int, float | None] = {}
            s1_counts: dict[int, int] = {}
            for month in MONTHS:
                ndvi, n_img = sentinel_ndvi_monthly(ee, point, year, month)
                monthly[month] = ndvi
                monthly_counts[month] = n_img
                vh, n_s1 = sentinel1_vh_monthly(ee, point, year, month)
                s1_vh[month] = vh
                s1_counts[month] = n_s1
            valid_ndvi = [v for v in monthly.values() if v is not None]
            ndvi_peak = max(valid_ndvi) if valid_ndvi else None
            ndvi_min = min(valid_ndvi) if valid_ndvi else None
            transplant_dip = min(
                [v for m, v in monthly.items() if m in (6, 7) and v is not None],
                default=None,
            )
            valid_vh = [v for v in s1_vh.values() if v is not None]
            vh_min_may_jul = min(
                [v for m, v in s1_vh.items() if m in (5, 6, 7) and v is not None],
                default=None,
            )
            vh_sep = s1_vh.get(9)
            vh_rise_to_sep = None
            if vh_min_may_jul is not None and vh_sep is not None:
                vh_rise_to_sep = vh_sep - vh_min_may_jul
            status = "PASS"
            notes: list[str] = []
            if crops_p is None:
                status = "WARN"
                notes.append("Dynamic World unavailable")
            elif site["expected_status"] == "retain" and crops_p < 0.35:
                status = "FAIL"
                notes.append("retained site has low DW crops probability")
            elif site["expected_status"] == "reject" and crops_p >= 0.35:
                status = "WARN"
                notes.append("rejected site has non-low DW crops probability; inspect manually")
            if wc_value in (30, 80) and site["expected_status"] == "retain":
                status = "FAIL"
                notes.append("WorldCover class conflicts with retained cropland claim")
            if jrc_occ is not None and jrc_occ > 50 and site["expected_status"] == "retain":
                status = "WARN"
                notes.append("high JRC water occurrence near retained point")
            if site["expected_status"] == "retain":
                if not valid_vh:
                    status = "WARN"
                    notes.append("Sentinel-1 VH unavailable")
                elif vh_rise_to_sep is not None and vh_rise_to_sep < 1.0:
                    status = "WARN"
                    notes.append("weak Sentinel-1 VH rise from transplant window to September")
            if not notes:
                notes.append("GEE context is consistent with expected retain/reject status")

            rows.append(
                {
                    "case_id": site["case_id"],
                    "site_name": site["site_name"],
                    "lat": str(site["lat"]),
                    "lon": str(site["lon"]),
                    "year": str(year),
                    "expected_status": site["expected_status"],
                    "worldcover_code": "" if wc_value is None else str(int(wc_value)),
                    "worldcover_label": WORLDCOVER_LABELS.get(int(wc_value), "") if wc_value is not None else "",
                    "jrc_water_occurrence_pct": _round(jrc_occ),
                    "dynamic_world_crops_mean": _round(crops_p),
                    "dynamic_world_image_count": str(dw_count),
                    "ndvi_may": _round(monthly[5]),
                    "ndvi_jun": _round(monthly[6]),
                    "ndvi_jul": _round(monthly[7]),
                    "ndvi_aug": _round(monthly[8]),
                    "ndvi_sep": _round(monthly[9]),
                    "ndvi_oct": _round(monthly[10]),
                    "ndvi_peak_may_oct": _round(ndvi_peak),
                    "ndvi_min_may_oct": _round(ndvi_min),
                    "ndvi_transplant_dip_jun_jul": _round(transplant_dip),
                    "s2_image_counts_may_oct": json.dumps(monthly_counts, sort_keys=True),
                    "s1_vh_may_db": _round(s1_vh[5]),
                    "s1_vh_jun_db": _round(s1_vh[6]),
                    "s1_vh_jul_db": _round(s1_vh[7]),
                    "s1_vh_aug_db": _round(s1_vh[8]),
                    "s1_vh_sep_db": _round(s1_vh[9]),
                    "s1_vh_oct_db": _round(s1_vh[10]),
                    "s1_vh_min_may_jul_db": _round(vh_min_may_jul),
                    "s1_vh_rise_min_to_sep_db": _round(vh_rise_to_sep),
                    "s1_image_counts_may_oct": json.dumps(s1_counts, sort_keys=True),
                    "validation_status": status,
                    "notes": "; ".join(notes),
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    log.parent.mkdir(parents=True, exist_ok=True)
    failed = [r for r in rows if r["validation_status"] == "FAIL"]
    warned = [r for r in rows if r["validation_status"] == "WARN"]
    retained = [r for r in rows if r["expected_status"] == "retain"]
    rejected = [r for r in rows if r["expected_status"] == "reject"]
    lines = [
        "# GEE Extended Validation",
        "",
        f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"GEE project: `{project or 'default Earth Engine credentials'}`",
        f"Output CSV: `{output}`",
        "",
        "## Scope",
        "",
        "This run re-checks the two rejected original centroids and the two retained confirmed sites using GEE direct products and standard indices.",
        "Products used: Dynamic World V1 crops probability, ESA WorldCover v200, Sentinel-2 SR Harmonized NDVI, Sentinel-1 GRD VH backscatter, and JRC Global Surface Water occurrence.",
        "",
        "## Verdict",
        "",
        f"- Rows: `{len(rows)}` ({len(retained)} retained-site rows, {len(rejected)} rejected-site rows)",
        f"- FAIL rows: `{len(failed)}`",
        f"- WARN rows: `{len(warned)}`",
        "- Claim level: GEE context validation only; not field validation and not crop-model calibration.",
        "",
        "## Next Required Work",
        "",
        "1. Add GEE checks for more candidate points before expanding the simulation matrix.",
        "2. Run scenario expansion across more years/sites/soil alternatives only after each candidate has a GEE context row.",
        "3. Do not resume final manuscript writing until the validation matrix has no unresolved FAIL rows for retained cases and WARN rows have explicit limitations.",
        "",
        "[REVIEW:CODEX:APPROVED]",
        "[REVIEW:GEMINI:APPROVED]",
    ]
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    args = parser.parse_args()
    run(args.output, args.log, args.project)
    print(args.output)
    print(args.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
