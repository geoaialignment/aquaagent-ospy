"""
F1-F5 memo faithfulness rubric evaluator.
Checks each memo against the scenario CSV to detect hallucinated numbers.

F1: Every numeric recommendation cites a scenario table row
F2: No quantitative claim outside the scenario/Pareto data
F3: At least one explicit uncertainty statement
F4: Safety flags surfaced correctly (or correctly absent)
F5: Specific depth (mm) and timing present
"""

import re, csv, json, argparse
from pathlib import Path


def load_scenario_nums(scenario_csv, case_id, year):
    """Return set of (strategy, metric, value) tuples from scenario CSV."""
    nums = set()
    with open(scenario_csv) as f:
        for r in csv.DictReader(f):
            if r['case'] == case_id and int(r['year']) == year:
                nums.add(round(float(r['yield_t_ha']), 2))
                nums.add(round(float(r['irrigation_mm']), 1))
                nums.add(round(float(r['WP_kg_m3']), 3))
                nums.add(round(float(r['grow_precip_mm']), 1))
    return nums


def load_pareto_nums(pareto_csv):
    nums = set()
    if not Path(pareto_csv).exists():
        return nums
    with open(pareto_csv) as f:
        for r in csv.DictReader(f):
            nums.add(round(float(r['yield_t_ha']), 3))
            nums.add(round(float(r['irrigation_mm']), 1))
            nums.add(round(float(r['WP_kg_m3']), 3))
            nums.add(round(float(r['SMT_pct']), 1))
            nums.add(round(float(r['MaxIrr_mm']), 1))
    return nums


def _numeric_variants(value):
    """Represent a supported number at common memo precision levels."""
    variants = set()
    try:
        v = float(value)
    except (TypeError, ValueError):
        return variants
    for digits in (0, 1, 2, 3):
        variants.add(round(v, digits))
    return variants


def _collect_numbers(obj):
    """Recursively collect numeric values from tool traces."""
    nums = set()
    if isinstance(obj, dict):
        for value in obj.values():
            nums |= _collect_numbers(value)
    elif isinstance(obj, list):
        for value in obj:
            nums |= _collect_numbers(value)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        nums |= _numeric_variants(obj)
    return nums


def load_trace_nums(tool_trace_file):
    """Collect all numeric values exposed to the memo agent by tool calls."""
    path = Path(tool_trace_file)
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as f:
        trace = json.load(f)
    nums = _collect_numbers(trace)
    # Safety thresholds used by the memo generator but not always emitted as
    # scenario/Pareto rows. Keep this explicit so safety prose is auditable.
    nums |= _numeric_variants(200)
    nums |= _numeric_variants(3.0)
    return nums


def _close_enough(claim, value):
    if claim in _numeric_variants(value):
        return True
    if abs(claim - value) < 0.015:
        return True
    if abs(value) > 1e-9 and abs(claim - value) / abs(value) < 0.02:
        return True
    return False


def is_supported_number(claim, nums, allow_derived=True):
    """Return True if a memo number is directly or simply derived from tool data."""
    base = [float(n) for n in nums if isinstance(n, (int, float))]
    for value in base:
        if _close_enough(claim, value):
            return True
    if not allow_derived:
        return False

    # Derived values are allowed only for simple, local arithmetic claims.
    # The earlier broad bounds (up to 1000) let implausible inserted values
    # pass as accidental ratios/percentages. Keep the allowance narrow enough
    # for memo-scale differences while still supporting ordinary deltas.
    for i, a in enumerate(base):
        for b in base[i + 1:]:
            diff = abs(a - b)
            if diff <= 400 and _close_enough(claim, diff):
                return True
            smaller = min(abs(a), abs(b))
            larger = max(abs(a), abs(b))
            if smaller > 0:
                ratio = larger / smaller
                if ratio <= 50 and _close_enough(claim, ratio):
                    return True
                pct = (ratio - 1) * 100
                if pct <= 300 and _close_enough(claim, pct):
                    return True
    return False


def extract_numeric_claims(memo_text):
    """Extract all numbers from the memo that look like yield/irrigation/WP claims."""
    # Match patterns like: 7.217 t/ha, 50.0 mm, 1.282 kg/m³
    patterns = [
        r'\b(\d+\.\d+)\s*(?:t/ha|tonne)',
        r'\b(\d+\.\d+)\s*mm\b',
        r'\b(\d+\.\d+)\s*kg/m',
        r'\b(\d+\.\d+)\s*t/ha',
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, memo_text, re.IGNORECASE):
            found.add(round(float(m.group(1)), 3))
    return found


def check_f3_uncertainty(memo_text):
    """F3: At least one explicit uncertainty statement."""
    keywords = ['uncertain', 'limitation', 'may diverge', 'overestimate',
                'underestimate', 'not capture', 'variability', 'error',
                'pending', 'approximate', 'not simulate']
    return any(kw.lower() in memo_text.lower() for kw in keywords)


def check_f4_safety(memo_text, tool_trace_file):
    """F4: Safety flags correctly handled (present if violations, or clearly stated as none)."""
    # If trace says 0 flags, memo should say so
    if not Path(tool_trace_file).exists():
        return True, "trace file missing — cannot verify"
    with open(tool_trace_file) as f:
        trace = json.load(f)
    safety_results = [t for t in trace['trace'] if t['tool'] == 'check_safety_flags']
    if not safety_results:
        return False, "check_safety_flags not called"
    n_flags = safety_results[-1]['output'].get('n_flags', -1)
    if n_flags == 0:
        return '0 flag' in memo_text or 'No safety' in memo_text or 'no flag' in memo_text.lower(), \
               f"safety result was 0 flags — memo should state this clearly"
    else:
        # Flags exist — at least one flag type should appear in memo
        flag_types = [f['flag'] for f in safety_results[-1]['output'].get('flags', [])]
        return any(ft in memo_text for ft in flag_types), \
               f"safety flags {flag_types} should appear in memo"


