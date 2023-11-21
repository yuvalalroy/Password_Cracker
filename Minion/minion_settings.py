BASE_URL = 'http://127.0.0.1:'
DEFAULT_MASTER_PORT = 5000

class minion_settings():
    def __init__(self, minion_port, master_port, minion_url, master_url):
        self.minion_port = minion_port
        self.master_port = master_port
        self.minion_url = minion_url
        self.master_url = master_url


def build_minion_settings(argv):
    minion_str_port = argv[1] if len(argv) > 1 else None
    master_str_port = argv[2] if len(argv) > 2 else None

    if minion_str_port is None:
        raise ValueError("Please provide a port as a command-line argument.")

    master_port = DEFAULT_MASTER_PORT if not master_str_port else master_str_port

    try:
        minion_port = int(minion_str_port)
        master_port = int(master_port)
    except (ValueError, TypeError):
        raise ValueError('Error: Invalid port number.')

    if minion_port == master_port:
        raise ValueError("Minion port cannot be the same as the master port.")
    
    minion_url = BASE_URL + str(minion_port)
    master_url = BASE_URL + str(master_port)

    return minion_settings(minion_port, master_port, minion_url, master_url)
