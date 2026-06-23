#!/usr/bin/env python3
"""
Container self-validation diagnostic script.
Checks GPU, weight files, and deserialization on boot.
"""
import os
import sys
import torch

WEIGHTS_DIR = "/opt/netlistify/weights"
REQUIRED_WEIGHTS = {
    "DETR Wire Connectivity": "best_train.pth",
    "ResNet50 Orientation":   "res50_1.pt",
    "Component Classifier":   "cc_res50_1.pt",
}


def check_gpu() -> str:
    if not torch.cuda.is_available():
        print("FAIL: CUDA not available — no GPU detected.", file=sys.stderr)
        sys.exit(1)
    name = torch.cuda.get_device_name(0)
    cap = torch.cuda.get_device_capability(0)
    print(f"  GPU: {name}")
    print(f"  Compute Capability: {cap[0]}.{cap[1]}")
    if cap[0] < 8:
        print("  WARNING: Below Ampere (8.0). Inference may be slow.", file=sys.stderr)
    return name


def check_weights():
    all_ok = True
    for label, filename in REQUIRED_WEIGHTS.items():
        path = os.path.join(WEIGHTS_DIR, filename)
        if not os.path.exists(path):
            print(f"FAIL: Missing {label} at {path}", file=sys.stderr)
            all_ok = False
        else:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb < 1.0:
                print(f"WARNING: {label} is only {size_mb:.1f} MB", file=sys.stderr)
            print(f"  {label}: {size_mb:.1f} MB")
    return all_ok


def check_deserialization():
    path = os.path.join(WEIGHTS_DIR, "res50_1.pt")
    try:
        checkpoint = torch.load(path, map_location="cuda:0", weights_only=False)
        if isinstance(checkpoint, dict) or hasattr(checkpoint, "state_dict"):
            print("  Model deserialization: OK")
        else:
            print(f"  WARNING: Unexpected checkpoint type={type(checkpoint).__name__}", file=sys.stderr)
    except Exception as exc:
        print(f"FAIL: Cannot load model: {exc}", file=sys.stderr)
        return False
    return True


def main():
    print("=== Netlistify Container Diagnostics ===")
    print("[1/3] GPU check ...")
    check_gpu()
    print("[2/3] Weight file verification ...")
    if not check_weights():
        sys.exit(1)
    print("[3/3] Deserialization smoke test ...")
    if not check_deserialization():
        sys.exit(1)
    print("=== All diagnostics passed ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
