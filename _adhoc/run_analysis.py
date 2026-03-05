# Wrapper to run the analysis script
import subprocess, sys, os
script = os.path.join(r"C:\Users\rikit\Projects\2_\u30af\u30e9\u30a4\u30a2\u30f3\u30c8\u30c7\u30fc\u30bf\lightmarks", "analyze_topics.py")
print(f"Running: {script}")
print(f"Exists: {os.path.exists(script)}")
result = subprocess.run([sys.executable, script], capture_output=True, text=True, encoding="utf-8", errors="replace")
print("STDOUT:", result.stdout[:500] if result.stdout else "(empty)")
if result.stderr:
    print("STDERR:", result.stderr[:2000])
print("Return code:", result.returncode)

# Check output file
output = r"C:\Users\rikit\Projects\topic_analysis_output.txt"
if os.path.exists(output):
    print(f"\nOutput file created: {output}")
    print(f"Size: {os.path.getsize(output)} bytes")
else:
    print("Output file not created!")
