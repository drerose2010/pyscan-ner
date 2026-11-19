from ast import arg
import socket
import argparse
from IPy import IP
from argParser import argParse, parse_ports
import threading
import time

args = argParse("-ip 8.8.8.8")
portList = parse_ports(args.ports)
print(args.ports)

def scan_port(port):
    sock = socket.socket()
    sock.settimeout(0.5)
    try:
        sock.connect((args.ip, int(port)))
        print(f"Port {port} is open")
    except:
        pass

start_time = time.time()

print(time.time())
for port in portList:
    #threading.Thread(target=scan_port, args=(port,)).start()
    pass

print("--- %s seconds ---" % (time.time() - start_time))