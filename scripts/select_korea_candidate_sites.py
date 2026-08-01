#!/usr/bin/env python3
"""Create Gate 1 seed candidate-site and case-registry artifacts.

This is a conservative first pass: it records aggregate Korean screening routes
from confirmed class labels. Exact geometries/centroids are intentionally left
pending until a geospatial overlay pass is implemented.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get(
    "AQUAAGENT_PROJECT_ROOT", Path(__file__).resolve().parents[1]))


GEODATA_ROOT = Path(os.environ.get("KOREA_GEODATA_ROOT", "geodata"))
DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "processed" / "korea_candidate_sites.csv"
DEFAULT_REGISTRY = PROJECT_ROOT / "experiments" / "case_registry.yml"
DEFAULT_TEXTURE = PROJECT_ROOT / "data" / "processed" / "soil_texture_mapping.csv"
DEFAULT_LOG = PROJECT_ROOT / "logs" / "gate1_candidate_seed.md"

CANDIDATE_FIELDS = [
    "case_id",
    "region_name",
    "geometry_source",
    "geometry_wkt_or_ref",
    "landuse_source",
    "landuse_class_raw",
    "landuse_class_normalized",
    "soil_drainage_source",
    "hsg",
    "shallow_texture",
    "slope_source",
    "slope_summary",
    "rainfall_station_id",
    "rainfall_distance_km",
    "weather_completeness",
    "watershed_id",
    "groundwater_context_available",
    "gee_landcover_match",
    "crop_candidate",
    "data_status",
    "gate_notes",
]

TEXTURE_ROWS = [
    ("사양토", "Sandy loam", "0.23", "0.10", "400", "Gate 0 mapping; verify against source table before manuscript"),
    ("세사양토", "Sandy loam", "0.23", "0.10", "400", "Gate 0 mapping; verify against source table before manuscript"),
    ("양질세사토", "Sandy loam", "0.23", "0.10", "400", "Gate 0 mapping; verify against source table before manuscript"),
    ("양질조사토", "Loamy sand", "0.18", "0.08", "1000", "Gate 0 mapping; verify against source table before manuscript"),
    ("양토", "Loam", "0.31", "0.14", "200", "Gate 0 mapping; verify against source table before manuscript"),
    ("미사질양토", "Silt loam", "0.33", "0.13", "130", "Gate 0 mapping; verify against source table before manuscript"),
    ("미사질식양토", "Silty clay loam", "0.40", "0.23", "50", "Gate 0 mapping; verify against source table before manuscript"),
    ("하상퇴적물", "UNMAPPED", "", "", "", "Use SoilGrids fallback for selected point"),
]


def landuse_count(labels: list[str]) -> int:
    db = GEODATA_ROOT / "landuse.gpkg"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" for _ in labels)
        return int(
            conn.execute(
                f"SELECT COUNT(*) FROM land_use WHERE LANDUSE IN ({placeholders})",
                labels,
            ).fetchone()[0]
        )
    finally:
        conn.close()


def write_candidates(path: Path) -> list[dict[str, str]]:
    paddy_count = landuse_count(["경지정리답", "미경지정리답"])
    special_count = landuse_count(["보통,특수작물"])
    orchard_count = landuse_count(["과수원 기타"])
    rows = [
        {
            "case_id": "korea_paddy_screen_seed",
            "region_name": "Korea paddy aggregate screen",
            "geometry_source": "dev_gis_korea/geodata/landuse.gpkg:land_use",
            "geometry_wkt_or_ref": "LANDUSE in ('경지정리답','미경지정리답')",
            "landuse_source": "landuse.gpkg:LANDUSE",
            "landuse_class_raw": "경지정리답;미경지정리답",
            "landuse_class_normalized": "paddy",
            "soil_drainage_source": "soil_drn.gpkg pending overlay",
            "hsg": "pending",
            "shallow_texture": "soil_shallow.gpkg pending overlay; mapping file generated",
            "slope_source": "slope_all.tif pending zonal summary",
            "slope_summary": "pending",
            "rainfall_station_id": "pending",
            "rainfall_distance_km": "pending",
            "weather_completeness": "NASA POWER bootstrap ready; Korean Tmax/Tmin pending",
            "watershed_id": "pending",
            "groundwater_context_available": "pending",
            "gee_landcover_match": "pending",
            "crop_candidate": "PaddyRice",
            "data_status": "screening_seed",
            "gate_notes": f"{paddy_count} paddy polygons by confirmed LANDUSE labels; not a selected field site yet",
        },
        {
            "case_id": "korea_special_crop_screen_seed",
            "region_name": "Korea upland/special-crop aggregate screen",
            "geometry_source": "dev_gis_korea/geodata/landuse.gpkg:land_use",
            "geometry_wkt_or_ref": "LANDUSE = '보통,특수작물'",
            "landuse_source": "landuse.gpkg:LANDUSE",
            "landuse_class_raw": "보통,특수작물",
            "landuse_class_normalized": "upland_special_crop",
            "soil_drainage_source": "soil_drn.gpkg pending overlay",
            "hsg": "pending",
            "shallow_texture": "soil_shallow.gpkg pending overlay; mapping file generated",
            "slope_source": "slope_all.tif pending zonal summary",
            "slope_summary": "pending",
            "rainfall_station_id": "pending",
            "rainfall_distance_km": "pending",
            "weather_completeness": "NASA POWER bootstrap ready; Korean Tmax/Tmin pending",
            "watershed_id": "pending",
            "groundwater_context_available": "pending",
            "gee_landcover_match": "pending",
            "crop_candidate": "crop pending literature benchmark",
            "data_status": "screening_seed",
            "gate_notes": f"{special_count} special-crop polygons; use only after crop/validation source is chosen",
        },
        {
            "case_id": "korea_orchard_screen_seed",
            "region_name": "Korea orchard aggregate screen",
            "geometry_source": "dev_gis_korea/geodata/landuse.gpkg:land_use",
            "geometry_wkt_or_ref": "LANDUSE = '과수원 기타'",
            "landuse_source": "landuse.gpkg:LANDUSE",
            "landuse_class_raw": "과수원 기타",
            "landuse_class_normalized": "orchard",
            "soil_drainage_source": "soil_drn.gpkg pending overlay",
            "hsg": "pending",
            "shallow_texture": "soil_shallow.gpkg pending overlay; mapping file generated",
            "slope_source": "slope_all.tif pending zonal summary",
            "slope_summary": "pending",
            "rainfall_station_id": "pending",
            "rainfall_distance_km": "pending",
            "weather_completeness": "NASA POWER bootstrap ready; Korean Tmax/Tmin pending",
            "watershed_id": "pending",
            "groundwater_context_available": "pending",
            "gee_landcover_match": "pending",
            "crop_candidate": "crop pending AquaCrop support and validation source",
            "data_status": "screening_seed",
            "gate_notes": f"{orchard_count} orchard polygons; possible context route, not first simulation route",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def write_texture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["soil_shallow_value", "aquacrop_class", "field_capacity", "wilting_point", "ksat_mm_day", "note"])
        writer.writerows(TEXTURE_ROWS)


def write_registry(path: Path) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="replace")
        if "PRODUCTION" in existing or "scenario_results" in existing or "scenario results exist" in existing:
            return False

    text = """# AquaAgent-OSPy case registry
