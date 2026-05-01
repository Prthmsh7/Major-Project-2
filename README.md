# Major-Project-2
Mentor - Mr. Pawan Mishra
Name
1. Prathmesh Shukla 221B275
2. Manas Singh 221B226
3. Priyanshu Jain 221B282

# Problem Statement
A CLI tool that compiles C++ code with coverage, runs tests, identifies uncovered statements, asks an LLM to generate inputs, and iteratively improves statement coverage.

## Prerequisites
- Python 3.10+
- GCC toolchain (`g++`, `gcov`) available in PATH
- A valid Gemini key in `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)

## Setup
```bash
python -m venv .venv
```

Linux/macOS:
```bash
source .venv/bin/activate
export GOOGLE_API_KEY='gemini-api-key'
```

Windows PowerShell:
```powershell
.venv\Scripts\activate
$env:GOOGLE_API_KEY='gemini-api-key'
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Run
```bash
python -m cli.main --source samples/math_ops.cpp --max-iters 5
python -m cli.main --source samples/advanced_logic.cpp --max-iters 3
python -m cli.main --source samples/complex.cpp --max-iters 1
```

# Line coverage with 80% threshold
python -m cli.main --source samples/math_ops.cpp --coverage-threshold 80.0

# Branch coverage
python -m cli.main --source samples/math_ops.cpp --coverage-type branch

# Function coverage with 50% threshold
python -m cli.main --source samples/math_ops.cpp --coverage-type function --coverage-threshold 50.0

# Architecture
The optimization loop is orchestrated with LangGraph (`core/loop.py`). The graph executes:
1) generate current test file,
2) compile,
3) run tests,
4) parse coverage,
5) stop or ask the LLM for another test,
6) advance iteration and repeat.

## Notes
- On Windows, the runner automatically resolves `.exe` binaries produced by `g++`.