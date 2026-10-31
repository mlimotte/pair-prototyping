# Pair prototyping: a learning series

Seven interactive posts that teach pair prototyping and the loop, set at Brew Board, a fictional coffee ordering app. Engineers first. Contract: `DESIGN.md`.

```bash
python serve.py                                   # build and serve: http://localhost:8765/
python starters/make_starter.py 04 ~/backlog/p04  # a part's exercise folder
python datagen/generate.py --truth                # the planted truth, as measured
```

Python 3.11+, standard library only. Part 2's live example calls your own `claude -p` (no API key).

| Part | State |
|---|---|
| 1 The constraint moves | not written |
| 2 Give me the prompt | post, figures (recorded + live), cards, exercise |
| 3 An old loop | not written |
| 4 Pair prototyping | post, figures (data + recorded agent runs), cards, exercise |
| 5–7 | not written |

Maintenance:

```bash
python tools/record_part2.py > site/static/data/part2-runs.json         # re-record (then re-check post 2's numbers)
python starters/make_starter.py 04 /tmp/p4 && python tools/export_part4.py /tmp/p4 > site/static/data/part4.json
python tools/record_part4.py /tmp/p4 2 product,quiet,quiet-pointer,none,pointer > site/static/data/part4-runs.json
python serve.py build && (cd tools/check && npm ci && SITE_DIR=../../_site node check.mjs)
```

## Deploy

Pushes to `main` build the site and deploy it to GitHub Pages (`.github/workflows/pages.yml`). The workflow runs the site check first. In the repo settings, set Pages → Source to "GitHub Actions". On Pages, part 2's live box shows recorded runs only.
