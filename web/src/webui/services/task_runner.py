import os
from typing import Dict, Any, Tuple

from core.loop import CoverageOptimizer
from core.types import CoverageType


def run_coverage_job(source_file: str, config: Dict[str, Any]) -> Tuple[Any, Any, Dict[str, Any]]:
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
    }

    if os.path.exists(optimizer.test_file_path):
        with open(optimizer.test_file_path, "r", encoding="utf-8") as f:
            result_data["test_file_content"] = f.read()

    return final_coverage, generated_tests, result_data
