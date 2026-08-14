# SENSO source and portability record

The author-hosted `symmetry-1.1.tar.gz` archive is frozen by size and SHA-256
in `config/frozen/sources.json`. The B0 feasibility probe used only a temporary
directory outside this repository and did not produce scored construction
evidence.

`MEASURED`: on the frozen Apple M4 host, the original configure step found the
Homebrew Boost installation. A serial build completed after the three
semantics-preserving changes in
`tools/patches/symmetry-1.1-macos.patch`:

1. qualify the dependent-base `push_back` call with `this->`;
2. map the removed GNU `slist` extension to `std::forward_list` under Clang;
3. replace two front erasures with the equivalent `pop_front()` operation.

GNU Make 3.81 exposed a dependency race with parallel compilation, so frozen
scored builds use `-j1`. An unscored smoke invocation with 13 channels,
population 2, generation 1, and seed 1 terminated normally and initialized
only 49- and 50-comparator networks. It was a setup probe, not one of the 20
frozen B2 seeds and not evidence of baseline reproduction.

No source behavior, fitness rule, mutation operator, comparator-count target,
or stopping criterion is changed by the portability patch. B2 must rebuild
from a freshly extracted, hash-checked archive and apply this exact patch.
