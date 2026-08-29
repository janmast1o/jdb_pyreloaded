import threading
import time
import random

from typing import List, Tuple


class ConcurrentPrintersRunner:
    def __init__(self, number_of_printers: int, 
                 printing_frequency_range: Tuple[int, int],
                 start_immdiately: bool = False):
        self.printer_messages: List[str] = []
        self._number_of_printers: int = number_of_printers
        self._printing_frequency_range: Tuple[int, int] = printing_frequency_range
        self._printer_threads: List[threading.Thread] = []
        self._keep_printers_active: bool = False
        if start_immdiately:
            self.start()

    def _printer_function(self, printer_index: int) -> None:
        while self._keep_printers_active:
            time.sleep(random.randint(*self._printing_frequency_range))
            print(f"Printer {printer_index}: {self.printer_messages[printer_index]}")

    def start(self) -> None:
        if len(self._printer_threads) != 0:
            raise Exception("Cocurrent printers runner already activated")
        self._keep_printers_active = True
        for i in range(self._number_of_printers):
            self.printer_messages.append(f"Printer says 'Hello!'")
            self._printer_threads.append(threading.Thread(target=lambda _pi=i: self._printer_function(printer_index=_pi)))

        for thread in self._printer_threads:
            thread.start()

    def shutdown(self) -> None:
        if len(self._printer_threads) == 0:
            raise Exception("Concurrent printers already stopped")
        self._keep_printers_active = False
        for thread in self._printer_threads:
            thread.join()


