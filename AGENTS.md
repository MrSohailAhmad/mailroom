# Mailroom – project rules

- Mailroom is a command-line tool for one newsletter: Kettlebird Tea's Steep Club. It reads the subscribers, checks an issue, and sends it to a practice mail server.
- Use uv for everything.
- Never use a real person's email address. Use @example.com, and @resend.dev for practice sends.
- Commit and push after every step.
- Keep every subscriber made up; never put real customer data in this repository.
- Behaviors first: I give the expected answers, you write them as checks, show them failing, then write the code.
- Never read today's date inside the logic. Pass the run date in.
- Never read today's date inside the logic. Pass the run date in.
- When something breaks, show me the full error before changing anything.
- I decide the test cases and their answers. Never change an expected answer to make a test pass.
- Subject and preview length count what Python's len() counts.
- One module per job. Only the commands module prints.
- Every function has type hints, and pyright must be clean.
- Pass Subscriber and Issue objects around, never raw rows or raw text.
- Data from outside goes through the model before any code uses it.
- The model checks the shape. Our own rules check the meaning.
- Report every problem with its row. No traceback for a user's mistake.
- JSON read from a file is outside data: it goes through a model too.
- The key and the address come from the environment. Sending works only against localhost.
- Handle each status on purpose. Never retry a 4xx.
- Send with a limit on how many at once.
- Retry only what can succeed later, and every send has an idempotency key.
- Mailroom sends with httpx, not the resend SDK: our guards, errors, retries and async stay in our own code.
- Every change goes on a branch and arrives as a pull request.
- A pull request shows its evidence.
- The checks must pass before a merge.
- Reviewers read REVIEW.md.

## How I learn
- I am new to Python. I have completed up to 15.6 of https://agentfactory.panaversity.org/building-ai-workers/programming-fundamentals/ and I update this number as I learn.
- Write only with what I have learned. If something new would really help, stop and tell me its name in one line. I decide.
- When the code uses something new, show me that piece first and ask me to predict what it does. Stay quiet while I guess. Then run it, and explain a line only when I ask.
