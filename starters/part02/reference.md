# Brief: customers leave or switch when oat sells out

## What we see
Oat sells out on many afternoons. Customers who wanted oat then switch milk or leave. Some still order oat in the app after Sam marks it out, and the counter refunds them or makes the drink with almond.

## Who it affects
Customers who want oat, after a sell-out. Baristas at the counter.

## Evidence
- About 45 of 150 feedback rows are about oat selling out. Their average rating is 2.2 of 5; the other rows average 3.8. (customer-feedback.csv)
- "Came in for an oat latte. Sold out again. Left." (feedback, 8 rows)
- Sam: people order oat "for a few minutes after" it is marked out; when made with almond, "the ticket still says oat". (barista-notes.md)

## What we do not know
- How many customers leave when oat sells out, and how many switch?
- How does sold-out status reach the app, and why can customers still order oat after it is marked out?
- What does the dashboard abandonment rate count? Does it include people who leave before they add to the cart?
- What can we change on a placed order? (March double-charge postmortem)

## Out of scope
Syrups and food. Loyalty points. Personalized recommendations.

## How we will know
The share of customers who leave after they see a milk sold out. Set a target after we measure the baseline.
