"""
AquaAgent-OSPy action memo generator.
A4-class code-executing LLM tool-agent: reads scenario results and writes
an auditable irrigation action memo grounded in AquaCrop-OSPy outputs.

Usage:
    python3 generate_action_memo.py \
        --scenario-csv data/processed/scenario_results_all_cases.csv \
        --pareto-csv   data/processed/pareto_front_case1_chungnam_2019.csv \
        --case-id      case1_chungnam \
        --year         2019 \
        --output       experiments/memos/memo_case1_chungnam_2019.md \
        --trace        data/processed/tool_trace_case1_chungnam_2019.json
"""

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Tool implementations (the "tool world" the agent can call)
# ---------------------------------------------------------------------------

def tool_load_scenario_table(case_id: str, year: int, scenario_csv: str) -> dict:
    """Load scenario comparison results for a specific case and year."""
    rows = []
    with open(scenario_csv) as f:
        for r in csv.DictReader(f):
            if r['case'] == case_id and int(r['year']) == year:
                rows.append({
                    'strategy': r['strategy'],
                    'yield_t_ha': float(r['yield_t_ha']),
                    'irrigation_mm': float(r['irrigation_mm']),
                    'grow_precip_mm': float(r['grow_precip_mm']),
                    'WP_kg_m3': float(r['WP_kg_m3']),
                })
    return {'case_id': case_id, 'year': year, 'rows': rows, 'n_strategies': len(rows)}


def tool_load_pareto_front(pareto_csv: str) -> dict:
    """Load NSGA-2 Pareto front solutions."""
    rows = []
    with open(pareto_csv) as f:
        for r in csv.DictReader(f):
            rows.append({
                'SMT_pct': float(r['SMT_pct']),
                'MaxIrr_mm': float(r['MaxIrr_mm']),
                'yield_t_ha': float(r['yield_t_ha']),
                'irrigation_mm': float(r['irrigation_mm']),
                'WP_kg_m3': float(r['WP_kg_m3']),
            })
    best_wp  = max(rows, key=lambda x: x['WP_kg_m3'])
    best_yld = max(rows, key=lambda x: x['yield_t_ha'])
    return {
        'n_pareto_solutions': len(rows),
        'best_WP_solution': best_wp,
        'max_yield_solution': best_yld,
        'pareto_irrigation_range_mm': [
            min(r['irrigation_mm'] for r in rows),
            max(r['irrigation_mm'] for r in rows),
        ],
    }


def tool_load_site_context(case_id: str) -> dict:
    """Load site metadata from case_registry (no external call needed)."""
    registry = {
        'case1_chungnam': {
            'region': '충청남도 (Chungcheongnam-do), Korea',
            'lat': 36.9346, 'lon': 126.5540,
            'soil_type': 'ClayLoam', 'HSG': 'C',
            'crop': 'PaddyRice (transplanted)',
            'planting_date': 'May 25',
            'harvest_window': 'Oct 1–15',
            'gee_landcover': 'Cropland (ESA WorldCover check pending)',
            'nearest_kma_station': 616,
            'station_dist_km': 7.7,
        },
        'case2_jeonnam': {
            'region': '전라남도 (Jeollanam-do), Korea',
            'lat': 34.8236, 'lon': 127.9347,
            'soil_type': 'ClayLoam', 'HSG': 'C',
            'crop': 'PaddyRice (transplanted)',
            'planting_date': 'May 25',
            'harvest_window': 'Oct 1–15',
            'gee_landcover': 'Cropland (ESA WorldCover check pending)',
            'nearest_kma_station': 295,
            'station_dist_km': 0.6,
        },
        'case1_gimje': {
            'region': '김제시, 전라북도 (Gimje, Jeollabuk-do), Korea',
            'lat': 35.754, 'lon': 126.898,
            'soil_type': 'ClayLoam', 'HSG': 'C',
            'crop': 'PaddyRice (transplanted)',
            'planting_date': 'May 25',
            'harvest_window': 'Oct 1-15',
            'gee_landcover': 'Dynamic World crops_p=0.571; NDVI rice phenology PASS',
            'gee_weather_check': 'ERA5 vs NASA POWER: T MAE=0.8 C, monthly P corr=0.878',
            'nearest_kma_station': 'pending registry linkage',
            'station_dist_km': 'pending',
        },
        'case2_hampyeong': {
            'region': '함평군, 전라남도 (Hampyeong, Jeollanam-do), Korea',
            'lat': 35.070, 'lon': 126.540,
            'soil_type': 'ClayLoam', 'HSG': 'C',
            'crop': 'PaddyRice (transplanted)',
            'planting_date': 'May 25',
            'harvest_window': 'Oct 1-15',
            'gee_landcover': 'Dynamic World crops_p=0.506; NDVI rice phenology PASS',
            'gee_weather_check': 'ERA5 vs NASA POWER: T MAE=0.92 C, monthly P corr=0.667 WARN',
            'nearest_kma_station': 'pending registry linkage',
            'station_dist_km': 'pending',
        },
    }
    return registry.get(case_id, {'error': f'case_id {case_id} not found'})