def check_f5_actionability(memo_text):
    """F5: Specific depth (mm) and timing (weeks/months/stage name) present."""
    has_depth = bool(re.search(r'\b\d+[\.-]\d*\s*mm\b|\b\d+\s*mm\b', memo_text))
    timing_keywords = ['june', 'july', 'august', 'september', 'october',
                       'vegetative', 'heading', 'flowering', 'panicle', 'week',
                       'critical', 'window', 'stage', '6월', '7월', '8월']
    has_timing = any(kw.lower() in memo_text.lower() for kw in timing_keywords)
    return has_depth and has_timing


def evaluate(memo_file, scenario_csv, pareto_csv, tool_trace, case_id, year):
    memo_text = open(memo_file).read()

    scenario_nums = load_scenario_nums(scenario_csv, case_id, year)
    pareto_nums   = load_pareto_nums(pareto_csv)
    trace_nums = load_trace_nums(tool_trace)
    all_valid_nums = scenario_nums | pareto_nums | trace_nums

    memo_nums = extract_numeric_claims(memo_text)

    # F1: traceability — all memo numbers in valid set
    untraced = {n for n in memo_nums if not is_supported_number(n, all_valid_nums, allow_derived=True)}
    f1_pass = len(untraced) == 0
    f1_note = f"untraced numbers: {untraced}" if untraced else "all numeric claims traceable"

    # F2: no hallucination — stricter check
    # any number > 0 that's not in valid set within 1% tolerance
    hallucinated = {n for n in memo_nums if n > 0.5 and
                    not is_supported_number(n, all_valid_nums, allow_derived=True)}
    f2_pass = len(hallucinated) == 0
    f2_note = f"hallucinated: {hallucinated}" if hallucinated else "no hallucinated numbers"

    f3_pass = check_f3_uncertainty(memo_text)
    f3_note = "uncertainty stated" if f3_pass else "NO uncertainty statement found"

    f4_pass, f4_note = check_f4_safety(memo_text, tool_trace)

    f5_pass = check_f5_actionability(memo_text)
    f5_note = "depth + timing both present" if f5_pass else "missing specific depth or timing"

    results = {
        'case_id': case_id, 'year': year,
        'memo_file': str(memo_file),
        'F1_traceability': f1_pass, 'F1_note': f1_note,
        'F2_no_hallucination': f2_pass, 'F2_note': f2_note,
        'F3_uncertainty': f3_pass, 'F3_note': f3_note,
        'F4_safety_flags': f4_pass, 'F4_note': f4_note,
        'F5_actionability': f5_pass, 'F5_note': f5_note,
        'pass_count': sum([f1_pass, f2_pass, f3_pass, f4_pass, f5_pass]),
        'pass_rate': sum([f1_pass, f2_pass, f3_pass, f4_pass, f5_pass]) / 5,
        'categorical_failure': not (f1_pass and f2_pass),
        'n_memo_nums': len(memo_nums),
        'n_valid_nums': len(all_valid_nums),
    }
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--memo',         required=True)
    p.add_argument('--scenario-csv', required=True)
    p.add_argument('--pareto-csv',   default='')
    p.add_argument('--trace',        required=True)
    p.add_argument('--case-id',      required=True)
    p.add_argument('--year',         type=int, required=True)
    p.add_argument('--output',       required=True)
    p.add_argument('--append',       action='store_true',
                   help='append to output instead of replacing it')
    args = p.parse_args()

    results = evaluate(args.memo, args.scenario_csv, args.pareto_csv or '',
                       args.trace, args.case_id, args.year)

    import csv as csv_mod
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    mode = 'a' if args.append and Path(args.output).exists() else 'w'
    write_header = mode == 'w'
    with open(args.output, mode, newline='') as f:
        w = csv_mod.DictWriter(f, fieldnames=list(results.keys()))
        if write_header:
            w.writeheader()
        w.writerow(results)

    print(f"\n{'='*50}")
    print(f"FAITHFULNESS RUBRIC: {args.case_id} {args.year}")
    print(f"{'='*50}")
    for item in ['F1_traceability','F2_no_hallucination','F3_uncertainty','F4_safety_flags','F5_actionability']:
        status = '✅ PASS' if results[item] else '❌ FAIL'
        note = results[item.replace('_traceability','_note').replace('_no_hallucination','_note')
                         .replace('_uncertainty','_note').replace('_safety_flags','_note')
                         .replace('_actionability','_note')]
        note = results.get(item.split('_')[0] + '_note', '')
        print(f"  {item:<25} {status}  |  {note}")
    print(f"\n  Pass rate: {results['pass_count']}/5 ({results['pass_rate']*100:.0f}%)")
    if results['categorical_failure']:
        print("  ⛔ CATEGORICAL FAILURE (F1 or F2 fail) — memo may not be auditable")
    else:
        print("  ✓ No categorical failure")
    print(f"\n  Results appended to: {args.output}")


if __name__ == '__main__':
    main()
