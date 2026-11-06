// Play one trained blueprint against another in real No-Limit Hold'em, with duplicate deals. Used to check
// whether longer training made the bot better in the real game, not only inside the abstract one.
//
//   node bp_compare.js <bpDirA> <bpDirB> <dataDir> <mode> <depthBB> <pairs> <seed> [turnIters] [riverIters]
//
// mode: blueprint = the trained tables on every street (needs bp_<d>_full.bin in both folders)
//       expert    = the site's Expert (tables for preflop and flop, live solving after), each with its own blueprint
// The result is A's win rate against B, in bb/100.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { ExpertBot } from '../../poker/js/ai/expert.js';
import { RealtimeSolver } from '../../poker/js/ai/realtime.js';
import { loadSolverCore } from '../../poker/js/ai/solver.js';
import { seededRng } from '../../poker/js/engine/cards.js';
import { loadBlueprint, loadBuckets } from './node_models.js';
import { runMatch } from './arena.js';

const [dirA, dirB, dataDir, mode, depthArg, pairsArg, seedArg, turnArg, riverArg] = process.argv.slice(2);
if (mode !== 'blueprint' && mode !== 'expert') throw new Error('mode must be blueprint or expert');
const depth = Number(depthArg), pairs = Number(pairsArg), seed = Number(seedArg || 1);
const turnIters = Number(turnArg || 80), riverIters = Number(riverArg || 400);
const wasm = readFileSync(fileURLToPath(new URL('../../poker/js/ai/solver.wasm', import.meta.url)));
const file = (dir) => `${dir}/bp_${depth}${mode === 'blueprint' ? '_full' : ''}.bin`;
const bpA = loadBlueprint(file(dirA)), bpB = loadBlueprint(file(dirB));
const buckets = loadBuckets(dataDir, mode === 'blueprint' ? 3 : 1);

/** @param {string} name @param {any} bp @param {number} s */
async function make(name, bp, s) {
  return new ExpertBot({
    name,
    blueprintFor: () => bp,
    bucketsFor: buckets,
    rng: seededRng(s),
    solver: mode === 'expert'
      ? new RealtimeSolver(await loadSolverCore(wasm), { turn: { iterations: turnIters }, river: { iterations: riverIters }, riverStride: 4 })
      : null,
  });
}

const a = await make('A', bpA, seed * 7 + 1), b = await make('B', bpB, seed * 11 + 3);
const t0 = Date.now();
const r = await runMatch(() => a, () => b, { pairs, seed: 5000 + seed, stackBB: depth });
console.log(JSON.stringify({
  mode, depth, pairs, seed, a: dirA, b: dirB,
  ...(mode === 'expert' ? { turnIters, riverIters } : {}),
  bb100: r.bb100, ci95: r.ci95, hands: r.hands, seconds: (Date.now() - t0) / 1000,
}));
