# Decisions

## Logging: SQLite with SHA-256 text hashing

**What:** every prediction logs to a local SQLite database.
**Why SQLite:** zero infrastructure, queryable with SQL, file-based.
Swaps to Postgres in production with one connection string change.
**Why hash text:** PII safety. We never store raw user input. The hash
plus length is enough to find a specific prediction by recomputing the
hash from the user's complaint.
**In production:** Postgres + structured logs to a log aggregator
(Datadog, CloudWatch, etc).

## Development environment: Docker-first

Apple Silicon Python 3.11 + transformers showed intermittent shutdown
crashes during pytest. Linux containers are rock-solid for the same
code, and they match our production deploy target. Doing dev inside
the container removes a class of "works on my machine" bugs.
