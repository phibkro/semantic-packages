# Loader fixture packet v1

These records are the durable data inputs for `scripts/loader_fixture_check.py`.
The harness copies them into temporary source trees so it can exercise lexical path
aliases, directory overlap, malformed input, ignored extensions, and both explicit
and recursively discovered symbolic links without committing an invalid lowercase
`.json` file or a live symbolic link.

The positive import graphs intentionally include self, cyclic, diamond, and repeated
exact edges. Imports are visibility checks over the supplied record set; they do not
drive file acquisition or impose an evaluation DAG. In the dangling case, the target
record exists under `outside/` but the harness supplies only `loaded/`.

The stable oracle surface is exit status plus diagnostic code, normalized source
label, JSON pointer, and ordering. Text after a diagnostic's `:` is informative prose
and is not frozen by this packet.
