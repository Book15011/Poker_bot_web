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

test('the quick match: 50 big blinds that carry over, 10 hands, and running out of chips ends it', () => {
  const f = FORMATS.quick;
  assert.equal(f.handsInMatch, 10);
  assert.ok(!f.resetStacks, 'chips carry over');
  assert.equal(f.startingStack / f.blinds[0].big, 50);
  const rng = seededRng(7);
  let endedEarly = 0;
  for (let g = 0; g < 40; g++) {
    const m = new Match({ startingStack: f.startingStack, blinds: f.blinds });
    let prev = [f.startingStack, f.startingStack];
    while (m.winner() === null && m.handNumber < f.handsInMatch) {
      const h = m.nextHand(shuffledDeck(rng.int));
      assert.deepEqual([h.stacks[0] + h.totals[0], h.stacks[1] + h.totals[1]], prev, 'each hand starts where the last one ended');
      // Shove and call every hand: the most violent way to play the format.
      while (!h.finished) {
        const l = h.legalActions();
        m.act(l.canRaise ? { type: 'raise', to: l.maxRaiseTo } : l.canCall ? { type: 'call' } : { type: 'check' });
      }
      assert.equal(m.stacks[0] + m.stacks[1], 2 * f.startingStack, 'chips are conserved');
      prev = [m.stacks[0], m.stacks[1]];
    }
    if (m.winner() !== null) endedEarly++;
    assert.ok(m.handNumber <= f.handsInMatch);
  }
  // With equal stacks, the first shove-and-call decides it, so every one of these ends early.
  assert.equal(endedEarly, 40);
});
