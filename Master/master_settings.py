from master_utils import validate_input_file_path, validate_input_port

DEFAULT_MASTER_PORT = 5000
BATCH_SIZE = 100000
RANGE_START = 500000000
RANGE_END = 600000000
MAX_POOL_SIZE = 100
TIMEOUT = 30

class master_settings:
    def __init__(self, file_path, master_port):
        self.file_path = file_path
        self.master_port = master_port


def build_minion_settings(argv):
    file_path = argv[1] if len(argv) > 1 else None
    master_port = argv[2] if len(argv) > 2 else None

    validate_input_file_path(file_path)
    master_port = DEFAULT_MASTER_PORT if not master_port else validate_input_port(master_port)
    return master_settings(file_path, master_port)