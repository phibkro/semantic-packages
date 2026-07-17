# Problem statement

Software packages currently bundle together several concerns that should be independently selectable:

- a semantic abstraction;
- one implementation;
- implementation-language and runtime assumptions;
- tests and documentation;
- trust in a publisher and its transitive executable dependencies.

Interfaces generally describe names and types while leaving laws, protocols, effects, resource obligations, performance, security properties, assumptions, and evidence informal.

This makes composition depend on human interpretation and makes semantic reuse require executable trust.

## Proposed shift

Treat the primary package artifact as a semantic specification. Distribute realizations and evidence separately.

```text
problem → choose specification → choose assurance policy
        → resolve or author realization → verify → execute
```

The research question is not merely how to add richer types to packages. It is how to formalize a software package as a theory with observable behavior, multiple models, heterogeneous evidence, deployment profiles, and refinement/version relations.
