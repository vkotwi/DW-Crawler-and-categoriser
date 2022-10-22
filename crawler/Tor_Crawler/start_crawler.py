import ctypes, sys, os
import win32con
import win32com.shell.shell as shell
from win32com.shell import shellcon
import time

def run():
    path = os.path.join(os.path.dirname(__file__), 'run_crawler.py')
    path = '"' + path + '"' 

    ASADMIN = 'asadmin'
    if sys.argv[-1] != ASADMIN:
        try:
            procInfo = shell.ShellExecuteEx(
                nShow=win32con.SW_SHOWNORMAL,
                lpVerb='runas',
                lpFile='py',
                lpParameters=path
            )
        except Exception as e:
            while True:
                print("Administrator permissions are required to run this program in order to reset th Tor service.")
                print("Please press enter to retry granting administrator privileges or type `quit` without the ` symbols to exit")
                i = input(">>> ")
                if i == "quit":
                    sys.exit(0)
        else:
            print("ran")
            
        
if __name__ == "__main__":
    run()
