import time
import threading
import concurrent.futures 
start = time.perf_counter()
"""
def loop1():
    for i in range(0,10):
        print("from file 1")

threads = []
for _ in range(10):
    t = threading.Thread(target=dosome , args=[1.5])
    t.start()
    threads.append(t)

for thread in threads:
    thread.join()
"""
       

def dosome(sec):
    print(f"sleeping now for {sec} seconds")
    time.sleep(sec)
    return "done sleeping"

with concurrent.futures.ThreadPoolExecutor() as executor:
    res = []
    secs = [2,4,2,5,1]
    for i in range(5):
        futureObj = executor.submit(dosome , secs[i])
        res.append(futureObj)
    
    
    for f in concurrent.futures.as_completed(res):
        print(f.result())
        


fin = time.perf_counter()

print(f'it took {round(fin-start,2) } sec to complete the dosome function')