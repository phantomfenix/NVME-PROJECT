import subprocess
import json

#CLIMETHOD
smartlog = subprocess.run(
    ["nvme", "smart-log", "/dev/nvme0n1", "-o", "json"],
    capture_output=True,
    text=True
)
slog_data = json.loads(smartlog.stdout)

#Get vital info
media_errors = slog_data.get("media_errors")
POH = slog_data.get("power_on_hours") #Power on hours
Percentage_usage = slog_data.get("percent_used")

if media_errors!=0:
    print("media errors found:")
    print(media_errors)
else:
    print("No media errors")

if POH > 1000:
    print("Warning, power on hours exceed 1000 hours")  
else:
    print("Power on hours less than 1000")
    
if Percentage_usage>100:
    print("Warning percentage usage value exceeds 100%")
else:
    print("Percentage usage below 100%")
       
    
          



