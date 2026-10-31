import asyncio
import time

from abc import ABC as AbstractClass
from enum import StrEnum
from types import CoroutineType
from typing import Callable, List, Type


class PerformanceTestOutcomeType(StrEnum):
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    TIMEOUT = "TIMEOUT"


class TimespanRecorder:
    def __init__(self):
        self.start: float = None
        self.end: float = None

    def record_start(self) -> None:
        self.start = time.time()        

    def record_end(self) -> None:
        self.end = time.time()

    def get_diff(self) -> float:
        return self.end - self.start    


def ignore_performace_test(f: Callable):
    def inner_print_ignore_message(*args, **kwargs) -> PerformanceTestOutcomeType:
        print(f"Test case {f.__name__}")
        return PerformanceTestOutcomeType.SKIPPED
    return inner_print_ignore_message


# Negative values passed as `test_timeout_ms` indicate no timeout
class PerformanceTestFramework(AbstractClass):
    def __init__(self, test_timeout_ms: int = 20_000):
        # Expressed in seconds
        self._test_timeout_s: float = test_timeout_ms / 1000
        if self._test_timeout_s < 0:
            print("Will not use timeout for tests")

    def before_class(self) -> None:
        pass

    def after_class(self) -> None:
        pass 

    def before_test(self) -> None:
        pass

    def after_test(self) -> None:
        pass

    def create_async_coroutine_wrapper_for_test_method(self, test_method: Callable, timespan_recorder: TimespanRecorder) -> CoroutineType:
        async def internal_coroutine_for_test_method(*args, **kwargs):
            timespan_recorder.record_start()
            test_method(*args, **kwargs)
            timespan_recorder.record_end()

        return internal_coroutine_for_test_method

    async def async_run_all_tests(self) -> None:
        all_tests_method_names = [t for t in dir(self) if (t.startswith("test_") and callable(getattr(self, t)))]
        all_test_methods: List[Callable] = [getattr(self, t) for t in all_tests_method_names]
        n = len(all_tests_method_names)

        for i in range(n):
            test_method_name = all_tests_method_names[i]
            test_method = all_test_methods[i]
            print(f"Running test: {test_method_name}...")
            timespan_recorder = TimespanRecorder()
            # Create a task and automatically start it
            async_task = asyncio.create_task(self.create_async_coroutine_wrapper_for_test_method(test_method, timespan_recorder)())

            if self._test_timeout_s < 0:
                res = await async_task
                if res == PerformanceTestOutcomeType.SKIPPED:
                    print(f"Skipped")
                else:
                    execution_time = timespan_recorder.get_diff()
                    outcome = PerformanceTestOutcomeType.SUCCESSFUL if async_task.exception() is None else PerformanceTestOutcomeType.FAILED
                    print(f"Executed in: {execution_time%.3}s, result={outcome}")
            else:
                time_quant = 1e-2
                cumulative_sleep_time = 0
                while True:
                    if async_task.done():
                        break
                    cumulative_sleep_time += time_quant
                    await asyncio.sleep(time_quant)
                
                if not async_task.done():
                    async_task.cancel()
                    print(f"Test timed out")
                else:
                    res = async_task.result()
                    execution_time = timespan_recorder.get_diff()
                    outcome = PerformanceTestOutcomeType.SUCCESSFUL if async_task.exception() is None else PerformanceTestOutcomeType.FAILED
                    print(f"Executed in: {execution_time%.3}s, result={outcome}")

            # Extra empty line
            print("\n", end="")

    def run_all_tests(self):
        asyncio.run(self.async_run_all_tests())        


# Don't know how to annotate the type here.
def run_performace_tests_for_class(performance_test_type, *args, **kwargs) -> None:
    performance_test_suite: PerformanceTestFramework = performance_test_type(*args, **kwargs)
    performance_test_suite.run_all_tests()