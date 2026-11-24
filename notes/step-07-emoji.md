# Step 7: how long is an emoji?

Subject: "👍🏽 Thanks for joining"

- A reader sees 19 characters: one thumbs-up (with skin tone), a space and "Thanks for joining".
- Python's len() says 21: the emoji is two code points (👍 U+1F44D and the skin-tone modifier 🏽 U+1F3FD).

Two ways the check could count:
1. Code points, what len() counts (21).
2. Grapheme clusters, what a reader sees (19). Needs an extra library.

Decision: count what Python's len() counts. It is simple, needs no extra library, and errs on the safe side (a subject never looks longer than len() says).
