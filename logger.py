from threading import Thread, Lock

from datetime import datetime

import time

class Logger:
    def __init__(self, filename: str):
        self.filename = filename + ".log" if filename.endswith(".log") else filename
        self.buffer = []
        self.__buffer_to_save = []
        self.locker = Lock()
        self.is_open = True
        self.thead = Thread(target=self.__threadProc)
        self.thead.start()

    def __del__(self):
        self.close()

    def close(self):
        if self.is_open:
            self.is_open = False
            self.thead.join()
            self.flush()

    def log(self, type_log: str, value: str):
        """
        Парсит строку на основе type_log и value и добавляет её в очередь
        """
        curr_time = datetime.now()
        curr_time_str = curr_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        log_str = f"[{curr_time_str}: {type_log.upper()}]: {value}"

        with self.locker:
            if len(self.buffer) < 1000:
                self.buffer.append(log_str)

    def __threadProc(self):
        while self.is_open:
            try:
                self.flush()
            except:
                pass
            time.sleep(1)

    def flush(self):
        with self.locker:
            self.buffer, self.__buffer_to_save = self.__buffer_to_save, self.buffer

        if len(self.__buffer_to_save):
            with open(self.filename, "r") as file:
            	log_file = file.readlines()
            if len(log_file) > 50_000:
            	log_file = log_file[10_000:]
            	for i in self.__buffer_to_save:
            		log_file.append(str(i) + "\n")
            	log_file_str = ""
            	for i in log_file:
            		log_file_str += i + "\n"
            	with open(self.filename, "w") as file:
            		file.write(log_file_str)
            	
            with open(self.filename, "a") as file:
                for i in self.__buffer_to_save:
                    file.write(str(i) + "\n")
            self.__buffer_to_save.clear()