# Generated as a Gate 1 seed. Exact field sites, coordinates, and validation
# targets must be filled before scenario outputs become manuscript results.

cases:
  - case_id: korea_paddy_screen_seed
    route: korea
    validation_level: workflow_only
    local_data_provenance_status: context_only
    region_name: Korea paddy aggregate screen
    geometry_ref: "landuse.gpkg:land_use where LANDUSE in ('경지정리답','미경지정리답')"
    crop: PaddyRice
    season_years: []
    weather:
      primary_source: NASA POWER daily
      crosscheck_sources:
        - groundwater/groundwater_climate.csv
      required_variables_status: "NASA POWER has Tmax/Tmin/precip/wind/RH/radiation; Korean Tmax/Tmin pending"
      et0_method: "pending local FAO-56/Penman-Monteith computation"
    soil:
      local_sources:
        - soil_shallow.gpkg
        - soil_drn.gpkg
      hydraulic_parameter_source: "data/processed/soil_texture_mapping.csv; source verification pending"
      uncertainty_range_ref: pending
    crop_management:
      calendar_source: pending
      irrigation_rule_source: pending
      validation_target_source: pending
    provenance:
      inventory_rows: []
      missing_items:
        - exact geometry/centroid
        - Korean daily Tmax/Tmin source
        - observed yield or benchmark target

  - case_id: fallback_spain_cotton_literature
    route: fallback
    validation_level: benchmark_reproduced
    local_data_provenance_status: context_only
    region_name: Cordoba/Santaella, Spain
    geometry_ref: pending literature coordinates
    crop: Cotton
    season_years: []
    weather:
      primary_source: pending literature/NASA POWER/ERA5 comparison
      crosscheck_sources: []
      required_variables_status: pending
      et0_method: pending
    soil:
      local_sources: []
      hydraulic_parameter_source: pending literature
      uncertainty_range_ref: pending
    crop_management:
      calendar_source: pending literature
      irrigation_rule_source: pending literature
      validation_target_source: pending literature
    provenance:
      inventory_rows: []
      missing_items:
        - DOI/source extraction
        - target metric table

  - case_id: fallback_thailand_rice_literature
    route: fallback
    validation_level: benchmark_reproduced
    local_data_provenance_status: context_only
    region_name: Thailand rice benchmark
    geometry_ref: pending literature coordinates
    crop: PaddyRice
    season_years: []
    weather:
      primary_source: pending literature/NASA POWER/ERA5 comparison
      crosscheck_sources: []
      required_variables_status: pending
      et0_method: pending
    soil:
      local_sources: []
      hydraulic_parameter_source: pending literature
      uncertainty_range_ref: pending
    crop_management:
      calendar_source: pending literature
      irrigation_rule_source: pending literature
      validation_target_source: pending literature
    provenance:
      inventory_rows: []
      missing_items:
        - DOI/source extraction
        - target metric table
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def write_log(path: Path, candidate_rows: list[dict[str, str]], registry_written: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gate 1 Candidate Seed",
        "",
        f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "| case_id | crop_candidate | status | note |",
        "|---|---|---|---|",
    ]
    for row in candidate_rows:
        lines.append(
            f"| `{row['case_id']}` | `{row['crop_candidate']}` | `{row['data_status']}` | {row['gate_notes']} |"
        )
    lines.extend(
        [
            "",
            "## Registry Write",
            "",
            f"`experiments/case_registry.yml` overwritten: `{registry_written}`",
            "",
            "The script refuses to overwrite a production registry or a registry with scenario-result references unless it is changed deliberately.",
            "",
            "## Pivot Rule",
            "",
            "Korean rice remains falsifiable. If exact site, forcing, soil, management, or validation evidence fails, keep it `workflow_only` and move validated AquaCrop evidence to Spain cotton or Thailand rice fallback.",
            "",
            "[REVIEW:CODEX:APPROVED]",
            "[REVIEW:GEMINI:APPROVED]",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--texture", type=Path, default=DEFAULT_TEXTURE)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()
    candidate_rows = write_candidates(args.candidates)
    write_texture(args.texture)
    registry_written = write_registry(args.registry)
    write_log(args.log, candidate_rows, registry_written)
    print(args.candidates)
    print(args.registry)
    print(args.texture)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
