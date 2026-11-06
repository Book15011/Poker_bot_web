"""Draw the figures in docs/figures from the raw results, in a light and a dark version each.

Every number comes from a file in research/results or poker/data, so rerunning this after new results
redraws the charts. A chart whose inputs are missing is skipped with a message.

Usage: python research/scripts/make_figures.py
"""
import json
import logging
import os
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'research' / 'results'
OUT = ROOT / 'docs' / 'figures'

# Reference palette (validated for these three slots, all pairs, light and dark) and chart chrome.
THEMES = {
    'light': dict(surface='#fcfcfb', ink='#0b0b0b', ink2='#52514e', muted='#898781', grid='#e1e0d9',
                  base='#c3c2b7', band='#f0efec', series=['#2a78d6', '#eb6834', '#1baf7a']),
    'dark': dict(surface='#1a1a19', ink='#f0efec', ink2='#c3c2b7', muted='#898781', grid='#2c2c2a',
                 base='#383835', band='#2c2c2a', series=['#3987e5', '#d95926', '#199e70']),
}
PX = 0.75  # points per CSS pixel
FONT_STACK = "'Segoe UI', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"

plt.rcParams.update({
    'font.family': ['Segoe UI', 'DejaVu Sans'],
    'font.size': 10.5,
    'svg.fonttype': 'none',
    'axes.spines.top': False,
    'axes.spines.right': False,
})


def frame(t, w=7.6, h=4.3):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(t['surface'])
    ax.set_facecolor(t['surface'])
    for s in ('left', 'bottom'):
        ax.spines[s].set_color(t['base'])
        ax.spines[s].set_linewidth(1 * PX * 1.33)
    ax.tick_params(colors=t['muted'], labelcolor=t['ink2'], length=0, pad=6)
    ax.grid(axis='y', color=t['grid'], linewidth=1 * PX * 1.33)
    ax.set_axisbelow(True)
    return fig, ax


def titles(fig, t, title, subtitle):
    fig.text(0.012, 0.975, title, ha='left', va='top', fontsize=13, fontweight='bold', color=t['ink'])
    fig.text(0.012, 0.905, subtitle, ha='left', va='top', fontsize=9.5, color=t['ink2'])


def save(fig, name, mode):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{name}-{mode}.svg'
    fig.savefig(path, facecolor=fig.get_facecolor(), metadata={'Date': None})
    # Text stays text, so give viewers without Segoe UI a system sans instead of a serif fallback.
    svg = path.read_text(encoding='utf-8').replace("'Segoe UI', 'DejaVu Sans'", FONT_STACK)
    path.write_text(svg, encoding='utf-8', newline='\n')
    if os.environ.get('FIG_PREVIEW'):  # PNG copies for checking the layout by eye
        fig.savefig(Path(os.environ['FIG_PREVIEW']) / f'{name}-{mode}.png', facecolor=fig.get_facecolor(), dpi=110)
    plt.close(fig)
    return path


def read_jsonl(path):
    with open(path, encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.startswith('{')]


