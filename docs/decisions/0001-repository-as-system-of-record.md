# ADR 0001: Repository as system of record

## Status

Accepted.

## Decision

Durable project intent, research synthesis, design, active plans, decisions, schemas, and evidence conventions live in the repository. Chat transcripts may inform updates but are not authoritative runtime context.

`AGENTS.md` remains short and points agents to deeper documents.

## Consequences

- Codex and other agents can start from the repository without hidden conversation context.
- Documentation drift becomes a repository quality problem that can be checked.
- Design changes must update the relevant source-of-truth document.
