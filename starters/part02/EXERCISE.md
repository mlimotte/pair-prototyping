# Part 2: cut six pages to half a page

Morgan sent you `brewboard/inputs/six-page-doc.md`, an agent-written proposal. Morgan's prompt was two sentences:

> When oat milk sells out, customers who wanted oat either switch to another milk or leave. When the milk a customer picks is sold out, suggest a substitute.

## Do this

1. Read the six-page document. Then read the other inputs: `brewboard/inputs/customer-feedback.csv` and `brewboard/inputs/barista-notes.md`.
2. Write a half-page brief in `answer.md` (250 words at most). Use the template from the post: What we see, Who it affects, Evidence, What we do not know, Out of scope, How we will know.
3. Keep only what someone knows. Each number has a source. Turn each guess in the document into a question, or cut it.
4. You may use Claude Code to help, for example to count themes in the feedback. You write the brief.
5. Grade it:

```bash
cd grade && claude "/grade"
```

Keep your brief. In part 7, it becomes a real change to Brew Board.

You do not need the code or the data in this part. Part 4 uses them.
