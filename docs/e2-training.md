# E2 version-1 training subgate

The frozen development split has an observed pathology: all 1,216 positive
rows occur in calibration seed 18, so training seeds 1--16 have zero positives.
Version 1 does not move the seed, relabel examples, add data, or change its
binary objective. The configured capped class weight is interpreted as the
limit `min(infinity, 100) = 100`, and the limitation is explicit evidence.

`tools/e2_train_gate.py` transfers only the content-addressed compressed E1
dataset and committed training script to the authorized RTX 3060 server. It
runs the frozen 85-64-32-1 MLP training twice with seed 2026081501 and
deterministic PyTorch algorithms. The model export, generated C++ float header,
and inference fixture must be byte-identical across replays.

Run from a clean commit:

```sh
make method-e2-train
make evidence-check
```

This subgate does not access validation or E3 seeds and does not by itself pass
E2. Its selected checkpoint is next compiled into the one frozen truncation
integration, then evaluated exactly once on the validation partition.
