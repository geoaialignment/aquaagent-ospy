"""
Graphical abstract policy guard.

Paper-facing graphical abstracts must be prepared as publication artwork
(PaperBanana or equivalent), not generated as Matplotlib/Mermaid flowcharts.

This script intentionally does not draw a graphical abstract. It verifies that
the curated raster/PDF assets are present and exits with a clear message.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "figures" / "graphical_abstract.png",
    ROOT / "figures" / "graphical_abstract.pdf",
    ROOT / "figures" / "paperbanana_aquaagent_workflow.png",
]


def main() -> int:
    missing = [str(path) for path in REQUIRED if not path.exists()]
    if missing:
        print("Missing publication-art graphical abstract assets:")
        for path in missing:
            print(f"  - {path}")
        return 1

    print("Graphical abstract assets are curated publication artwork.")
    print("No Matplotlib/Mermaid flowchart generation is permitted for this figure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
