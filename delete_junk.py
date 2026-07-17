import os
import glob

# delete old test scripts left by error
files_to_delete = glob.glob("*.py")
exclude = ["delete_junk.py"]
for f in files_to_delete:
    if f not in exclude:
        os.remove(f)
print("Deleted junk scripts")