def tool_load_weather_summary(case_id: str, year: int, weather_csv: str) -> dict:
    """Summarize growing-season weather from AquaCrop weather file."""
    rows = []
    with open(weather_csv) as f:
        for r in csv.DictReader(f):
            mo = int(r['Month'])
            if 5 <= mo <= 9:
                rows.append({
                    'tmax': float(r['MaxTemp']),
                    'tmin': float(r['MinTemp']),
                    'prec': float(r['Precipitation']),
                    'eto':  float(r['ReferenceET']),
                })
    if not rows:
        return {'error': 'no growing season data found'}
    return {
        'case_id': case_id, 'year': year,
        'period': 'May–September',
        'total_precip_mm': round(sum(r['prec'] for r in rows), 1),
        'total_eto_mm':    round(sum(r['eto']  for r in rows), 1),
        'mean_tmax_C':     round(sum(r['tmax'] for r in rows) / len(rows), 1),
        'mean_tmin_C':     round(sum(r['tmin'] for r in rows) / len(rows), 1),
        'source': 'NASA POWER Daily API (Hargreaves-Samani ETo)',
    }


def tool_check_safety_flags(scenario_rows: list) -> dict:
    """Check for strategies that violate safety thresholds."""
    flags = []
    for r in scenario_rows:
        if r['irrigation_mm'] > 200:
            flags.append({
                'strategy': r['strategy'],
                'flag': 'HIGH_IRRIGATION',
                'value_mm': r['irrigation_mm'],
                'threshold_mm': 200,
                'message': f"Irrigation {r['irrigation_mm']:.0f}mm exceeds 200mm safety threshold — verify field capacity and drainage.",
            })
        if r['yield_t_ha'] < 3.0:
            flags.append({
                'strategy': r['strategy'],
                'flag': 'LOW_YIELD',
                'value_t_ha': r['yield_t_ha'],
                'threshold_t_ha': 3.0,
                'message': f"Yield {r['yield_t_ha']:.2f} t/ha below 3.0 t/ha — possible calibration or weather issue.",
            })
    return {'n_flags': len(flags), 'flags': flags}


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "load_scenario_table",
        "description": "Load AquaCrop-OSPy scenario comparison results (yield, irrigation, WP) for a given case and year.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Case identifier, e.g. case1_chungnam"},
                "year":    {"type": "integer", "description": "Simulation year, e.g. 2019"},
            },
            "required": ["case_id", "year"],
        },
    },
    {
        "name": "load_pareto_front",
        "description": "Load NSGA-2 Pareto front: best yield, best WP, and irrigation range from optimizer results.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "load_site_context",
        "description": "Load site metadata: region, coordinates, soil type, crop, planting calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "load_weather_summary",
        "description": "Summarize growing-season weather: total precipitation, ETo, mean temperatures.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "year":    {"type": "integer"},
            },
            "required": ["case_id", "year"],
        },
    },
    {
        "name": "check_safety_flags",
        "description": "Check scenario results for safety violations: excessive irrigation (>200mm) or very low yield (<3 t/ha).",
        "input_schema": {
            "type": "object",
            "properties": {
                "scenario_rows": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "List of scenario result dicts with strategy, yield_t_ha, irrigation_mm.",
                },
            },
            "required": ["scenario_rows"],
        },
    },
]


