#!/bin/env python3.9
import subprocess
import platform

def print_header(use_passthru, nvme_device="/dev/nvme0"):
    print("="*80)
    print("NVMe Test Suite")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Script: {os.path.basename(__file__)}")
    print(f"Python Version: {platform.python_version()}")
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Admin Passthru: {'Enabled' if use_passthru else 'Disabled'}")

    # Try to get NVMe device info
    try:
        nvme_info = subprocess.check_output(
            ["nvme", "id-ctrl", nvme_device, "-o", "json"], text=True
        )
        nvme_json = json.loads(nvme_info)
        print(f"NVMe Model: {nvme_json.get('mn', 'Unknown')}")
        print(f"NVMe Serial: {nvme_json.get('sn', 'Unknown')}")
        print(f"Firmware Rev: {nvme_json.get('fr', 'Unknown')}")
    except Exception as e:
        print(f"NVMe info not available ({e})")

    # Try to get nvme-cli version
    try:
        nvme_cli_ver = subprocess.check_output(["nvme", "--version"], text=True).strip()
        print(f"nvme-cli version: {nvme_cli_ver}")
    except Exception:
        print("nvme-cli not available")

    print("="*80)
    print()