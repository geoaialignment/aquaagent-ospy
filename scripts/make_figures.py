"""
AquaAgent-OSPy quantitative figure generation.
Produces data-driven paper figures from processed data.

Conceptual, workflow, architecture, infographic, and graphical-abstract
figures are intentionally excluded. Those paper-facing figures must be
prepared as publication artwork rather than Matplotlib box/arrow flowcharts.

Usage:
    python3 make_figures.py --outdir figures/
"""

import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Style
# ─────────────────────────────────────────────────────────────────────────────

COLORS = {
    'rainfed':       '#4e79a7',
    'deficit_SMT30': '#59a14f',
    'deficit_SMT50': '#f28e2b',
    'full_SMT80':    '#e15759',
    'fixed_7d_80pct':'#76b7b2',
    'pareto':        '#b07aa1',
    'ndvi1':         '#59a14f',
    'ndvi2':         '#f28e2b',
}

STRAT_LABELS = {
    'rainfed':        'Rainfed',
    'deficit_SMT30':  'Deficit SMT30',
    'deficit_SMT50':  'Deficit SMT50 ⭐',
    'full_SMT80':     'Full SMT80',
    'fixed_7d_80pct': 'Fixed weekly',
}


def load_scenarios(csv_path):
    rows = {}
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            key = (r['case'], int(r['year']))
            rows.setdefault(key, []).append({
                'strategy': r['strategy'],
                'yield': float(r['yield_t_ha']),
                'irr':   float(r['irrigation_mm']),
                'WP':    float(r['WP_kg_m3']),
            })
    return rows


def load_pareto(csv_path):
    rows = []
    with open(csv_path) as f:
        for r in csv.DictReader(f):
            rows.append({'yield': float(r['yield_t_ha']),
                         'irr':   float(r['irrigation_mm']),
                         'WP':    float(r['WP_kg_m3'])})
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2: Site map (text-based for now, QGIS/matplotlib placeholder)
# ─────────────────────────────────────────────────────────────────────────────

def fig2_site_map(outdir):
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.set_xlim(125.5, 130)
    ax.set_ylim(33.5, 38.5)
    ax.set_xlabel('Longitude (°E)')
    ax.set_ylabel('Latitude (°N)')
    ax.grid(True, alpha=0.3)
    ax.plot(126.898, 35.754, 'o', color='#f28e2b', ms=12, zorder=5, label='Case 1: Gimje')
    ax.plot(126.540, 35.070, 's', color='#4e79a7', ms=12, zorder=5, label='Case 2: Hampyeong')
    ax.annotate('Gimje\n35.75°N, 126.90°E', (126.898, 35.754),
                textcoords='offset points', xytext=(10, 8), fontsize=9)
    ax.annotate('Hampyeong\n35.07°N, 126.54°E', (126.540, 35.070),
                textcoords='offset points', xytext=(10, -18), fontsize=9)
    ax.legend(loc='lower right', fontsize=9)
    path = outdir / 'fig2_site_map.pdf'
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3: Scenario comparison — yield vs irrigation, 4 panels (2 sites × 2 years)
# ─────────────────────────────────────────────────────────────────────────────

