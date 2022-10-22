from pymongo import MongoClient
import ctypes, psutil, os, sys

import win32con
import win32com.shell.shell as shell
from win32com.shell import shellcon

import subprocess
import time

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
    return

def check_service(s): 
 
        service = None 
        try: 
            service = psutil.win_service_get(s) 
            service = service.as_dict() 
        except: 
            pass 
 
        return service 

def crawl():
    dict_path = os.path.dirname(__file__).replace('\\', '/')#[:-1]
    path = os.path.join(dict_path, 'run_crawler.py')
    #dict_path = '"' + dict_path + '"' 
    path = '"' + path + '"'

    # Hides console
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    while True:
        try:
            a = subprocess.run(["net", "start", "tor"])
            pass
        except:
            print("Failed to start Tor process.")
        else:
            break

    count = 2
    while True:
        # TODO: Clear console
        subprocess.call('cls', shell=True)
        if count == 2:
            while True:
                try:
                    print("Trying to stop the Tor process again")
                    i = subprocess.check_output(["net", "stop", "tor"])
                except subprocess.CalledProcessError as e:
                    print(e)
                    print("Error stopping Tor")
                else:
                    break
                
            while True:
                try:
                    print("Trying to start the Tor process again")
                    i = subprocess.check_output(["net", "start", "tor"])
                    print(i)
                except subprocess.CalledProcessError as e:
                    print(e)
                    print("Error starting Tor")
                else:
                    break
            count = 0

        visisted_sites = db.find({'visited': True}).count()

        db_urls = db.find({}).count()
        urlsCheck = list(db.find({'visited': False}, {'url': 1}).limit(1))
        upCheck = list(db.find({'visited': True}, {'status': 1}))

        check = 0
        for i in upCheck:
            if i["status"] == 200:
                check += 1
        
        print(visisted_sites, " web pages processed")
        print(str(check) + "/" + str(visisted_sites) + " web pages up")
        print(db_urls, " urls in database")
        
        if len(urlsCheck) == 0:
            print("End of database reached")
            break
        
        #pproxy -l http://:8181 -r socks5://127.0.0.1:9050 -vv
        p = subprocess.Popen('pproxy -l http://:8181 -r socks5://127.0.0.1:9050 -vv', shell=True, startupinfo=si)
        time.sleep(2)
        #..\..\polipo-1.1.0-win32\polipo -c ..\..\polipo-1.1.0-win32\config.sample
        #p = subprocess.Popen('..\..\polipo-1.1.0-win32\polipo -c ..\..\polipo-1.1.0-win32\config.sample')#, startupinfo=si)
        # yield p
        subprocess.run("scrapy crawl tc", shell=True, cwd=dict_path, startupinfo=si) # scrapy crawl tc

        process_id = p.pid
        kill_tree(process_id)
        
        p.terminate()
        p.kill()
        p.wait() # waits for process to finish terminating


        unlabelled_sites = db.find({'labels': {'$exists': False}, 'status': 200}).count()

        # If more than 200 unlabelled entries, labels them.
        if unlabelled_sites > 200:
            subprocess.run("py categoriser/categoriser.py", shell=True, cwd=dict_path, startupinfo=si) # blocking
            
        print("Cancel process now...")
        #i = input(">>>")
        print("3...")
        time.sleep(1)
        print("2...")
        time.sleep(1)
        print("1...")
        time.sleep(1)
        print("")
        
        count += 1
        
    client.close()

if __name__ == '__main__':
    print("Loading...")
    client = MongoClient('mongodb://localhost:27017/')
    db = client["DWProject"]["DW_URLs"]
    crawl()
    print("Done")
