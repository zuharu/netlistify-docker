#!/usr/bin/env python3
"""Dynamic path override for Netlistify."""
import os, sys, re

def patch_file(path, subs):
    with open(path) as f:
        content = f.read()
    modified = False
    for pattern, replacement in subs:
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
    subs = [
        (r'torch\.load\(\s*"bubble_orientation/res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/res50_1.pt",'),
        (r'torch\.load\(\s*"bubble_orientation/cc_res50_1\.pt"\s*,',
         r'torch.load("/opt/netlistify/weights/cc_res50_1.pt",'),
        (r'img_dir\s*=\s*"[^"]*"',
         r'img_dir = "/workspace/input/images/"'),
        (r'output_folder\s*=\s*Path\(.+',
         r'output_folder = Path("/workspace/results/")'),
    ]
    ok = patch_file("/app/inference.py", subs)
    print("PASS: inference.py" if ok else "FAIL: No inference.py matches")

def patch_main_config():
    subs = [
        (r'return\s+"runs/[^"]*best_train\.pth"',
         'return "/opt/netlistify/weights/best_train.pth"'),
    ]
    ok = patch_file("/app/main_config.py", subs)
    print("PASS: main_config.py" if ok else "NOTE: main_config.py unchanged")

def patch_testing():
    subs = [
        (r'(weight_dir\s*=\s*Path\(__file__\)\.parent\s*/)\s*"runs/FormalDatasetWindowedLinePair"',
         r'\1 "/opt/netlistify/weights"'),
    ]
    ok = patch_file("/app/testing.py", subs)
    print("PASS: testing.py" if ok else "NOTE: testing.py unchanged")

def main():
    print("[patch_paths] Applying container path overrides ...")
    patch_inference()
    patch_main_config()
    patch_testing()
    sys.exit(0)

if __name__ == "__main__":
    main()
