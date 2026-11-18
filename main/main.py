import socket
import argparse
from IPy import IP



for port in range(1, 65535):
    sock = socket.socket()
    sock.settimeout(0.5)
    try:
        sock.connect(("127.0.0.1", port))
        print(f"Port {port} is open")
    except:
        pass

parser = argparse.ArgumentParser(
    prog = "portScanner"
)