#!/usr/bin/env python3
"""Gate 0 probe for AquaCrop-OSPy availability.

This script is intentionally diagnostic only. It does not install packages or
modify environments. It records whether the current Python can import
``aquacrop`` and, when available, whether the crop names needed for the first
case are defined.
"""

from __future__ import annotations

import importlib
import inspect
import json
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = (
    PROJECT_ROOT
    / "communication"
    / "research"
    / "aquaagent_8h_20260502"
    / "gate0_aquacrop_import_check.md"
)


def _probe() -> dict:
    result: dict = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_executable": sys.executable,
        "python_version": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "import_aquacrop": False,
        "exports": [],
        "crop_signature": None,
        "predefined_crops": [],
        "crop_checks": {},
        "error": None,
        "traceback": None,
    }

    try:
        aquacrop = importlib.import_module("aquacrop")
        result["import_aquacrop"] = True
        result["aquacrop_file"] = getattr(aquacrop, "__file__", None)
        result["aquacrop_version"] = getattr(aquacrop, "__version__", None)

        for name in [
            "AquaCropModel",
            "Crop",
            "Soil",
            "InitialWaterContent",
            "IrrigationManagement",
        ]:
            if hasattr(aquacrop, name):
                result["exports"].append(name)

        Crop = getattr(aquacrop, "Crop")
        result["crop_signature"] = str(inspect.signature(Crop))

        try:
            crop_mod = importlib.import_module("aquacrop.entities.crop")
            crop_params = getattr(crop_mod, "crop_params", {})
            result["predefined_crops"] = sorted(str(k) for k in crop_params.keys())
        except Exception as exc:  # pragma: no cover - diagnostic fallback
            result["predefined_crops_error"] = f"{type(exc).__name__}: {exc}"

        for crop_name in ["Rice", "PaddyRice", "PaddyRiceGDD", "localpaddy", "Cotton", "Maize", "Wheat"]:
            try:
                crop = Crop(crop_name, planting_date="05/25")
                result["crop_checks"][crop_name] = {
                    "ok": True,
                    "resolved_name": getattr(crop, "Name", None) or getattr(crop, "name", None),
                }
            except Exception as exc:
                result["crop_checks"][crop_name] = {
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    return result


def _write_markdown(result: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if result["import_aquacrop"] else "BLOCKED"
    paddy_ok = any(
        result.get("crop_checks", {}).get(name, {}).get("ok")
        for name in ("PaddyRice", "PaddyRiceGDD", "localpaddy")
    )
    rice_literal_ok = result.get("crop_checks", {}).get("Rice", {}).get("ok", False)

    lines = [
        "# Gate 0 AquaCrop-OSPy Import Check",
        "",
        f"Status: **{status}**",
        f"Timestamp UTC: `{result['timestamp_utc']}`",
        "",
        "## Environment",
        "",
        f"- Python executable: `{result['python_executable']}`",
        f"- Python version: `{result['python_version']}`",
        f"- Platform: `{result['platform']}`",
        "",
        "## Import Result",
        "",
        f"- `import aquacrop`: `{result['import_aquacrop']}`",
        f"- aquacrop file: `{result.get('aquacrop_file')}`",
        f"- aquacrop version: `{result.get('aquacrop_version')}`",
        f"- exports: `{', '.join(result.get('exports', []))}`",
        "",
        "## Crop Name Check",
        "",
        f"- Literal `Rice`: `{rice_literal_ok}`",
        f"- Paddy rice alternatives (`PaddyRice`, `PaddyRiceGDD`, `localpaddy`): `{paddy_ok}`",
        "",
        "| crop name | ok | detail |",
        "|---|---:|---|",
    ]
    for crop_name, check in result.get("crop_checks", {}).items():
        detail = check.get("resolved_name") or check.get("error", "")
        detail = str(detail).replace("\n", " ")
        lines.append(f"| `{crop_name}` | {check.get('ok')} | {detail} |")

    lines.extend(
        [
            "",
            "## Predefined Crops",
            "",
            ", ".join(f"`{name}`" for name in result.get("predefined_crops", [])) or "(none)",
            "",
            "## Gate 0 Decision",
            "",
        ]
    )
    if result["import_aquacrop"] and paddy_ok:
        lines.append(
            "Gate 0 environment is usable in this Python. Do not use literal `Rice`; use `PaddyRice`, `PaddyRiceGDD`, or `localpaddy` after choosing calendar assumptions."
        )
    elif result["import_aquacrop"]:
        lines.append(
            "AquaCrop imports, but paddy rice naming is unresolved. Do not start the Korean rice case until crop-name/template mapping is fixed."
        )
    else:
        lines.append(
            "AquaCrop is not importable in this Python. Use another environment or install dependencies before scenario work."
        )
        if result.get("error"):
            lines.extend(["", "Error:", "", f"```text\n{result['error']}\n```"])
        if result.get("traceback"):
            lines.extend(["", "Traceback:", "", f"```text\n{result['traceback']}\n```"])

    lines.extend(
        [
            "",
            "## Raw JSON",
            "",
            "```json",
            json.dumps(result, ensure_ascii=False, indent=2),
            "```",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    result = _probe()
    _write_markdown(result, out_path)
    print(out_path)
    return 0 if result["import_aquacrop"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