# ---------- 1. Turn aggression against solve length ----------
def turn_aggression():
    runs = []
    for p in sorted((RESULTS / 'turn_profile').glob('d*_p0.02.jsonl')):
        r = read_jsonl(p)[0]
        runs.append(r)
    if not runs:
        return print('skip turn_aggression: no research/results/turn_profile')
    depths = sorted({r['depth'] for r in runs}, reverse=True)
    own = [r['blueprint'][2]['aggr'] for r in runs]
    for mode, t in THEMES.items():
        fig, ax = frame(t)
        fig.subplots_adjust(left=0.085, right=0.97, top=0.8, bottom=0.14)
        ax.axhspan(min(own) * 100, max(own) * 100, color=t['band'], zorder=0, linewidth=0)
        ax.text(16.5, (min(own) + max(own)) * 50, "Trained tables' own rate", va='center', ha='left',
                fontsize=9, color=t['ink2'])
        handles, ends = [], []
        for i, d in enumerate(depths):
            pts = sorted((r['turnIters'], r['expert'][2]['aggr'] * 100) for r in runs if r['depth'] == d)
            xs, ys = zip(*pts)
            c = t['series'][i]
            (h,) = ax.plot(xs, ys, color=c, linewidth=2 * PX, marker='o', markersize=8 * PX,
                           markeredgecolor=t['surface'], markeredgewidth=2 * PX, label=f'{d}bb', zorder=3)
            handles.append(h)
            ends.append([ys[-1], ys[-1], f'{d}bb'])
            if d == depths[0]:
                for x, y in pts[:-1]:
                    ax.annotate(f'{y:.1f}%', (x, y), textcoords='offset points', xytext=(7, 5), fontsize=9,
                                color=t['ink2'])
        # End labels, spread apart so they never overlap (at least 4.2 points of the y scale).
        ends.sort(key=lambda e: -e[0])
        for i in range(1, len(ends)):
            ends[i][1] = min(ends[i][1], ends[i - 1][1] - 4.2)
        for y, ly, label in ends:
            ax.text(345, ly, f'{label}  {y:.1f}%', va='center', ha='left', fontsize=9.5, color=t['ink'])
        ax.set_xscale('log')
        ax.set_xticks([20, 80, 300])
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}'))
        ax.xaxis.set_minor_formatter(FuncFormatter(lambda v, _: ''))
        ax.set_xlim(15, 560)
        ax.set_ylim(0, 70)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.0f}%'))
        ax.set_xlabel('Turn solve iterations', color=t['ink2'])
        leg = ax.legend(handles=handles, loc='upper right', frameon=False, fontsize=9, labelcolor=t['ink'],
                        title='Stack depth', title_fontsize=9)
        leg.get_title().set_color(t['ink2'])
        titles(fig, t, 'Short live solves made the Expert over-bet the turn',
               "Turn decisions that were bets or raises, Expert against its own blueprint "
               '(300 to 600 duplicate hands per point)')
        print('wrote', save(fig, 'turn_aggression', mode))


# ---------- 2. Head-to-head at 20bb ----------
def head_to_head():
    data = json.loads((ROOT / 'poker' / 'data' / 'benchmarks.json').read_text(encoding='utf-8'))
    chart = next(s['chart'] for s in data['sections'] if (s.get('chart') or {}).get('title', '').startswith('Expert win rate at 20bb'))
    rows = sorted(chart['rows'], key=lambda r: r['value'])
    for mode, t in THEMES.items():
        fig, ax = frame(t, h=4.9)
        fig.subplots_adjust(left=0.25, right=0.97, top=0.82, bottom=0.12)
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=t['grid'], linewidth=1 * PX * 1.33)
        ax.spines['left'].set_visible(False)
        c = t['series'][0]
        for i, r in enumerate(rows):
            ax.plot([r['value'] - r['ci'], r['value'] + r['ci']], [i, i], color=c, linewidth=2 * PX,
                    solid_capstyle='round', zorder=2)
            ax.plot([r['value']], [i], 'o', color=c, markersize=9 * PX, markeredgecolor=t['surface'],
                    markeredgewidth=2 * PX, zorder=3)
            ax.text(r['value'] + r['ci'] + 4, i, f"{r['value']:+.1f}", va='center', fontsize=9, color=t['ink2'])
        ax.axvline(0, color=t['ink2'], linewidth=1.5 * PX)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r['label'] for r in rows], color=t['ink'])
        ax.set_xlim(-60, 215)
        ax.set_xlabel('Expert win rate, bb/100 (dot) with 95% interval (line). Right of zero = Expert wins',
                      color=t['ink2'])
        titles(fig, t, 'Expert against each opponent, 20 big blinds deep',
               'Duplicate deals, 2,400 to 10,400 hands per opponent. Intervals that clear zero are significant')
        print('wrote', save(fig, 'head_to_head_20bb', mode))


