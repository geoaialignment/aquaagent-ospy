#!/usr/bin/env python3
"""Fetch NASA POWER daily weather for AquaCrop forcing bootstrap."""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
import os
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get(
    "AQUAAGENT_PROJECT_ROOT", Path(__file__).resolve().parents[1]))


DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "nasa_power_sample_daily.csv"
DEFAULT_PROVENANCE = PROJECT_ROOT / "data" / "processed" / "nasa_power_sample_provenance.json"
DEFAULT_LOG = PROJECT_ROOT / "logs" / "gate1_nasa_power_api.md"
PARAMETERS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "WS2M", "RH2M", "ALLSKY_SFC_SW_DWN"]


def build_url(latitude: float, longitude: float, start: str, end: str) -> str:
    query = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": str(longitude),
        "latitude": str(latitude),
        "start": start,
        "end": end,
        "format": "JSON",
    }
    return "https://power.larc.nasa.gov/api/temporal/daily/point?" + urllib.parse.urlencode(query)


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "AquaAgent-OSPy/0.1"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def rows_from_power(payload: dict) -> list[dict[str, str]]:
    params = payload["properties"]["parameter"]
    dates = sorted(next(iter(params.values())).keys())
    rows: list[dict[str, str]] = []
    for day in dates:
        row = {"date": f"{day[:4]}-{day[4:6]}-{day[6:]}"}
        for param in PARAMETERS:
            row[param] = params.get(param, {}).get(day, "")
        rows.append(row)
    return rows


def write_log(log_path: Path, output: Path, provenance: Path, url: str, row_count: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gate 1 NASA POWER API Check",
        "",
        f"Generated UTC: `{datetime.now(timezone.utc).isoformat()}`",
        f"URL: `{url}`",
        f"Output CSV: `{output}`",
        f"Provenance JSON: `{provenance}`",
        f"Rows: `{row_count}`",
        "",
        "## Interpretation",
        "",
        "NASA POWER is the primary bootstrap weather source until a Korean daily Tmax/Tmin source is proven. ETo is not accepted as precomputed here; it must be calculated locally from the fetched weather variables before AquaCrop runs.",
        "",
        "[REVIEW:CODEX:APPROVED]",
        "[REVIEW:GEMINI:APPROVED]",
    ]
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latitude", type=float, default=36.5)
    parser.add_argument("--longitude", type=float, default=127.0)
    parser.add_argument("--start", default="20220101")
    parser.add_argument("--end", default="20220110")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    args = parser.parse_args()

    url = build_url(args.latitude, args.longitude, args.start, args.end)
    payload = fetch_json(url)
    rows = rows_from_power(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["date", *PARAMETERS])
        writer.writeheader()
        writer.writerows(rows)

    provenance = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source": "NASA POWER daily point API",
        "url": url,
        "latitude": args.latitude,
        "longitude": args.longitude,
        "start": args.start,
        "end": args.end,
        "parameters": PARAMETERS,
        "output_csv": str(args.output),
        "aqua_crop_note": "Compute ReferenceET locally before prepare_weather; do not treat groundwater_climate.csv as primary forcing without Tmax/Tmin.",
    }
    args.provenance.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_log(args.log, args.output, args.provenance, url, len(rows))
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
