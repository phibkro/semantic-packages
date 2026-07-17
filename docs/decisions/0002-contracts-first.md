# ADR 0002: Contracts before implementations

## Status

Accepted.

## Decision

The platform identifies packages by semantic specification. Realizations and evidence are separately versioned artifacts associated with that specification.

## Consequences

- Multiple implementations can compete under one semantic identity.
- Consumers can resolve implementations based on deployment and evidence policy.
- The system must model underspecification and unknown evidence explicitly.
