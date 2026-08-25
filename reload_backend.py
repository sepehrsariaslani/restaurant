import os
import signal
# Send HUP to PID 1 (main process in container) to trigger graceful reload
os.kill(1, signal.SIGHUP)
print("SIGHUP sent to PID 1")
