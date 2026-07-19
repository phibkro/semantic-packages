# Rust OrderedMap candidate

This dependency-free packet implements `ordered-map-runner-json-v1` using an immutable
ordered sequence of class-token/value pairs with linear lookup. That private source
representation is not Specification meaning. The adapter owns only valid bounded JSON
translation and opaque session handles.

```sh
candidate_dir=$(mktemp -d)
${RUSTC:-rustc} --edition=2024 -C opt-level=2 -C linker=${GCC:-gcc} \
  -o "$candidate_dir/ordered-map-rust" src/main.rs
"$candidate_dir/ordered-map-rust"
${RUSTC:-rustc} --edition=2024 --test -C linker=${GCC:-gcc} \
  -o "$candidate_dir/ordered-map-unit" src/ordered_map.rs
"$candidate_dir/ordered-map-unit"
```

Observed provenance is rustc 1.96.1 commit
`31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd` with gcc (GCC) 15.2.0.

adapter faithfulness and event completeness remain assumptions. external effects,
performance instrumentation, concurrency, malformed clients, registry-driven execution,
and cross-language interoperation are excluded. A runner report is an ephemeral fact,
not Evidence, review, registration, or acceptance authority.
