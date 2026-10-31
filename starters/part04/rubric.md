# Rubric: part 4 (switch or leave?)

The measured truth for this data: 477 sessions saw oat sold out. 166 (34.8%) left without ordering. 201 (42.1%) switched to almond and 110 (23.1%) to whole.

1. **Three answers.** The answer has the product view, the engineer view with no pointer, and the engineer view with the pointer, each with the leave rate it reported.
2. **The right number.** The run with the pointer reports a leave rate between 30% and 40%, from the session events.
3. **Why not the orders table.** It holds only customers who ordered. People who left are not in it, so it shows oat moving to almond and whole, as if everyone switched.
4. **Why not the dashboard tile.** Names at least one reason: most leavers left before a cart existed, so they have no cart row; or the tile drops carts open under 60 seconds. Full marks if it notes that the tile is lower on sell-out days.
5. **Why the pointer mattered.** Run 2 had the same access but did not know the session events existed or where they were (outside the repo, not in the warehouse). One sentence told it.
6. **One more finding.** Names one more thing from the code or logs, with its file: the 5-minute stock cache (`brewboard/stock.py`); counter rejections (`logs/counter/`); the POS contract (`contracts/pos_order_line.schema.json`); the `substitutions` branch; or the double-charge postmortem.
7. **Next question.** States a next question for Morgan that the answer raises (for example: is a substitute suggestion worth it if 35% leave at the moment they see "sold out"; should the cache be fixed first; what can change on a placed order).
