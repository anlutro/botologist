class StreamCache:
    def __init__(self):
        self.initiated = False
        self.new_cache = []
        self.old_cache = []

    def push(self, streams):
        assert isinstance(streams, list)
        self.old_cache = self.new_cache
        self.new_cache = streams
        if not self.initiated:
            self.initiated = True

    def get_all(self):
        return set(self.new_cache + self.old_cache)

    def __contains__(self, stream):
        return stream in self.new_cache or stream in self.old_cache
