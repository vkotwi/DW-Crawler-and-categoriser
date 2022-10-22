import subprocess
import win32serviceutil
import psutil, os
import time
import win32con
from win32com.shell.shell import ShellExecuteEx
from win32com.shell import shellcon


found = False

# Checks to see if python proxy is already running
for p in psutil.process_iter():
    if "pproxy.exe" == p.name():
        found = True

# Kills the pproxy proxy completely
def kill_tree(pid):
    p = psutil.Process(pid)
    c = p.children(recursive=True)
    for child in c:
        child.kill()
    _, _ = psutil.wait_procs(c)
    try:
        p.kill()
        p.wait(5)
    except:
        pass

if not found:
    # Starts Proxy
    try:
        p = subprocess.Popen('pproxy -l http://:8181 -r socks5://127.0.0.1:9050 -vv')
        process_id = p.pid
        kill_tree(process_id) # Kills the proxy
    except Exception as e:
        print("An error occurred while trying to start the proxy:", e)
    else:
        print("Proxy started, listening on port 8181")
else:
     print("Proxy already listening on port 8181")

time.sleep(2)

# Checks to see if Tor is already installed as a service, if not attempts to install it
try: 
    win32serviceutil.QueryServiceStatus('tor')
except:
    try:
        # Runs as admin
        ShellExecuteEx(nShow=win32con.SW_HIDE,
                       fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                       lpVerb='runas',
                       lpFile='..\\..\\tor-win32-0.4.4.6\\Tor\\tor.exe',
                       lpParameters='--service install')
    except Exception as e:
        print("The Tor service must be installed in order to use this program.")
        print("ERROR:", e)
        i = input("Please press the Enter key to exit the program...")
        sys.exit()
    else:
        print("Tor service started successfully")
else:
    print("Tor service already installed")

if win32serviceutil.QueryServiceStatus('tor')[1] == 4:
    print("Tor service already running")
else:
    # Starts Tor
    try:
        ShellExecuteEx(nShow=win32con.SW_HIDE,
                       fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                       lpVerb='runas',
                       lpFile='net',
                       lpParameters='start tor')

    except Exception as e:
        print("The Tor service was unable to start. The Tor service must be running in order to use this program.")
        print("ERROR:", e)
        i = input("Please press the Enter key to exit the program...")
        sys.exit()
    else:
        print("Tor service started successfully")

try:
    win32serviceutil.QueryServiceStatus('MongoDB')
except:
    try:
        ShellExecuteEx(nShow=win32con.SW_HIDE,
                       fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                       lpVerb='runas',
                       lpFile='net',
                       lpParameters='start MongoDB')
    except Exception as e:
        print("MongoDB service must be running in order to use this program.")
        print("ERROR:", e)
        i = input("Please press the Enter key to exit the program...")
        sys.exit()
    else:
        print("MongoDB service started successfully")

print("")
print("Prechecks complete")
