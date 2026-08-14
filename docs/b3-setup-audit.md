# B3 external setup audit

Both successful setup attempts are Git-ignored external artifacts retained on
the local host.

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
No upstream code, checked extraction, proof artifact, or sibling repository was
modified.
