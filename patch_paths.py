#!/usr/bin/env python3
"""
Dynamic path override for Netlistify.

Runs on container boot AFTER validation. Rewrites hardcoded paths in
inference.py and main_config.py to match container directory layout.
"""
import os
import sys
import re


def patch_file(path: str, substitutions: list) -> bool:
    with open(path, "r") as f:
        content = f.read()
    modified = False
    for pattern, replacement in substitutions:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            modified = True
            print(f"  Patched: {pattern[:55]}... ({count})")
    if modified:
        with open(path, "w") as f:
            f.write(content)
    return modified


def patch_inference():
    path = "/app/inference.py"
    subs = [
        (r'torch\.load\(\s*"bubble_orientation/res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/res50_1.pt",'),
        (r'torch\.load\(\s*"bubble_orientation/cc_res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/cc_res50_1.pt",'),
        (r'img_dir\s*=\s*"[^"]*"',
         r'img_dir = "/workspace/input/"'),
        (r'output_folder\s*=\s*Path\(\s*"[^"]*"\s*',
         r'output_folder = Path("/workspace/results/"'),
    ]
    ok = patch_file(path, subs)
    print(f"PASS: inference.py" if ok else "FAIL: No inference.py matches")


def patch_main_config():
    path = "/app/main_config.py"
    subs = [
        (r'return\s+"runs/[^"]*best_train\.pth"',
         'return "/opt/netlistify/weights/best_train.pth"'),
        (r'return\s+"/[^"]*best_train\.pth"',
         'return "/opt/netlistify/weights/best_train.pth"'),
    ]
    ok = patch_file(path, subs)
    print(f"PASS: main_config.py" if ok else "NOTE: main_config.py DETR path not patched")


def main():
    print("[patch_paths] Applying container path overrides ...")
    for target in ["/app/inference.py", "/app/main_config.py"]:
        if not os.path.exists(target):
            print(f"WARNING: {target} not found — skipping", file=sys.stderr)
    patch_inference()
    patch_main_config()
    sys.exit(0)


if __name__ == "__main__":
    main()
