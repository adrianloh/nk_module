import signal
TIMEOUT=5

class TimeoutFunctionException(Exception):
    """Exception to raise on a timeout"""
    pass 

class TimeoutFunction: 

    def __init__(self, function, timeout):
        self.timeout = timeout
        self.function = function 

    def handle_timeout(self, signum, frame):
        raise TimeoutFunctionException()

    def __call__(self, *args, **kwargs):
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        try:
            result = self.function(*args, **kwargs)
        finally:
            signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result

if __name__ == '__main__':
    import sys
    stdin_read = TimeoutFunction(sys.stdin.readline, TIMEOUT)
    try:
        line = stdin_read()
    except TimeoutFunctionException:
        print 'Too slow!'
    else:
        print 'You made it!'
