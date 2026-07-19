# OrderedMap reorder breaker

This packet is a targeted negative control for `ordered-map-runner-json-v1`. It uses
an independent persistent implementation and the Rust wire surface. Replacing an
already-present class deliberately moves that class to the end; all other bounded
behavior is ordinary.

The packet is test input, not Evidence, review, acceptance, registry membership, or
semantic authority. Its executable is built only into a temporary directory by the
repository reproduction check.