def fig3_scenario_comparison(scenarios, outdir):
    cases = [
        ('case1_gimje',     2019, 'Case 1 Gimje 2019\n(Precip/ETo = 1.00)'),
        ('case1_gimje',     2022, 'Case 1 Gimje 2022\n(Precip/ETo = 1.09)'),
        ('case2_hampyeong', 2019, 'Case 2 Hampyeong 2019\n(Precip/ETo = 1.73)'),
        ('case2_hampyeong', 2022, 'Case 2 Hampyeong 2022\n(Precip/ETo = 1.52)'),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    strat_order = ['rainfed', 'deficit_SMT30', 'deficit_SMT50', 'full_SMT80', 'fixed_7d_80pct']

    for ax, (cid, yr, title) in zip(axes.flat, cases):
        rows = scenarios.get((cid, yr), [])
        by_strat = {r['strategy']: r for r in rows}
        irrs  = [by_strat.get(s, {}).get('irr', 0) for s in strat_order]
        yields= [by_strat.get(s, {}).get('yield', 0) for s in strat_order]
        colors= [COLORS.get(s, '#888888') for s in strat_order]
        bars = ax.bar(range(len(strat_order)), yields, color=colors,
                      edgecolor='white', linewidth=0.8, zorder=3)
        ax2 = ax.twinx()
        ax2.plot(range(len(strat_order)), irrs, 'k--o', ms=5, lw=1.5,
                 label='Irrigation (mm)', zorder=4)
        ax.axhline(y=by_strat.get('rainfed', {}).get('yield', 0),
                   color='#4e79a7', lw=0.8, ls=':', alpha=0.6)
        ax.set_title(title, fontsize=10)
        ax.set_xticks(range(len(strat_order)))
        ax.set_xticklabels([STRAT_LABELS.get(s, s).replace(' ⭐', '*')
                            for s in strat_order], rotation=30, ha='right', fontsize=8)
        ax.set_ylabel('Dry yield (t/ha)', fontsize=9)
        ax2.set_ylabel('Irrigation (mm)', fontsize=9)
        ax.set_ylim(5.5, 8.0)
        ax2.set_ylim(0, 250)
        ax.yaxis.grid(True, alpha=0.3, zorder=0)
        # Safety line
        ax2.axhline(y=200, color='red', lw=0.8, ls='--', alpha=0.5, label='200mm safety limit')

    handles = [mpatches.Patch(color=COLORS[s], label=STRAT_LABELS.get(s,s).replace(' ⭐','*'))
               for s in strat_order]
    handles += [plt.Line2D([0],[0], color='k', lw=1.5, ls='--', label='Irrigation depth'),
                plt.Line2D([0],[0], color='red', lw=0.8, ls='--', alpha=0.5, label='200mm safety limit')]
    fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=8,
               bbox_to_anchor=(0.5, -0.04))
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    path = outdir / 'fig3_scenario_comparison.pdf'
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4: Pareto front (Case 1 Gimje 2019)
# ─────────────────────────────────────────────────────────────────────────────

def fig4_pareto_front(pareto_rows, scenario_rows, outdir):
    fig, ax = plt.subplots(figsize=(7, 5))

    irrs  = [r['irr']   for r in pareto_rows]
    yields= [r['yield'] for r in pareto_rows]
    ax.scatter(irrs, yields, color=COLORS['pareto'], s=40, zorder=3, label='Pareto solutions')

    # Highlight best WP
    best_wp = max(pareto_rows, key=lambda r: r['WP'])
    ax.scatter([best_wp['irr']], [best_wp['yield']], color='gold', s=120, zorder=5,
               edgecolors='black', lw=1.2, label=f"Best WP ({best_wp['WP']:.3f} kg/m³)")

    # Overlay scenario strategies
    strat_order = ['rainfed', 'deficit_SMT30', 'deficit_SMT50', 'full_SMT80', 'fixed_7d_80pct']
    by_strat = {r['strategy']: r for r in scenario_rows}
    for s in strat_order:
        r = by_strat.get(s)
        if r:
            marker = '*' if s == 'deficit_SMT50' else 'D'
            sz = 120 if s == 'deficit_SMT50' else 70
            ax.scatter([r['irr']], [r['yield']], color=COLORS.get(s, '#888'), s=sz,
                       zorder=4, marker=marker, edgecolors='black', lw=0.8,
                       label=STRAT_LABELS.get(s, s).replace(' ⭐', '*'))

    ax.axvline(x=200, color='red', lw=1, ls='--', alpha=0.6, label='200mm safety limit')
    ax.set_xlabel('Seasonal irrigation (mm)', fontsize=11)
    ax.set_ylabel('Dry yield (t/ha)', fontsize=11)
    ax.legend(fontsize=8, loc='lower right', ncol=2)
    ax.grid(True, alpha=0.3)

    path = outdir / 'fig4_pareto_front.pdf'
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5: GEE NDVI time series
# ─────────────────────────────────────────────────────────────────────────────

