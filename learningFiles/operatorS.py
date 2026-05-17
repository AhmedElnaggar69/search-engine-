import threading
from parallelStuff1 import loop1

from parallelStuff2 import loop2

thread1 = threading.Thread(target=loop1)
thread2 = threading.Thread(target=loop2)
thread1.start()
thread2.start()

thread1.join()
thread2.join()
