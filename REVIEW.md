# What a reviewer checks in Mailroom

Taken from AGENTS.md. Rules no test can catch come first.

## Rules no test can catch
1. **No real people.** No real person's name or email address appears anywhere: only `@example.com`, and `@resend.dev` for practice sends.
2. **Tests first, and the expected answers are mine.** No expected answer in a test was changed to make it pass. Check the diff of `tests/`.
3. **Write only with what I have learned.** New Python ideas are named and agreed first (see "How I learn" in AGENTS.md).
4. **One module per job, and only the commands module prints.**
5. **Today's date is read in one place only**, the command line; logic takes the run date as an argument.
6. **No traceback for a user's mistake.** Bad data is reported with its row and field.
7. **The key and the address come from the environment.** No key is written in the code or committed.
8. **The pull request shows its evidence**: real pytest, pyright and `mailroom check` output.

## Rules the checks also enforce
9. Every function has type hints, and pyright is clean.
10. Data from outside, and JSON read from a file, goes through a model.
11. Sending works only against localhost, and only to `@example.com` or `@resend.dev`.
12. Each status is handled on purpose; a 4xx is never retried; every send has an idempotency key.
13. Sending has a limit on how many run at once.

When you comment, name the rule by its number.
