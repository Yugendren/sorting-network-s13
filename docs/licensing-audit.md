# Licensing audit

## SENSO distribution

The author-hosted `symmetry-1.1.tar.gz` is a mixed-license distribution. Its
top-level notice delegates terms to subdirectories. The sorting experiment's
`experiments/COPYING` is BSD-3-Clause. The OpenBEAGLE and sorting-network
library headers identify LGPL-2.1-or-later. Bundled OPAL, Algorithm::Networksort,
and other components retain separate notices.

Decision: do not vendor the archive. Fetch the exact hashed artifact into the
Git-ignored cache, retain its notices there, apply only the audited macOS
portability patch, and run it as an external pinned artifact. Project evidence
records the archive and patch hashes.

## Harder repository and certificate

The `jix/sortnetopt` repository at the frozen commit contains no LICENSE or
COPYING file, so its redistribution license is `UNKNOWN`. Do not vendor or
modify it in this repository. Clone the exact commit into the ignored external
cache and execute the official scripts there. The Zenodo certificate metadata
states CC-BY-4.0; the 1.2 GB compressed file and decompressed certificate are
never committed.

## Other sources

The optional Wang repository declares MIT. The maintained catalog repository
has no license file at the frozen commit, so only the cited witness is
transcribed into the canonical fact artifact. Paper PDFs stay in the ignored
source cache and are cited, not redistributed by this repository.
