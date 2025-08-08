
id_ctrl = subprocess.run(
    ["nvme", "id-ctrl", "/dev/nvme0", "-o", "json"],
    capture_output=True,
    text=True
)
id_data = json.loads(id_ctrl.stdout)

     serial = id_data.get("sn")
