# B2 external build audit

Both setup attempts are Git-ignored external build artifacts and remain on the
local host.

- `MEASURED`: attempt `attempt-20260814T231943Z` built and installed the pinned
  libraries but failed while linking the sorting executable because the build
  command omitted Homebrew's Boost include directory. The preserved log is
  271 MiB of build tree plus log SHA-256
  `1f2c221c04f76d94279d4311d032b308f6e0d3a8071a420215843eb040546d62`.
- `MEASURED`: attempt `attempt-20260814T232113Z` added only
  `-I/opt/homebrew/include` to that link command. The serial build and smoke
  run passed. Its manifest SHA-256 is
  `24f47b42a966ed1b53553d4a77aca305af5cdd19ed12f44f0a8238210e5078e4`;
  its binary SHA-256 is
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`.

No upstream source or algorithm parameter changed between the attempts. The
only source delta in the successful build is the audited portability patch.
