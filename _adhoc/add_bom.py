import os
import glob

# Find the CSV file
base = r"C:\Users\rikit\Projects\2_クライアントデータ\lightmarks"
target = os.path.join(base, "vip-limo-kw候補.csv")

if os.path.exists(target):
    with open(target, 'rb') as f:
        data = f.read()

    # Check if BOM already exists
    if data[:3] == b'\xef\xbb\xbf':
        print("BOM already present")
    else:
        with open(target, 'wb') as f:
            f.write(b'\xef\xbb\xbf' + data)
        print(f"BOM added to: {target}")
        print(f"File size: {os.path.getsize(target)} bytes")
else:
    print(f"File not found: {target}")
