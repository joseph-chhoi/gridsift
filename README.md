# GridSift

Automatically classify and sort MRI series from raw hospital DICOM exports.

## Requirements

- Python 3.9+
- 4GB RAM minimum (8GB recommended)

## Installation

```bash
git clone https://github.com/joseph-chhoi/gridsift.git
cd gridsift
pip install pydicom PyQt6 llama-cpp-python
```

## Download the AI model

Download the Llama 3.2 3B model (2GB) and place it in the gridsift folder:

[Download Llama 3.2 3B](https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf)

## Run

```bash
python app.py
```

## What it does

GridSift takes a raw DICOM dump folder as input and:
- Groups files by SeriesInstanceUID
- Classifies each series using MRI physics parameters (TE, TR, flip angle, inversion time)
- Falls back to keyword matching and LLM normalization for ambiguous cases
- Sorts files into labeled subfolders: T1, T2, FLAIR, DWI, DCE, flagged_for_review
- Outputs a CSV log of every classification decision with confidence scores

## Supported sequence types

T1, T2, FLAIR, DWI, DCE, localizer. Uncertain series are flagged for human review rather than silently misclassified.