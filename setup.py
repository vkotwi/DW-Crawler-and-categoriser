import os
import sys
import csv

missing_packages = []
with open('requirements.txt', 'r') as req:
    csv.reader(req, delimiter='\n')
    for r in req:
        try:
            print(r.split('=')[0])
            cmd = 'pip install ' + r
            os.system(cmd)
        except Exception as e:
            print("Could not install", r.split('=')[0], ". Please try installing it manually using `pip install "+ r.split('=')[0] + "`")
            print("ERROR:", e)
            missing+packages.append(r.split('=')[0])

if len(missing_packages) != 0:
    print("Please manually install the missing packages:")
    for i in missing_packages:
        print(i)