def fig5_ndvi_timeseries(outdir):
    # Values from GEE execution (Section 4.4, Gate 4 results)
    months = [4, 5, 6, 7, 9, 10]
    month_labels = ['Apr', 'May', 'Jun', 'Jul', '(Aug\ncloud)', 'Sep', 'Oct']
    gimje_ndvi     = [0.837, 0.481, 0.124, None, None, 0.773, 0.466]  # Aug missing
    hampyeong_ndvi = [0.703, 0.429, 0.244, 0.053, None, 0.674, 0.409]

    x = range(len(month_labels))
    fig, ax = plt.subplots(figsize=(8, 5.2))

    def plot_line(vals, color, label):
        xs, ys = [], []
        for i, v in enumerate(vals):
            if v is not None:
                xs.append(i); ys.append(v)
        ax.plot(xs, ys, 'o-', color=color, lw=2, ms=7, label=label)
        for i, v in enumerate(vals):
            if v is not None:
                ax.annotate(f'{v:.2f}', (i, v), textcoords='offset points',
                            xytext=(0, 8), ha='center', fontsize=8, color=color)

    plot_line(gimje_ndvi,     COLORS['ndvi1'], 'Case 1: Gimje, Jeollabuk-do')
    plot_line(hampyeong_ndvi, COLORS['ndvi2'], 'Case 2: Hampyeong, Jeollanam-do')

    ax.axvspan(1.5, 3.5, alpha=0.08, color='blue', label='Transplanting period\n(Jun–Jul, NDVI dip)')
    ax.axvspan(5, 6, alpha=0.08, color='green', label='Maturation\n(Sep–Oct, NDVI peak)')
    ax.set_xticks(range(len(month_labels)))
    ax.set_xticklabels(month_labels)
    ax.set_ylabel('NDVI (Sentinel-2 SR)', fontsize=10)
    ax.set_ylim(-0.1, 1.0)
    ax.legend(fontsize=8, loc='upper left', bbox_to_anchor=(0.0, -0.18),
              ncol=2, frameon=False)
    ax.grid(True, alpha=0.3)

    path = outdir / 'fig5_ndvi_seasonality.pdf'
    fig.subplots_adjust(bottom=0.26)
    fig.savefig(path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--outdir', default='figures', help='Output directory for figures')
    p.add_argument('--datadir', default='data/processed', help='Data directory')
    args = p.parse_args()

    outdir  = Path(args.outdir);  outdir.mkdir(exist_ok=True)
    datadir = Path(args.datadir)

    # Use SoilGrids-corrected results if available, else fall back to original
    scen_corrected = datadir / 'scenario_results_soilgrids_corrected.csv'
    scen_csv   = scen_corrected if scen_corrected.exists() else datadir / 'scenario_results_confirmed_sites.csv'
    pareto_corrected = datadir / 'pareto_front_case1_gimje_2019_soilcorrected.csv'
    pareto_csv = pareto_corrected if pareto_corrected.exists() else datadir / 'pareto_front_case1_gimje_2019.csv'
    print(f"Using scenario data: {scen_csv.name}")
    print(f"Using Pareto data:   {pareto_csv.name}")

    scenarios = load_scenarios(scen_csv)
    pareto    = load_pareto(pareto_csv)
    gimje19   = scenarios.get(('case1_gimje', 2019), [])

    print("Generating quantitative figures...")
    print("Skipping Fig. 1 system architecture: use PaperBanana publication artwork.")
    fig2_site_map(outdir)
    fig3_scenario_comparison(scenarios, outdir)
    fig4_pareto_front(pareto, gimje19, outdir)
    fig5_ndvi_timeseries(outdir)
    print(f"\nAll figures saved to {outdir}/")
    for f in sorted(outdir.glob('*.pdf')):
        print(f"  {f.name}")


if __name__ == '__main__':
    main()
