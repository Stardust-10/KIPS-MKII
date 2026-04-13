import csv
import time
import pandas as pd
import matplotlib.pyplot as plt

def record_heartbeat_run(serial_port, csv_path, duration=10):
	start = time.time()
	
	with open(csv_path, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["timestamp", "raw_value", "bpm", "beat"])
		
		while time.time() - start < duration:
			line = serial_port.readline().decode(errors="ignore").strip()
			
			# Expected format
			# HB:523,78,1
			if not line.startswith("HB:"):
				continue
			
			payload = line.split(":", 1)[1]
			parts = payload.split(",")
			
			if len(parts) != 3:
				continue
			
			raw_value = float(parts[0])
			bpm = float(parts[1])
			beat = int(parts[2])
			
			t = time.time()
			writer.writerrow([t, raw_value, bpm, beat])
			
def make_heartbeat_plot(csv_path, png_path):
	df = pd.read_csv(csv_path)
	
	plt.figure(figsize=(8,4))
	plt.plot(df["timestamp"], df["raw_value"])
	plt.xlabel("Time (s)")
	plt.ylabel("Sensor Value")
	plt.title("Heartbeat Sensor Output")
	plt.grid(True)
	plt.tight_layout()
	plt.savefig(png_path)
	plt.close()
	
def make_bpm_plot(csv_path, png_path):
	df = pd.read_csv(csv_path)
	
	plt.figure(figsize=(8,4))
	plt.plot(df["timestamp"], df["bpm"])
	plt.xlabel("Time (s)")
	plt.ylabel("BPM")
	plt.title("Heart Rate Over Time")
	plt.grid(True)
	plt.tight_layout()
	plt.savefig(png_path)
	plt.close()
	
	
	
	
	
	
	
