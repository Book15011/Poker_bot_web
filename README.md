# Poker AI: training, research and benchmarks

The source behind **[Can You Beat My Poker AI?](https://book15011.github.io/quant.html#poker)**, a heads-up No-Limit Texas Hold'em game on my portfolio. You play against an AI that was trained by self-play and that solves the turn and river live on your device. There is no server, no sign-up and no paid API. Virtual chips only.

**[Play it](https://book15011.github.io/quant.html#poker)** · **[How it works](https://book15011.github.io/poker/how-it-works.html)** · **[Benchmarks](docs/BENCHMARKS.md)** · **[Training](docs/TRAINING.md)**

This repository has everything: the game, the training code, the live solver, the research notes and every benchmark result. The [website repository](https://github.com/Book15011/Book15011.github.io) carries only a published copy of the playable game (see [Publishing](#publishing-to-the-website)).

## How the AI works

Poker is a hard kind of AI problem because you can't see the other player's cards. The Expert bot uses the approach behind [Pluribus](https://noambrown.github.io/papers/19-Science-Superhuman.pdf) and [Modicum](https://arxiv.org/abs/1805.08195), on a budget:

1. **Trained offline.** External-sampling Monte Carlo CFR with Linear CFR discounting and regret pruning, in multithreaded C++ on 12 CPU cores. One strategy table (a "blueprint") per stack depth, from 5bb to 200bb, over a card abstraction of 2,000 flop buckets and 1,000 to 5,000 turn and river buckets.
2. **Solves live.** On the turn and river it builds a tree for the rest of the hand, including your exact bet size, and solves it with vector-form Discounted CFR. The solver is about 50 KB of WebAssembly (from C) running in a Web Worker. It keeps solving while you decide.
3. **Can't cheat by construction.** The rules engine runs on the page and posts the AI only its own observation: its cards, the board and the betting.
4. **Explains itself.** After each hand you can see its action probabilities, equity estimate and the range of hands it put you on, labelled as model estimates.

Plain-language version: [AI_EXPLAINED.md](docs/AI_EXPLAINED.md). Design and code layout: [ARCHITECTURE.md](docs/ARCHITECTURE.md). Why this approach over Deep CFR or value networks: [RESEARCH.md](docs/RESEARCH.md).

## Results

185,178 evaluated hands, with duplicate deals and 95% confidence intervals. All details and limitations are in [BENCHMARKS.md](docs/BENCHMARKS.md).

| Test | Result |
|---|---|
| Against the Competitive bot on the site, 20bb | +21.5 ± 13.1 bb/100 |
| Local Best Response (an exploiter that knows the exact strategy) | Never found a positive exploit |
| [Slumbot](https://slumbot.com), 2018 competition winner, 200bb | −35.5 ± 50.6 bb/100 over 4,500 hands |
| Turn aggression, 200bb | 61% bets and raises at 20 solve iterations, 29% at 300 (trained tables: 24 to 29%) |

Slumbot took about 250,000 core hours to compute. This project's first training run used about 55. The Slumbot loss led to the turn-aggression study, the think-time solving now on the site, and a longer deep-stack training run, documented in [BENCHMARKS.md](docs/BENCHMARKS.md#turn-aggression-and-solve-length) and [TRAINING.md](docs/TRAINING.md).

## Repository layout

| Path | Contents |
|---|---|
| [`poker/`](poker) | The browser game: rules engine, bots, Expert AI, solver front end, UI, deployed models, and unit and property tests |
| [`research/trainer/`](research/trainer) | C++ card abstraction and MCCFR blueprint trainer |
| [`research/solver/`](research/solver) | C live solver, compiled to WebAssembly |
| [`research/bench/`](research/bench) | Benchmarks: head-to-head, Local Best Response, Slumbot, solver quality, turn aggression. They import the same JavaScript that ships to the browser |
| [`research/scripts/`](research/scripts) | Training and benchmark job runners, and the report builder |
| [`research/results/`](research/results) | Raw benchmark results |
| [`research/e2e/`](research/e2e) | Browser tests that play full matches in real Chrome |
| [`docs/`](docs) | Research, architecture, training and benchmark write-ups |
| [`scripts/publish_site.py`](scripts/publish_site.py) | Copies the playable game into the website repository |

## Run it

```bash
# Any static file server will do
python -m http.server 8000
# Then open http://localhost:8000/poker/
```

The game's "back" link and the end-to-end tests expect the portfolio around it, so run those from the website checkout.

```bash
# Unit and property tests (Node 22 or newer, no dependencies)
cd poker
npm test
npm run typecheck
```

```bash
# Browser tests against a served copy of the website (Python, Playwright and an installed Chrome)
pip install playwright
python research/e2e/test_e2e.py http://localhost:8000
```

Training and benchmarks run on a Linux machine. [TRAINING.md](docs/TRAINING.md) has the full pipeline, and [BENCHMARKS.md](docs/BENCHMARKS.md) names the script and seed behind each result.

## Publishing to the website

The website repository serves a copy of `poker/` without the tests and tooling. After a change here:

```bash
python scripts/publish_site.py ../Book15011.github.io
```

It mirrors `poker/index.html`, `poker/how-it-works.html`, `css/`, `js/`, `models/` and `data/` into the website checkout, prints what changed, and touches nothing else. Review, commit and push there to deploy.

## Quality checks

- The hand evaluator matches the known counts for all 133,784,560 seven-card hands.
- The solver reproduces the exact solution of a river game with a known answer.
- Property tests check chip conservation and legal play over tens of thousands of random hands.
- Browser tests play full matches through the real buttons in Chrome, at desktop and phone sizes.

## Limitations

The AI approximates an equilibrium of a simplified game. It does not adapt to individual opponents and has not been tested against professional players. See [BENCHMARKS.md](docs/BENCHMARKS.md) for what the numbers do and don't show.

## Provenance

All code and models here were written or trained for this project. The bots and papers cited in [RESEARCH.md](docs/RESEARCH.md) were read for ideas, and no third-party code or weights are included. The training data is entirely self-play, with no human hand histories.

The history of this repository was carried over from the website repository, where the project started, keeping only these folders.
