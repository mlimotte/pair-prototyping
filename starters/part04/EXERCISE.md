# Part 4: switch or leave?

Morgan's brief has an open question: **when oat sells out, do customers switch to another milk, or do they leave?** Answer it three times, with three kinds of access. Use the same question each time.

The question:

> Morgan, the product owner, asks: when oat milk sells out, do customers switch to another milk, or do they leave? Answer from the data you can find, with numbers. At most 200 words. End with the sources you used.

## Do this

1. **Morgan's view.** `cd product && claude`. Paste the question. This folder has what a product person's agent usually gets: the warehouse copy, the inputs and the docs. Copy the answer into `answer.md` under "Product view".
2. **Your view, no pointer.** `cd brewboard && claude`. Start a new session. Paste the same question. Copy the answer under "Engineer, no pointer".
3. **Your view, one sentence.** `cd brewboard && claude`, a new session again. Paste the question and add one sentence: `Check the session events in ../logs, not only the orders.` Copy the answer under "Engineer, with pointer".
4. Under "What changed", write in your own words:
   - the leave rate each run reported;
   - why the orders table cannot answer this question;
   - why the dashboard's abandonment tile does not show it;
   - why run 2 missed it, though it had the same access as run 3;
   - one more thing the engineer's agent found that the product view cannot see, with the file it came from;
   - the next question for Morgan.
5. Grade it: `cd grade && claude "/grade"`.

Do not run Claude Code from this top folder, and do not give it `--add-dir`. Both tell the agent more than this exercise wants to give it. Agents vary from run to run: if your run 2 finds the logs anyway, write that down. It is a real result.
