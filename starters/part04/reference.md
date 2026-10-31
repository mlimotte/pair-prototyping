# Reference answer: switch or leave?

## Product view
"Mostly they switch. Very few leave." It compared order mix and order volume in sell-out windows: oat fell from about 29% of milk lines to 1%, almond and whole rose, and orders fell about 4%. It called 4% the upper bound on leavers.

## Engineer, no pointer
"Mostly they switch. The data shows little sign of customers leaving." Same method, plus the code. It gave no leave rate: it called the 3% dip in order volume the best proxy. It noticed that a customer who taps sold-out oat never gets a cart, but it could not measure them.

## Engineer, with pointer
"Most switch, but about a third leave." 477 sessions saw oat sold out; 166 (35%) left without ordering; 201 switched to almond and 110 to whole.

## What changed
- Leave rate: about 4% (upper bound), about 3% (a proxy), then 35%.
- The orders table holds only people who ordered. The 166 who left are not in it. Their absence looks like switching.
- The dashboard tile counts carts, and 156 of the 166 left before they had a cart. The tile also drops carts open under 60 seconds. It counted 1 of the 166. It is lower on sell-out days (7.1%) than on other days (7.7%).
- Run 2 had the same access. The session events are not in the warehouse and not in the repo, so it did not know they existed. One sentence told it where to look.
- More: `brewboard/stock.py` caches sold-out status for 5 minutes, so customers order oat after it is gone. `logs/counter/` shows 12 rejected lines.
- Next question for Morgan: 35% leave the moment they see "sold out". Does a suggestion at that moment win them back, and should we fix the 5-minute cache first?
