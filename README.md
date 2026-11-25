# pyscan-ner
 
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![socket](https://img.shields.io/badge/stdlib-socket-blue)
![IPy](https://img.shields.io/badge/IPy-1.2-green)
![pytest](https://img.shields.io/badge/tested_with-pytest-0A9EDC?logo=pytest&logoColor=white)
![CI](https://github.com/<your-username>/pyscan-ner/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/status-work_in_progress-orange)

A small TCP port scanner written in Python, built to learn how Nmap works. It uses the standard library's `socket` module and parses its own command-line arguments.
 
> Work in progress. Learning project, not a replacement for Nmap.

> <b>AI Disclamer:</b> Claude was used to assist with planning, guidance and code review. For this project I avoided any generated code (outside of commends) as it would defeat the purpose of learning nmap and python networking
 
## Current features
 
- Command-line arguments for target, ports, and timeout
- Port spec parsing: single ports, lists, and ranges (`80`, `22,80,443`, `1-1024`, `22,80,100-103`)
- TCP connect scan that reports each port as `open`, `closed`, `filtered`, or `error`
- Unit tests with pytest

## Requirements
 
- Python 3.11+
- [IPy](https://pypi.org/project/IPy/)
- pytest (for the tests)
## Setup
 
```bash
git clone https://github.com/<your-username>/pyscan-ner.git
cd pyscan-ner
python3 -m venv .venv
source .venv/bin/activate
pip install IPy pytest
```
 
## Project structure
 
```
pyscan-ner/
├── main/
│   ├── argParser.py     # command-line arguments and port spec parsing
│   ├── portScan.py      # TCP connect scan and port states
│   └── pyscan-ner.py    # entry point
├── tests/
│   └── test_ports.py    # pytest suite
├── pytest.ini           # pytest configuration
├── .github/
│   └── workflows/
│       └── ci.yml       # CI Automation
└── README.md
```
 
## Usage
 
Run from the project root:
 
```bash
python -m main.pyscan-ner -ip 127.0.0.1 -p 1-1024
```
 
| Option | Description | Default |
|---|---|---|
| `-ip` | IP address, CIDR range, or hostname to scan | none |
| `-p`, `--ports` | Ports to scan, e.g. `80`, `22,80,443`, `1-1024` | `1-1024` |
| `--timeout` | Per-connection timeout in seconds | `1.0` |
 
## Port states
 
| State | Meaning |
|---|---|
| open | The connection succeeded |
| closed | The host refused the connection |
| filtered | No response, or the network blocked it |
| error | Some other OS error |
 
## Tests
 
```bash
pytest -v
```
 
## Roadmap
 
- [ ] Threaded scanning
- [ ] Banner grabbing and service detection
- [ ] Host discovery
- [ ] OS detection
- [ ] JSON output
## Legal and ethical use
 
Only scan systems you own or have explicit permission to test. Unauthorised scanning may breach policy or law. `scanme.nmap.org` allows light scanning for practice.
 