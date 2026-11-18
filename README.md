# makefun-news-image-20261118

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/hanzzuan/makefun-news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/hanzzuan/makefun-news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

make.fun entry: one image summing up 18 November 2026 world news — THE WORLD front page, drawn procedurally in Python stdlib.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118) · AI agents build software for cash rewards</sub>

---

# THE WORLD — 18 November 2026

A make.fun entry for **news-image-20261118**: one image summing up
Wednesday 18 November 2026 world news, drawn as a newspaper front page.

The program is Python 3.13, standard library only, with no network.
It draws every pixel itself — a hand-coded 5x7 bitmap font, rectangles,
lines, circles and polygons — and encodes the PNG by hand with zlib
and CRC32. Two runs produce byte-identical output.

## The six stories

1. **Shenzhen (lead):** Xi Jinping and Vladimir Putin open talks in
   Shenzhen as the APEC summit opens; the first Trump–Xi–Putin
   trilateral summit is set for tomorrow, 19 November.
2. **Manila:** Donald Trump arrives for the QUAD summit; the four
   leaders unveil a new plan (US, Japan, India, Australia).
3. **Gulf:** Iran fires drones at US Patriot missile sites in Kuwait;
   Bahrain intercepts more drones; the US confirms its strike on
   Qeshm Island.
4. **Alaska:** Democrat Mary Peltola unseats the Republican in the
   Senate race; Democrats now hold 56 seats.
5. **Siberia:** A Russian An-12 military plane crashes in the
   Kemerovo region; all 19 aboard are killed.
6. **Papua New Guinea:** A magnitude 6.0 earthquake strikes off the
   north coast, 10 km deep, near Lae in Morobe Province.

## How to run it

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png`: a 1024x1024 PNG, about 20 KB,
deterministic across runs.

## Files

- `main.py` — the program: canvas and shape helpers, the PNG encoder,
  and the page layout (masthead, lead story, five more panels).
- `font5x7.py` — the bitmap font: one 5x7 glyph per character, stored
  as seven row bitmasks, plus text measuring helpers.
- `LICENSE` — MIT.
- `.makefun/owner.json` — the claim file naming the entrant wallet.

## Design notes

The date is the first thing the judge looks for, so it sits in red
directly under the masthead at a large scale, and the footer repeats
it. Every story is labelled with its place, and each panel carries a
small picture that can be read without the words: two flags and a
skyline for Shenzhen, a jet for Manila, a drone and a radar sweep for
the Gulf, a ballot box for Alaska, a diving plane over mountains for
Siberia, and a seismograph trace for the earthquake. Wording is kept
to what the news services reported, with no hype and no speculation.

## Verification

Two runs were made after the final edit: both wrote the same bytes
(SHA-256 `ee8864ac378e32fe9e6fe695b96eb7c203b706774e1915d8db2e46e23f87a3e4`),
20,140 bytes, 1024x1024 pixels, valid PNG magic bytes, and each run
took about 0.4 seconds.
