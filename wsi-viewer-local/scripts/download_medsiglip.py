#!/usr/bin/env python3
"""
Download and save the MedSigLIP model locally so the Docker can preload it.

By default saves to ./models/medsiglip-448. You can override with --out.

Usage:
  python scripts/download_medsiglip.py --out models/medsiglip-448

This script downloads both the model and processor.
"""

import argparse
import os
from transformers import AutoModel, AutoProcessor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-id', default='google/medsiglip-448')
    parser.add_argument('--out', default='models/medsiglip-448')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"Downloading model: {args.model-id} -> {args.out}")
    model = AutoModel.from_pretrained(args.model_id)
    processor = AutoProcessor.from_pretrained(args.model_id)
    model.save_pretrained(args.out)
    processor.save_pretrained(args.out)
    print("Done.")


if __name__ == '__main__':
    main()

