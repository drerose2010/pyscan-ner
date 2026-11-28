import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from main.argParser import argParse, parse_ports
from main.portScan import PortState, scan_port


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
        with ThreadPoolExecutor(max_workers=args.threads) as pool:
            results = list(pool.map(lambda p: scan_port(args.ip, p, args.timeout), ports))
            
    except Exception as e:  # noqa: BLE001 - top-level handler for the CLI
        print(f"Error scanning ports: {e}")
        sys.exit(1)

    # 5. Report
    # open ports: loop over results, print only the OPEN ones
    for port, state, message in results:
        if state == PortState.OPEN:
            print(f" # Port {port}: Open")

    # summary: Counter of states, e.g. "993 closed, 28 filtered"
    counts = Counter(state for _, state, _ in results)
    for state, n in counts.items():
        print(f"State Summary: {n} {state.value}")

if __name__ == "__main__":
    main()