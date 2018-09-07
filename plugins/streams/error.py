import functools


class StreamException(RuntimeError):
    pass


class StreamNotFoundException(StreamException):
    def __init__(self, message=None):
        super().__init__(message or "Error: Stream not found")


class InvalidStreamException(StreamException):
    def __init__(self, message=None):
        super().__init__(message or "Error: Invalid stream URL")


class AmbiguousStreamException(StreamException):
    def __init__(self, streams):
        msg = "Ambiguous stream choice - "
        if len(streams) > 5:
            msg += str(len(streams)) + " options"
        else:
            msg += "options: " + ", ".join(streams)
        super().__init__(msg)
        self.streams = streams


class AlreadySubscribedException(StreamException):
    def __init__(self, stream):
        super().__init__("Already subscribed to stream: " + stream)
        self.stream = stream


def return_streamerror_message(func):
    """Decorator that automatically catches stream exceptions and returns the
	exception's string representation."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except StreamException as e:
            return str(e)

    return wrapper
