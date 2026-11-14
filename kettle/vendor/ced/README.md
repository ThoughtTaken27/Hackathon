# Vendored CED model code

`modeling_ced.py` and `configuration_ced.py` are copied from the Hugging Face repo
[mispeech/ced-tiny](https://huggingface.co/mispeech/ced-tiny) at revision
`ace276d29dd0bb3f3517b0fa8cf300738c409019` (Copyright 2023 Xiaomi Corporation and The HuggingFace Inc. team),
licensed under the Apache License 2.0 (`LICENSE` in this folder).

Why vendored: so Kettle never runs `trust_remote_code` and never needs the network at runtime.

Changes made by the Kettle team (Apache-2.0 §4b):
- `configuration_ced.py`: removed the block that downloaded AudioSet label names from `topel/ConvNeXt-Tiny-AT`;
  the same 527 names are already in `models/ced-tiny/config.json` (`id2label`).
- The feature extractor file is not vendored; `kettle/encoders.py` builds the same log-mel front end
  (torchaudio `MelSpectrogram` + `AmplitudeToDB(top_db=120)`, values from `preprocessor_config.json`).
