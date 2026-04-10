# Major-Project-2
Mentor - Mr. Pawan Mishra
Name
1. Prathmesh Shukla 221B275
2. Manas Singh 221B226
3. Priyanshu Jain 221B282

# Problem Statement
A CLI tool that compiles C++ code with coverage, runs tests, identifies uncovered statements, asks an LLM to generate inputs, and iteratively improves statement coverage.

source venv/bin/activate
export GOOGLE_API_KEY='gemini-api-key'

python -m cli.main --source samples/math_ops.cpp --max-iters 5
python -m cli.main --source samples/advanced_logic.cpp --max-iters 3
python -m cli.main --source samples/complex.cpp --max-iters 1

# Line coverage with 80% threshold
python -m cli.main --source samples/math_ops.cpp --coverage-threshold 80.0

# Branch coverage
python -m cli.main --source samples/math_ops.cpp --coverage-type branch

# Function coverage with 50% threshold
python -m cli.main --source samples/math_ops.cpp --coverage-type function --coverage-threshold 50.0