def dispatch_tool(tool_name: str, tool_input: dict, paths: dict) -> dict:
    if tool_name == "load_scenario_table":
        return tool_load_scenario_table(
            tool_input["case_id"], tool_input["year"], paths["scenario_csv"]
        )
    elif tool_name == "load_pareto_front":
        return tool_load_pareto_front(paths["pareto_csv"])
    elif tool_name == "load_site_context":
        return tool_load_site_context(tool_input["case_id"])
    elif tool_name == "load_weather_summary":
        return tool_load_weather_summary(
            tool_input["case_id"], tool_input["year"], paths["weather_csv"]
        )
    elif tool_name == "check_safety_flags":
        return tool_check_safety_flags(tool_input["scenario_rows"])
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are AquaAgent-OSPy, an A4-class code-executing advisory agent
for irrigation decision support. You have access to tools that read AquaCrop-OSPy
simulation results, Pareto optimizer outputs, site metadata, and weather summaries.

Your task is to generate a structured, auditable irrigation action memo for an agronomist.

Rules:
1. Call all available tools before writing the memo — you must have full evidence.
2. Every quantitative recommendation in the memo MUST cite the specific strategy row or
   Pareto solution it comes from. No numbers invented from prior knowledge.
3. State at least one explicit uncertainty (weather forecast, soil parameter, model limitation).
4. Flag any safety issues found by the safety checker.
5. Give a specific recommended irrigation depth (mm) and timing strategy — not vague advice.
6. Do NOT claim you are an autonomous controller. You are an advisory tool; a human agronomist
   must approve and execute the recommendation.
7. Format the memo in Markdown with sections: Summary, Site & Weather Context,
   Scenario Comparison, Pareto Optimizer Findings, Recommendation, Safety Notes,
   Uncertainty & Limitations, Provenance."""


def run_agent(case_id: str, year: int, paths: dict) -> tuple[str, list]:
    """Run the tool-calling agent loop. Returns (memo_text, tool_trace)."""
    client = anthropic.Anthropic()
    messages = [
        {
            "role": "user",
            "content": (
                f"Generate an irrigation action memo for {case_id}, year {year}. "
                f"Use all available tools to gather evidence, then write the memo."
            ),
        }
    ]
    tool_trace = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Collect tool uses
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if response.stop_reason == "end_turn" or not tool_uses:
            # Final memo text
            memo_text = "\n\n".join(b.text for b in text_blocks if b.text.strip())
            return memo_text, tool_trace

        # Execute tools and append results
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tu in tool_uses:
            result = dispatch_tool(tu.name, tu.input, paths)
            tool_trace.append({
                "tool": tu.name,
                "input": tu.input,
                "output": result,
                "timestamp": datetime.now().isoformat(),
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tu.id,
                "content": json.dumps(result),
            })

        messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-csv", required=True)
    parser.add_argument("--pareto-csv",   required=True)
    parser.add_argument("--weather-csv",  required=True)
    parser.add_argument("--case-id",      required=True)
    parser.add_argument("--year",         type=int, required=True)
    parser.add_argument("--output",       required=True)
    parser.add_argument("--trace",        required=True)
    args = parser.parse_args()

    paths = {
        "scenario_csv": args.scenario_csv,
        "pareto_csv":   args.pareto_csv,
        "weather_csv":  args.weather_csv,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.trace).parent.mkdir(parents=True, exist_ok=True)

    print(f"Running AquaAgent-OSPy memo generator: {args.case_id} {args.year}")
    memo_text, tool_trace = run_agent(args.case_id, args.year, paths)

    with open(args.output, "w") as f:
        f.write(f"# AquaAgent-OSPy Irrigation Action Memo\n")
        f.write(f"**Case**: {args.case_id} | **Year**: {args.year}\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')} | ")
        f.write(f"**Agent**: AquaAgent-OSPy (A4 tool-calling advisory)\n\n")
        f.write("---\n\n")
        f.write(memo_text)

    with open(args.trace, "w") as f:
        json.dump({"case_id": args.case_id, "year": args.year,
                   "n_tool_calls": len(tool_trace), "trace": tool_trace}, f, indent=2)

    print(f"Memo written: {args.output}")
    print(f"Tool trace:   {args.trace} ({len(tool_trace)} calls)")


if __name__ == "__main__":
    main()
