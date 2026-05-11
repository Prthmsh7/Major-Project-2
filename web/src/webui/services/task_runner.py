import os
import re
import subprocess
from typing import Dict, Any, Tuple

from core.loop import CoverageOptimizer
from core.types import CoverageType


def _explain_compile_error(source_file: str) -> str:
    cmd = ["g++", "-fsyntax-only", source_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return ""

    stderr = (result.stderr or "").strip()
    first_line = stderr.splitlines()[0] if stderr else "Compilation failed."

    hint = "Check syntax near the first reported line."
    lower = stderr.lower()
    if "expected" in lower and "before" in lower:
        hint = "Likely missing punctuation (semicolon, brace, or parenthesis) before the reported token."
    elif "was not declared in this scope" in lower:
        hint = "A variable/function is used before declaration or misspelled."
    elif "no matching function for call to" in lower:
        hint = "Function call arguments do not match any available overload."
    elif "undefined reference to" in lower:
        hint = "A declared symbol is missing a definition during linking."

    line_no = None
    m = re.search(r":(\d+):(\d+):\s+error:", stderr)
    if m:
        line_no = m.group(1)

    parts = [
        "Your C++ code does not compile.",
        f"Compiler summary: {first_line}",
        f"Hint: {hint}",
    ]
    if line_no:
        parts.append(f"Start by checking line {line_no} in your source.")
    return "\n".join(parts)


def run_coverage_job(source_file: str, config: Dict[str, Any]) -> Tuple[Any, Any, Dict[str, Any]]:
    compile_explanation = _explain_compile_error(source_file)
    if compile_explanation:
        raise ValueError(compile_explanation)

    coverage_type = CoverageType(config.get("coverage_type", "line"))
    max_iters = int(config.get("max_iters", 5))
    coverage_threshold = float(config.get("coverage_threshold", 100.0))
    model = config.get("model", "gemini-2.5-flash")
    focus_mode = config.get("focus_mode", "coverage")

    optimizer = CoverageOptimizer(
        source_file=source_file,
        max_iters=max_iters,
        model=model,
        coverage_type=coverage_type,
        coverage_threshold=coverage_threshold,
        focus_mode=focus_mode,
    )

    final_coverage, generated_tests = optimizer.run_optimization_loop()

    result_data = {
        "final_coverage": final_coverage.overall_percentage,
        "coverage_type": coverage_type.value,
        "threshold": coverage_threshold,
        "total_tests": len(generated_tests),
        "test_file_path": optimizer.test_file_path,
        "coverage_history": [],
        "uncovered_lines": final_coverage.uncovered_lines,
        "uncovered_branches": final_coverage.uncovered_branches,
        "uncovered_functions": final_coverage.uncovered_functions,
        "test_generation_reasons": optimizer.test_generation_reasons,
    }

    if os.path.exists(optimizer.test_file_path):
        with open(optimizer.test_file_path, "r", encoding="utf-8") as f:
            result_data["test_file_content"] = f.read()

    return final_coverage, generated_tests, result_data
