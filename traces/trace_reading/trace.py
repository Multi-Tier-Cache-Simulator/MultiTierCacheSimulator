_DEBUG = False


class Trace:
    # Column names extracted from recorder_viz, kept here as static members vars
    _COLUMN_NAMES = ("data_back", "timestamp", "name", "size", "priority", "InterestLifetime", "responseTime")

    def __init__(self):
        self.data = []

    def gen_data(self, trace_len_limit=-1):
        raise NotImplementedError("Using unspecialized trace class.")

    def read_data_line(self, env, name_lock, res, forwarder, line, log_file, logs_enabled=True):
        raise NotImplementedError("Using unspecialized trace class.")

    @property
    def column_names(self):
        return self._COLUMN_NAMES
