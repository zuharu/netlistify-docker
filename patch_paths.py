#!/usr/bin/env python3
"""
Dynamic path override for Netlistify inference.py.
Rewrites hardcoded paths to match container directory layout.
"""
import os
import sys
import re

INFERENCE_PATH = "/app/inference.py"


def apply_patch(path: str):
    with open(path, "r") as f:
        content = f.read()

    substitutions = [
        (r'torch\.load\(\s*"bubble_orientation/res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/res50_1.pt",'),
        (r'torch\.load\(\s*"bubble_orientation/cc_res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/cc_res50_1.pt",'),
        (r'img_dir\s*=\s*"[^"]*"',
         r'img_dir = "/workspace/input/"'),
        (r'output_folder\s*=\s*Path\(\s*"[^"]*"\s*',
         r'output_folder = Path("/workspace/results/"'),
    ]

    modified = False
    for pattern, replacement in substitutions:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            modified = True
            print(f"  Patched: {pattern[:55]}... ({count} occurrence(s))")

    if modified:
        with open(path, "w") as f:
            f.write(content)
        print("PASS: Path overrides applied to inference.py")
    else:
        print("FAIL: No paths matched.", file=sys.stderr)
        sys.exit(1)


def main():
    print("[patch_paths] Applying container path overrides ...")
    if not os.path.exists(INFERENCE_PATH):
        print(f"FAIL: {INFERENCE_PATH} not found.", file=sys.stderr)
        sys.exit(1)
    apply_patch(INFERENCE_PATH)
    sys.exit(0)


if __name__ == "__main__":
    main()