# ---------- 3. Slumbot: first match against the rematch ----------
def slumbot():
    first = [read_jsonl(p) for p in sorted(RESULTS.glob('slumbot_s*.jsonl'))]
    again = [read_jsonl(p) for p in sorted((RESULTS / 'slumbot_rematch').glob('*.jsonl'))]
    if not first or not again:
        return print('skip slumbot: needs research/results/slumbot_s*.jsonl and research/results/slumbot_rematch/')

    def curve(sessions):
        # Sessions ran side by side, so interleave them hand by hand.
        hands = [h for i in range(max(map(len, sessions))) for s in sessions if i < len(s) for h in [s[i]]]
        total, ys = 0, []
        for h in hands:
            total += h['winnings'] / 100
            ys.append(total)
        return list(range(1, len(ys) + 1)), ys

    series = [('Rematch: 300 turn iterations, longer training', again),
              ('First match: 20 turn iterations', first)]
    for mode, t in THEMES.items():
        fig, ax = frame(t)
        fig.subplots_adjust(left=0.1, right=0.8, top=0.8, bottom=0.14)
        ax.axhline(0, color=t['ink2'], linewidth=1.5 * PX)
        handles = []
        for i, (label, sess) in enumerate(series):
            xs, ys = curve(sess)
            (h,) = ax.plot(xs, ys, color=t['series'][i], linewidth=2 * PX, label=label)
            handles.append(h)
            rate = ys[-1] / len(xs) * 100
            ax.text(xs[-1] * 1.015, ys[-1], f'{rate:+.1f} bb/100\n{len(xs):,} hands', va='center', ha='left',
                    fontsize=9, color=t['ink'])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:+,.0f}' if v else '0'))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
        ax.set_xlabel('Hands played', color=t['ink2'])
        ax.set_ylabel('Cumulative big blinds won', color=t['ink2'])
        ax.legend(handles=handles, loc='upper left', frameon=False, fontsize=9, labelcolor=t['ink'])
        titles(fig, t, 'Against Slumbot, before and after the fixes',
               "Expert's running total at 200bb against the 2018 competition winner. Chip results are noisy")
        print('wrote', save(fig, 'slumbot', mode))


# ---------- 4. Training: first run against the longer run ----------
def training():
    path = RESULTS / 'training_long.json'
    if not path.exists():
        return print('skip training: no research/results/training_long.json')
    rows = json.loads(path.read_text(encoding='utf-8'))['depths']
    for mode, t in THEMES.items():
        fig, ax = frame(t, h=3.6)
        fig.subplots_adjust(left=0.1, right=0.97, top=0.76, bottom=0.17)
        ax.grid(axis='y', visible=False)
        ax.grid(axis='x', color=t['grid'], linewidth=1 * PX * 1.33)
        ax.spines['left'].set_visible(False)
        first, longer = t['series'][1], t['series'][0]
        for i, r in enumerate(rows):
            a, b = r['first']['exploitability'], r['long']['exploitability']
            ax.plot([a, b], [i, i], color=t['base'], linewidth=2 * PX, zorder=1)
            ax.plot([a], [i], 'o', color=first, markersize=9 * PX, markeredgecolor=t['surface'],
                    markeredgewidth=2 * PX, zorder=3, label='First run' if i == 0 else None)
            ax.plot([b], [i], 'o', color=longer, markersize=9 * PX, markeredgecolor=t['surface'],
                    markeredgewidth=2 * PX, zorder=3, label='Longer run' if i == 0 else None)
            ax.text(max(a, b) + 12, i, f"{r['first']['iterationsB']:.1f}B to {r['long']['iterationsB']:.1f}B iterations",
                    va='center', fontsize=9, color=t['ink2'])
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([f"{r['depth']}bb" for r in rows], color=t['ink'])
        ax.set_xlim(0, max(max(r['first']['exploitability'], r['long']['exploitability']) for r in rows) * 1.45)
        ax.set_xlabel('Abstract exploitability estimate, mbb/hand (lower is better)', color=t['ink2'])
        ax.legend(loc='lower right', frameon=False, fontsize=9, labelcolor=t['ink'])
        titles(fig, t, 'Longer training of the deep-stack blueprints',
               'Monte Carlo best response inside the abstract game. A convergence signal, not exploitability in real poker')
        print('wrote', save(fig, 'training', mode))


if __name__ == '__main__':
    turn_aggression()
    head_to_head()
    slumbot()
    training()
