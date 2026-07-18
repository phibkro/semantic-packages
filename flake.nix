{
  description = "Locked semantic-packages verification toolchain";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/a418a0f7ab27a138f681319fcb30e6f1f58dfa44";
    # Wave 4's accepted Rust binaries were linked by this exact GCC wrapper.
    # bbacb131 updated glibc from 2.42-61 to 2.42-67; this signed release pin
    # retains the accepted wrapper without rolling back unrelated tools.
    gcc-nixpkgs.url = "github:NixOS/nixpkgs/e8210c649915deed7080033cdbabcc19e40bb899";
  };

  outputs = { nixpkgs, gcc-nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      gccPkgs = import gcc-nixpkgs { inherit system; };
      inherit (pkgs) lib;

      exact = name: expected: package:
        assert lib.assertMsg (package.version == expected)
          "${name} version drift: expected ${expected}, got ${package.version}";
        package;

      pythonBase = exact "Python" "3.14.6" pkgs.python314;
      python = pythonBase.withPackages (pythonPackages: with pythonPackages; [
        jsonschema
        rfc3339-validator
      ]);
      # Use the compiler output directly. The nixpkgs rustc wrapper adds host
      # flags that change Wave 4's recorded realization bytes even though the
      # compiler commit is identical.
      rust = exact "Rust" "1.96.1" pkgs.rustc.unwrapped;
      # Match the default stdenv linker used for the accepted Wave 4 binary
      # digests; gcc15 is the same release but a distinct wrapper derivation.
      # Its older glibc closure is scoped to evidence reproduction, not a
      # deployment recommendation.
      gcc = exact "GCC" "15.2.0" gccPkgs.gcc;
      deno = exact "Deno" "2.9.2" pkgs.deno;

      # The source-built nixpkgs Lean package reports only the release tag. The
      # accepted proof evidence records the full commit embedded in Lean's
      # official release binary, so package that artifact directly and pin its
      # content hash as well as the surrounding nixpkgs revision.
      lean = pkgs.stdenv.mkDerivation {
        pname = "lean4-toolchain";
        version = "4.30.0";
        src = pkgs.fetchurl {
          url = "https://github.com/leanprover/lean4/releases/download/v4.30.0/lean-4.30.0-linux.tar.zst";
          hash = "sha256-Ta10FBwsEZyhqmJmVr6DuOFCOK+6lycf178es/CBsxk=";
        };
        nativeBuildInputs = [ pkgs.autoPatchelfHook pkgs.zstd ];
        buildInputs = [ pkgs.stdenv.cc.cc.lib pkgs.gmp pkgs.zlib pkgs.libuv ];
        dontConfigure = true;
        dontBuild = true;
        installPhase = "mkdir -p $out && cp -r . $out/";
        autoPatchelfIgnoreMissingDeps = [ "*" ];
      };

      toolchainCheck = pkgs.writeShellScriptBin "semantic-toolchain-check" ''
        set -eu

        test "$(${python}/bin/python3 --version)" = "Python 3.14.6"
        ${python}/bin/python3 -c 'import importlib.metadata as m; assert m.version("jsonschema") == "4.26.0"; assert m.version("rfc3339-validator") == "0.1.4"'
        test "$(${lean}/bin/lean --version | head -n 1)" = "Lean (version 4.30.0, x86_64-unknown-linux-gnu, commit d024af099ca4bf2c86f649261ebf59565dc8c622, Release)"
        test "$(${rust}/bin/rustc --version)" = "rustc 1.96.1 (31fca3adb 2026-06-26) (built from a source tarball)"
        ${rust}/bin/rustc --version --verbose | grep -Fx 'commit-hash: 31fca3adb283cc9dfd56b49cdee9a96eb9c96ffd'
        ${rust}/bin/rustc --version --verbose | grep -Fx 'commit-date: 2026-06-26'
        test "$(${gcc}/bin/gcc -dumpfullversion)" = "15.2.0"
        test "$(${deno}/bin/deno --version | sed -n '1p')" = "deno 2.9.2 (stable, release, x86_64-unknown-linux-gnu)"
        test "$(${deno}/bin/deno --version | sed -n '3p')" = "typescript 6.0.3"
      '';
    in
    {
      checks.${system}.toolchain = pkgs.runCommand "semantic-toolchain-check" {
        nativeBuildInputs = [ toolchainCheck ];
      } ''
        semantic-toolchain-check
        touch "$out"
      '';

      devShells.${system}.default = pkgs.mkShellNoCC {
        packages = [
          python
          lean
          rust
          gcc
          deno
          toolchainCheck
        ];

        shellHook = ''
          # Keep the shell free of an ambient stdenv compiler setup and export
          # the evidence-bound tools explicitly. Injected NIX_* compiler flags
          # would change the accepted Rust realization bytes.
          export LEAN="${lean}/bin/lean"
          export RUSTC="${rust}/bin/rustc"
          export CC="${gcc}/bin/gcc"
          export DENO="${deno}/bin/deno"
          unset NIX_CFLAGS_COMPILE NIX_LDFLAGS NIX_CFLAGS_LINK NIX_BINTOOLS
          unset NIX_BINTOOLS_WRAPPER_TARGET_HOST_x86_64_unknown_linux_gnu
          unset NIX_CC_WRAPPER_TARGET_HOST_x86_64_unknown_linux_gnu
          semantic-toolchain-check
        '';
      };
    };
}
