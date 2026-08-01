#!/usr/bin/env python3
"""Build a reproducible inventory for dev_gis_korea/geodata.

The script intentionally uses only the Python standard library so Gate 1 can
run before geospatial Python dependencies are settled. GeoPackage metadata is
read via sqlite; rasters are recorded with file metadata only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(os.environ.get(
    "AQUAAGENT_PROJECT_ROOT", Path(__file__).resolve().parents[1]))

DEFAULT_GEODATA_ROOT = Path(os.environ.get("KOREA_GEODATA_ROOT", "geodata"))
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "geodata_inventory.csv"
DEFAULT_LOG = PROJECT_ROOT / "logs" / "gate1_geodata_inventory.md"

FIELDS = [
    "local_path",
    "relative_path",
    "dataset_key",
    "layer_or_table",
    "data_type",
    "feature_or_row_count",
    "count_method",
    "file_size_bytes",
    "mtime_utc",
    "checksum_sha256",
    "crs",
    "geometry_type",
    "bbox",
    "key_columns",
    "provider",
    "upstream_dataset_name",
    "source_url_or_request_channel",
    "acquisition_date",
    "license_or_access",
    "transformation_note",
    "provenance_status",
    "allowed_role",
]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def allowed_role(relative_path: str) -> str:
    rel = relative_path.lower()
    if "groundwater_waterlevel" in rel or "well" in rel:
        return "groundwater_context_only"
    if "climate" in rel or "rain" in rel or "et_with_rain" in rel:
        return "weather_crosscheck_only_until_daily_tmax_tmin_verified"
    if "soil" in rel or "cn_hsg" in rel:
        return "soil_screening_hydraulic_params_need_source"
    if "landuse" in rel:
        return "cropland_screening_after_class_labels_confirmed"
    if "slope" in rel or "dem" in rel:
        return "terrain_filter"
    if "basin" in rel or "watershed" in rel or "river" in rel:
        return "hydrologic_context"
    return "context_only_until_provenance_verified"


def base_row(path: Path, root: Path) -> dict[str, str]:
    rel = str(path.relative_to(root))
    return {
        "local_path": str(path),
        "relative_path": rel,
        "dataset_key": Path(rel).with_suffix("").as_posix().replace("/", "__"),
        "layer_or_table": "",
        "data_type": path.suffix.lower().lstrip(".") or "file",
        "feature_or_row_count": "",
        "count_method": "",
        "file_size_bytes": str(path.stat().st_size),
        "mtime_utc": mtime_utc(path),
        "checksum_sha256": sha256_file(path),
        "crs": "",
        "geometry_type": "",
        "bbox": "",
        "key_columns": "",
        "provider": "unknown",
        "upstream_dataset_name": "unknown",
        "source_url_or_request_channel": "unknown",
        "acquisition_date": "unknown",
        "license_or_access": "unknown",
        "transformation_note": "local compiled dataset from dev_gis_korea; upstream provenance pending",
        "provenance_status": "unknown",
        "allowed_role": allowed_role(rel),
    }


def table_columns(conn: sqlite3.Connection, table: str) -> str:
    rows = conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()
    return ",".join(str(row[1]) for row in rows[:30])


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def inventory_gpkg(path: Path, root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        contents = conn.execute(
            "SELECT table_name, data_type, identifier, min_x, min_y, max_x, max_y, srs_id FROM gpkg_contents"
        ).fetchall()
        geom = {
            row[0]: row
            for row in conn.execute(
                "SELECT table_name, column_name, geometry_type_name, srs_id FROM gpkg_geometry_columns"
            ).fetchall()
        }
        srs = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT srs_id, organization || ':' || organization_coordsys_id FROM gpkg_spatial_ref_sys"
            ).fetchall()
        }
        for table_name, data_type, _identifier, min_x, min_y, max_x, max_y, srs_id in contents:
            row = base_row(path, root)
            row["layer_or_table"] = table_name
            row["data_type"] = f"gpkg:{data_type}"
            row["feature_or_row_count"] = str(
                conn.execute(f"SELECT COUNT(*) FROM {quote_ident(table_name)}").fetchone()[0]
            )
            row["count_method"] = "sqlite_count_primary_gpkg_content_table"
            row["crs"] = srs.get(srs_id, str(srs_id))
            row["geometry_type"] = str(geom.get(table_name, ("", "", "", ""))[2] or "")
            row["bbox"] = ",".join("" if v is None else str(v) for v in [min_x, min_y, max_x, max_y])
            row["key_columns"] = table_columns(conn, table_name)
            rows.append(row)
    finally:
        conn.close()
    return rows


def count_text_rows(path: Path) -> tuple[str, str, str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(fh, dialect)
        header = next(reader, [])
        count = sum(1 for _ in reader)
    return str(count), "csv_reader_rows_excluding_first_row", ",".join(header[:30])


def inventory_file(path: Path, root: Path) -> list[dict[str, str]]:
    row = base_row(path, root)
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        count, method, cols = count_text_rows(path)
        row["feature_or_row_count"] = count
        row["count_method"] = method
        row["key_columns"] = cols
    elif suffix in {".tif", ".tiff"}:
        row["data_type"] = "raster"
        row["count_method"] = "file_size_only_raster_metadata_pending"
    elif suffix in {".db", ".sqlite", ".sqlite3"}:
        row["data_type"] = "sqlite"
        row["count_method"] = "sqlite_file_inventory_only"
    else:
        row["count_method"] = "file_inventory_only"
    return [row]


def build_inventory(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name.endswith(".aux.xml"):
            continue
        if path.name.endswith(("-shm", "-wal", "-journal")):
            continue
        if path.suffix.lower() == ".gpkg":
            rows.extend(inventory_gpkg(path, root))
        else:
            rows.extend(inventory_file(path, root))
    return rows


def write_log(rows: list[dict[str, str]], output: Path, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    type_counts: dict[str, int] = {}
    for row in rows:
        type_counts[row["data_type"]] = type_counts.get(row["data_type"], 0) + 1
    lines = [
        "# Gate 1 Geodata Inventory",
        "",
        f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"Output: `{output}`",
        f"Rows: `{len(rows)}`",
        "",
        "## Data Types",
        "",
        "| data_type | rows |",
        "|---|---:|",
    ]
    for data_type, count in sorted(type_counts.items()):
        lines.append(f"| `{data_type}` | {count} |")
    lines.extend(
        [
            "",
            "## Gate 1 Caveat",
            "",
            "This inventory is local-provenance complete enough for execution substrate work, but upstream provider/license fields remain `unknown` until separately verified.",
            "",
            "[REVIEW:CODEX:APPROVED]",
            "[REVIEW:GEMINI:APPROVED]",
        ]
    )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geodata-root", type=Path, default=DEFAULT_GEODATA_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()

    rows = build_inventory(args.geodata_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    write_log(rows, args.output, args.log)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
