# B3 external setup audit

All setup attempts are Git-ignored external artifacts retained on the local
host.

- `MEASURED`: toolchain attempt `attempt-20260814T234115Z` completed in
  189.545153 wall seconds. Native Rust 1.95.0 produced an arm64 search binary
  with SHA-256
  `cd82f096f1e2fb7dacc647d9bc2458aa0b7c9324e143a9d90bd2fc21c3c2bd93`.
  Stack 3.11.1 installed the frozen x86_64 GHC 8.6.5 snapshot under Rosetta and
  produced the checked verifier with SHA-256
  `b37025c99c59cc1df764a79980430c5cf46e01dffa2f0a708378089608bec073`.
  The build-manifest SHA-256 is
  `a5ca73116e4169f3e8b2e543c32021218bb25606eb056aa0010d957abb833fd2`;
  the captured log SHA-256 is
  `ab8e2202419dfaef504aa934ea0a5d7bdf5a4f9275aab035bf7ffd9134c63c3b`.
- `MEASURED`: patched-worktree attempt `attempt-20260814T235625Z` completed in
  36.608286 wall seconds and demonstrated that the diagnostic-only patch
  builds. It was superseded before scoring because BSD `patch` retained an
  untracked `.orig` backup and the generated Cargo resolution was not yet part
  of the manifest. Its preserved build-manifest SHA-256 is
  `931c1eb6c9059ae9f031aad85704e526192c8baf2672c00de2b6651baa7d2dd2`.
- `MEASURED`: patched-worktree attempt `attempt-20260814T235750Z`
  completed in 30.475383 wall seconds. Patch SHA-256 is
  `2777a9772e19b01c9a6f178e5d40c9fb504cf7312350f44062fe4b174cdc0aa8`;
  the generated Cargo lock SHA-256 is
  `a999aa381b5436ff2a85565fc5985fe53fe134d4d0baebb6e57880ee807747f9`;
  the arm64 Rust binary SHA-256 is
  `92947286c87068a9688c16a024c97bf819a19683677c80471ee0f7941fce6d8c`.
  The x86_64 checked verifier is byte-identical to the first build. Its
  build-manifest SHA-256 is
  `ca35a703e4a293eccc5b95bbfaccc80ca2ee095721995fe2af9a82fdba9e3429`;
  log SHA-256 is
  `92716723fc8f3c1556d9129a2069dbab76c2b1089f4f2b05a2256de687efefae`.
  It was superseded only to remove a trailing blank context marker from the
  project-owned patch file; the applied `logging.rs` bytes did not change.
- `MEASURED`: active attempt `attempt-20260815T000004Z` completed in 31.69925
  wall seconds. Normalized patch SHA-256 is
  `49ce5d772ce6dfcb986b7185ec0e7c14d27681126d4dd703bb4ae259cafcdc42`;
  patched `logging.rs` SHA-256 remains
  `a4b1a04306f999196f8d3138f7fd698cde978dccbd67c842e46e026344e1962e`.
  The generated Cargo lock SHA-256 remains
  `a999aa381b5436ff2a85565fc5985fe53fe134d4d0baebb6e57880ee807747f9`;
  the path-bearing debug build has Rust binary SHA-256
  `6a158cc98a253713d26110f2bb0bc1ec8aae81a2f687d73ab8019e8e1972f030`.
  Active build-manifest SHA-256 is
  `b364c09a55914e654193b43823da0af27e6cf39018d3163120877470214d2a0d`;
  log SHA-256 is
  `dcf4fb4310cb18779803c7399d1318f2612bd27291c42c0ba6a8e844f5074dea`.
- `ARTIFACT_VERIFIED`: certificate attempt `attempt-20260814T234434Z`
  downloaded the Zenodo object in 282.576548 wall seconds. The compressed
  artifact is exactly 1,247,864,564 bytes with MD5
  `2847374c6bab1260c9771d6fafe65f44`; the decompressed artifact is exactly
  3,068,651,498 bytes with SHA-256
  `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e`.
  The certificate-manifest SHA-256 is
  `af0c69fa458388179ed00db83895abbcb778c3269933bd4bb4a20352156893f3`;
  the captured log SHA-256 is
  `76e62a4c88cf18859da7be6b5a0335f4aaf9288043814882acbdb68bababac97`.

The upstream repository remained detached and clean at
`0b5d09c47446096f9e3a0812b35afc72b7f2a718`. Its 44 tracked files have
aggregate SHA-256
`56b18efa19f3727f1945696f53bb597aec9b13ec210680578b1dc0b0b253a474`.
The original clone is unmodified. The active ignored worktree changes only
`src/logging.rs` through the recorded diagnostic portability patch. No checked
extraction, proof artifact, or sibling repository was modified.

The first `make baseline-b3` launch from source commit
`4364aaa585fd24d451cdaaa11030c57c6c7b4c04` failed before gate initialization:
direct execution of `tools/b3_gate.py` raised `ModuleNotFoundError: No module
named 'tools'`. No Rust search, Haskell checker, scored evidence directory, or
scientific output was created. The complete failure was retained in the task
execution record. The portability fix only adds the project root to the direct
script import path, and a subprocess regression test exercises that exact
entry mode before the retry.

Two subsequent scored failures are immutable evidence. Run
`b3-20260814T235403Z` stopped before search because macOS `realpath` rejected
the not-yet-created data directory. Run `b3-20260814T235503Z` reached the Rust
executable, which then panicked in the Linux-only `/proc/self/status`
diagnostic logger before calling the search. Their fixes pre-create only the
unique external data directory and make missing diagnostic metrics return the
logger's existing unavailable value. Neither alters the search or checker.

Run `b3-20260815T000143Z` then completed the official n=9 workflow and captured
`Just (9,25)`, but the strict parser expected the README's `Some` spelling and
failed rather than inferring equivalence. The preserved raw output establishes
the representation mismatch. The corrected parser accepts Haskell
`Just`/`Nothing` and documented `Some`/`None`, requires exactly one result line,
normalizes only the constructor, and records the raw line in subsequent
results.
