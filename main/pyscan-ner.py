from pprint import pprint
import sys

from main.argParser import parse_ports, argParse
from main.portScan import scan_port
from collections import Counter
from main.portScan import PortState


def main(argv=None) -> None:
    # 1. Get the arguments
    # argParse currently takes a string, so join sys.argv (without the script name)
    args = argParse(argv)

    # 2. Validate the target
    # args.ip is None when -ip is omitted, so print a usage error and exit
    if args.ip is None:
        print("Error: -ip argument is required")
        sys.exit(1)

    # 3. Convert the port spec
    # parse_ports raises ValueError on bad input, so catch it, print the
    # message, and exit with a non-zero code
    try:
        ports = parse_ports(args.ports)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 4. Scan (sequential for now)
    results = []  
    try:
        for port in ports:
            result = scan_port(args.ip, port, args.timeout)
            #print(result)
            results.append((port, result))
    except Exception as e:
        print(f"Error scanning ports: {e}")
        sys.exit(1)

    print(results)
    # 5. Report
    # open ports: loop over results, print only the OPEN ones
    for port, (port, state, message) in results:
        if state == PortState.OPEN:
            print(f" # Port {port}: Open")
    
    # summary: Counter of states, e.g. "993 closed, 28 filtered"
    resultList = []
    for portScanResult in results:
        resultList.append(portScanResult[1][1])

    counts = Counter(resultList)
    summary = [f"{n} {state.value}" for state, n in counts.items()]
    for stateTotal in summary:
        print(f"State Summary: {stateTotal}")

if __name__ == "__main__":
    main()