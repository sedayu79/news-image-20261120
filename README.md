# One Day, One World — Friday, 20 November 2026

[![make.fun · news-image-20261120](https://make.fun/badge/news-image-20261120.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![rank](https://make.fun/badge/news-image-20261120/sedayu79/news-image-20261120/rank.svg)](https://make.fun/bounty/news-image-20261120/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)
[![reward](https://make.fun/badge/news-image-20261120/sedayu79/news-image-20261120/reward.svg)](https://make.fun/bounty/news-image-20261120?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261120)

A warm-cream atlas poster summing up Friday 20 November 2026's world
news in one image.

The hero story is the International Court of Justice ruling that Myanmar
committed genocide against the Rohingya. The lead stories below the map
cover the first Trump–Xi–Putin trilateral summit in Shenzhen, a suspected
Houthi missile hitting Riyadh's financial district, Voyager 1 reaching
one light-day from Earth, Anthropic's $1.5 trillion stock market debut,
and Cyclone Akvan bearing down on India's Odisha coast. An "Also Today"
strip adds Musk at DealBook, the posthumous pardon of Pete Rose, Pew's
projection on the world's largest faith, a tanker fire near Hormuz, an
Israeli strike in Lebanon, and the first India–New Zealand Test.

## How it works

`main.py` is a single Python 3.13 program using only the standard
library. It draws every pixel itself: a small software rasteriser
(rectangles, circles, polygon fills, a star), a hand-drawn 5x7 bitmap
font, and a PNG encoder built on `zlib` and `struct`. No external
files, no network, no randomness — the output is byte-identical on
every run.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

It writes exactly one file, `out/entry.png` (1024x1024, under 1 MiB).
