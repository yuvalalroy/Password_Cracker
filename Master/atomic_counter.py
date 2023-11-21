import multiprocessing

class atomic_counter:
    def __init__(self, initial=0):
        self.value = multiprocessing.Value('i', initial)
        self.lock = multiprocessing.Lock()

    def increment(self):
        with self.lock:
            self.value.value += 1

    def decrement(self):
        with self.lock:
            self.value.value -= 1

    def get_value(self):
        with self.lock:
            return self.value.value