import test from 'node:test';
import assert from 'node:assert/strict';
import { allInEquity, FORMATS } from '../js/ui/game.js';
import { Match } from '../js/engine/game.js';
import { parseCards, seededRng, shuffledDeck } from '../js/engine/cards.js';

test('all-in equity: exact on the turn and flop, close preflop', () => {
  // River: nothing to come, so equity is the showdown.
  assert.equal(allInEquity(parseCards('Ah Kh'), parseCards('2c 2d'), parseCards('Qh Jh Th 3s 4s')), 1);
  // Turn: a flush draw, a gutshot and two overcards against a pair of twos have 18 outs of 44.
  assert.equal(allInEquity(parseCards('Ah Kh'), parseCards('2c 2d'), parseCards('Qh Jh 3s 4c')), 18 / 44);
  // Flop: identical hands in different suits, with no flush possible, always split.
  assert.equal(allInEquity(parseCards('Ac Kd'), parseCards('Ad Kc'), parseCards('2h 7s 9h')), 0.5);
  // Preflop is sampled: aces against kings win about 82% of the time.
  const e = allInEquity(parseCards('Ah As'), parseCards('Kh Ks'), []);
  assert.ok(Math.abs(e - 0.82) < 0.012, `AA vs KK came out at ${e}`);
});

test('the quick match is ten hands, and every hand starts from fresh stacks', () => {
  const f = FORMATS.quick;
  assert.equal(f.handsInMatch, 10);
  assert.equal(f.resetStacks, true);
  const m = new Match({ startingStack: f.startingStack, blinds: f.blinds, resetStacks: true });
  const rng = seededRng(7);
  let score = 0;
  for (let i = 0; i < f.handsInMatch; i++) {
    const h = m.nextHand(shuffledDeck(rng.int));
    assert.deepEqual([h.stacks[0] + h.totals[0], h.stacks[1] + h.totals[1]], [f.startingStack, f.startingStack]);
    // Shove and call every hand: the biggest swing the format allows.
    while (!h.finished) {
      const l = h.legalActions();
      m.act(l.canRaise ? { type: 'raise', to: l.maxRaiseTo } : l.canCall ? { type: 'call' } : { type: 'check' });
    }
    const r = /** @type {any} */ (h.result);
    assert.equal(r.net[0] + r.net[1], 0, 'chips are conserved');
    assert.ok(Math.abs(r.net[0]) <= f.startingStack, 'one hand swings the score by at most one stack');
    score += r.net[0];
  }
  assert.equal(m.handNumber, 10);
  assert.ok(Math.abs(score) <= 10 * f.startingStack);
});
