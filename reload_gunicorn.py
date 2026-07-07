import os
import signal
import subprocess
# Find parent gunicorn process (master) only
for pid_dir in os.listdir('/proc'):
    if pid_dir.isdigit():
        try:
            with open(f'/proc/{pid_dir}/cmdline', 'rb') as f:
                cmd = f.read().decode('utf-8', errors='ignore').replace('\x00', ' ')
                if 'gunicorn' in cmd and 'master' in cmd:
                    pid = int(pid_dir)
                    print(f"Sending SIGHUP to gunicorn master PID {pid}")
                    os.kill(pid, signal.SIGHUP)
                    break
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
