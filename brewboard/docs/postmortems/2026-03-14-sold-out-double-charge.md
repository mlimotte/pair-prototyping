# Postmortem: double charges after a sold-out change (2026-03-14)

**What happened.** For 40 minutes at Union Station, 23 customers were charged twice. A change let the counter edit an order line when a milk was sold out. The edit sent a second line to the POS instead of replacing the first. The POS charged both.

**Fix.** We removed the counter edit. The counter now rejects the line and either refunds it or makes the drink with another milk without changing the order.

**Follow-ups.**
- Any change to an order line after it is placed needs the POS vendor to support line replacement (their v4 contract, not scheduled).
- Add an alert on duplicate charges per order. (done)
