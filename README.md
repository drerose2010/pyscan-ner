# pyscan-ner
 
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![socket](https://img.shields.io/badge/stdlib-socket-blue)
![IPy](https://img.shields.io/badge/IPy-1.2-green)
![pytest](https://img.shields.io/badge/tested_with-pytest-0A9EDC?logo=pytest&logoColor=white)
![CI](https://github.com/drerose2010/pyscan-ner/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/status-work_in_progress-orange)
![Version](https://img.shields.io/badge/version-v1.0-blue)
 
A small multi-threaded TCP port scanner written in Python, built to learn how [Nmap](https://nmap.org/) works under the hood. It uses the standard library's `socket` module and parses its own command-line arguments.
 
> Work in progress. Learning project, not a replacement for Nmap.
 
## Features
 
- Command-line arguments for target, ports, timeout, and thread count
- Port spec parsing: single ports, lists, and ranges (`80`, `22,80,443`, `1-1024`, `22,80,100-103`)
- TCP connect scan that reports each port as `open`, `closed`, `filtered`, or `error`
- Threaded scanning with a configurable worker count
- Summary of how many ports are in each state
- pytest suite and GitHub Actions CI on Linux and macOS
## Requirements
 
- Python 3.11+
- [IPy](https://pypi.org/project/IPy/) (for CIDR target handling, in progress)
## Setup
 
```bash
git clone https://github.com/drerose2010/pyscan-ner.git
cd pyscan-ner
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```
 
`requirements.txt` holds the runtime dependencies. `requirements-dev.txt` adds pytest and ruff.
 
## Usage
 
Run from the project root:
 
```bash
python -m main.pyscan_ner -ip 127.0.0.1 -p 1-1024
python -m main.pyscan_ner -ip 127.0.0.1 -p 22,80,443 --timeout 0.5 --threads 100
```
 
| Option | Description | Default |
|---|---|---|
| `-ip` | IP address or hostname to scan (required) | none |
| `-p`, `--ports` | Ports to scan, e.g. `80`, `22,80,443`, `1-1024` | `1-1024` |
| `--timeout` | Per-connection timeout in seconds | `1.0` |
| `--threads` | Number of worker threads (at least 1) | `50` |
 
Each worker holds an open socket, and some systems limit open files per process (macOS is often 256), so very high thread counts can produce `error` results.
 
### Example output
 
Scanning a machine that has a web server on port 80:
 
```
 # Port 80: Open
State Summary: 1023 closed
State Summary: 1 open
```
 
## Port states
 
| State | Meaning |
|---|---|
| open | The connection succeeded |
| closed | The host refused the connection |
| filtered | No response, or the network blocked it |
| error | Some other OS error |
 
A timeout is reported as `filtered`, but it can also mean the host is down or the timeout was too short. Nmap makes the same trade-off.
 
## Project structure
 
```
pyscan-ner/
├── .github/
│   └── workflows/
│       └── ci.yml            # tests on Linux and macOS
├── main/
│   ├── argParser.py          # command-line arguments and port spec parsing
│   ├── portScan.py           # TCP connect scan and port states
│   └── pyscan_ner.py         # entry point
├── tests/
│   ├── conftest.py           # shared socket fixtures
│   ├── test_argparse.py
│   ├── test_main.py
│   ├── test_ports.py
│   ├── test_scan.py
│   └── test_threads.py
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── ruff.toml
└── README.md
```
 
## Tests and linting
 
```bash
pytest -v
ruff check .
```
 
The suite covers argument parsing, port spec parsing, the scan logic, and the threaded entry point. Most tests use a fake scanner so they never touch the network, and a few run real scans against local sockets.
 
## Roadmap
 
- [x] Argument parsing and port spec parser
- [x] TCP connect scan with port states
- [x] Threaded scanning
- [x] Unit tests and CI
- [ ] Target handling (CIDR ranges and hostnames)
- [ ] Live progress display
- [ ] Banner grabbing and service detection
- [ ] Host discovery
- [ ] OS detection
- [ ] JSON output
## Legal and ethical use
 
Only scan systems you own or have explicit permission to test. Unauthorised scanning may breach policy or law. `scanme.nmap.org` allows light scanning for practice.
 
## Acknowledgements
 
Inspired by [Nmap](https://nmap.org/) by Gordon "Fyodor" Lyon.
 