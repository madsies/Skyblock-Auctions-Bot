import apiCollector
import threading
import time

class syncManager():
    def __init__(self):
        self.tick = 0
        self.threads = {}
        self.looper = False

    def addThread(self, name, thread):
        if type(thread) == threading.Thread:
            self.threads[name] = thread
            return f"Thread {name} added"
        else:
            return "Invalid Thread"

    def startThread(self, name):
        self.threads[name].start()
    
    def disableThread(self, name):
        self.threads[name].stop()

    def removeThread(self, name):
        try:
            del self.threads[name]
            return f"Thread {name} deleted"
        except:
            return "That thread doesnt exist!"

    def ticker(self, looper):
        self.tick = 0
        self.looper = looper
        while self.looper:
            time.sleep(0.1) # 10tps
            if (self.tick % 3600 == 0):  # every 5mins
                self.addThread("api", threading.Thread(target=apiCollector.updateListings, args=(self, ), daemon=True))
                self.startThread("api")
            elif (self.tick % 600 == 0):
                print(f"Current threads:{self.threads}")

            self.tick +=1

    def tickTracker(self):
        print(f"Tick: {self.tick}")

    def killLoop(self):
        self.looper = False

def main():
    manager = syncManager()
    mainThread = threading.Thread(target=manager.ticker, args=(True,))
    manager.addThread("main", mainThread)
    manager.startThread("main")


if __name__ == "__main__":
    main()