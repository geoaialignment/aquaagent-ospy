"""
Adversarial audit for the AquaAgent-OSPy memo faithfulness rubric.

This does not replace external agronomist evaluation or stochastic LLM
trajectory testing. It checks a narrower but important property: when an
otherwise valid memo is modified to include unsupported numeric claims, the
F1/F2 numeric traceability checks should fail.
"""

import csv
from pathlib import Path

from evaluate_memo_faithfulness import evaluate


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_CSV = ROOT / "data/processed/scenario_results_soilgrids_corrected.csv"
OUT_DIR = ROOT / "data/processed/memo_adversarial"
OUT_CSV = ROOT / "data/processed/memo_adversarial_audit.csv"
SUMMARY_MD = ROOT / "communication/research/aquaagent_8h_20260502/memo_adversarial_audit.md"


CASES = [
    {
        "case_id": "case1_gimje",
        "year": 2019,
        "memo": ROOT / "experiments/memos/memo_case1_gimje_2019_soilcorrected.md",
        "pareto": ROOT / "data/processed/pareto_front_case1_gimje_2019_soilcorrected.csv",
        "trace": ROOT / "data/processed/tool_trace_case1_gimje_2019_soilcorrected.json",
    },
    {
        "case_id": "case1_gimje",
        "year": 2015,
        "memo": ROOT / "experiments/memos/memo_case1_gimje_2015_dry.md",
        "pareto": ROOT / "data/processed/pareto_front_case1_gimje_2015.csv",
        "trace": ROOT / "data/processed/tool_trace_case1_gimje_2015.json",
    },
    {
        "case_id": "case2_hampyeong",
        "year": 2022,
        "memo": ROOT / "experiments/memos/memo_case2_hampyeong_2022.md",
        "pareto": ROOT / "data/processed/pareto_front_case2_hampyeong_2022.csv",
        "trace": ROOT / "data/processed/tool_trace_case2_hampyeong_2022.json",
    },
    {
        "case_id": "case2_hampyeong",
        "year": 2015,
        "memo": ROOT / "experiments/memos/memo_case2_hampyeong_2015.md",
        "pareto": ROOT / "data/processed/pareto_front_case2_hampyeong_2015.csv",
        "trace": ROOT / "data/processed/tool_trace_case2_hampyeong_2015.json",
    },
]


ADVERSARIAL_SENTENCE = (
    "\n\nAdversarial inserted claim for audit only: apply 999.9 mm irrigation "
    "to achieve 99.9 t/ha yield and 9.999 kg/m3 water productivity.\n"
)


def bool_result(value: bool) -> str:
    return "PASS" if value else "FAIL"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for case in CASES:
        baseline = evaluate(
            case["memo"],
            SCENARIO_CSV,
            case["pareto"],
            case["trace"],
            case["case_id"],
            case["year"],
        )

        adv_memo = OUT_DIR / f"{case['case_id']}_{case['year']}_adversarial.md"
        adv_memo.write_text(case["memo"].read_text() + ADVERSARIAL_SENTENCE)
        adversarial = evaluate(
            adv_memo,
            SCENARIO_CSV,
            case["pareto"],
            case["trace"],
            case["case_id"],
            case["year"],
        )

        rows.append(
            {
                "case_id": case["case_id"],
                "year": case["year"],
                "baseline_pass_count": baseline["pass_count"],
                "baseline_categorical_failure": baseline["categorical_failure"],
                "adversarial_pass_count": adversarial["pass_count"],
                "adversarial_categorical_failure": adversarial["categorical_failure"],
                "adversarial_F1": bool_result(adversarial["F1_traceability"]),
                "adversarial_F2": bool_result(adversarial["F2_no_hallucination"]),
                "detected_injected_hallucination": (
                    (not baseline["categorical_failure"])
                    and adversarial["categorical_failure"]
                    and (not adversarial["F1_traceability"])
                    and (not adversarial["F2_no_hallucination"])
                ),
            }
        )

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    detected = sum(r["detected_injected_hallucination"] for r in rows)
    total = len(rows)
    with SUMMARY_MD.open("w") as f:
        f.write("# Memo Adversarial Audit\n\n")
        f.write("Date: 2026-05-02\n\n")
        f.write(
            "Purpose: test whether the F1/F2 numeric faithfulness checks fail "
            "when unsupported numeric claims are deliberately inserted into "
            "otherwise valid action memos.\n\n"
        )
        f.write(f"Result: {detected}/{total} injected hallucinations detected.\n\n")
        f.write(
            "Scope note: this is an adversarial unit audit of the rubric, not a "
            "replacement for external agronomist evaluation (C2) or large-N "
            "stochastic prompt-variation testing.\n\n"
        )
        f.write("| case | year | baseline | adversarial F1 | adversarial F2 | detected |\n")
        f.write("|---|---:|---:|---|---|---|\n")
        for r in rows:
            f.write(
                f"| {r['case_id']} | {r['year']} | {r['baseline_pass_count']}/5 | "
                f"{r['adversarial_F1']} | {r['adversarial_F2']} | "
                f"{r['detected_injected_hallucination']} |\n"
            )

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Detected {detected}/{total} injected hallucinations")


if __name__ == "__main__":
    main()
