import time


def wait_until(predicate, timeout=1.0, interval=0.01):
    deadline = time.time() + timeout

    while time.time() < deadline:
        if predicate():
            return

        time.sleep(interval)

    raise AssertionError("Condition was not met before timeout")
