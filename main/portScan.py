import errno
import socket
from enum import Enum


class PortState(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    ERROR = "error"

def scan_port(ip: str,port: int, timeout: float) -> tuple[int, PortState, str]:

    with socket.socket() as sock: # Opens a socket and automatically closes it when done
        sock.settimeout(timeout)

        try:
            sock.connect((ip, port))
            return port, PortState.OPEN, "Connection successful" 
        except ConnectionRefusedError:
            return port, PortState.CLOSED, "Connection refused"
        except TimeoutError as e:
            return port, PortState.FILTERED, str(e)
        except OSError as e:
            if e.errno in (errno.EHOSTUNREACH, errno.ENETUNREACH, errno.EPERM):
                return port, PortState.FILTERED, str(e)
            else:
                return port, PortState.ERROR, str(e)