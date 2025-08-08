
get_info = subprocess.run(
    ["nvme", "id-ctrl", "/dev/nvme0", "-o", "json"],
    capture_output=True,
    text=True
)  
     serial = id_data.get("sn")