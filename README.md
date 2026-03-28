# Major-Project-2
Mentor - Mr. Pawan Mishra
Name
1. Prathmesh Shukla 221B275
2. Manas Singh 221B226
3. Priyanshu Jain 221B282

# Problem Statement
A CLI tool that compiles C++ code with coverage, runs tests, identifies uncovered statements, asks an LLM to generate inputs, and iteratively improves statement coverage.

source venv/bin/activate
export GOOGLE_API_KEY='AIzaSyCc8jaevgJ91cyYeObI9liB8uVUtWtY9Vk'

python -m cli.main --source samples/math_ops.cpp --max-iters 5
python -m cli.main --source samples/advanced_logic.cpp --max-iters 3
python -m cli.main --source samples/complex.cpp --max-iters 1
