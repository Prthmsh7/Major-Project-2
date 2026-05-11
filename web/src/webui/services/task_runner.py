import os
from typing import Any, Dict, Tuple

from core.loop import CoverageOptimizer
from core.types import CoverageType


def run_coverage_job(source_file: str, config: Dict[str, Any]) -> Tuple[Any, Any, Dict[str, Any]]:
    coverage_type = CoverageType(config.get("coverage_type", "line"))
    optimizer = CoverageOptimizer(
        source_file=source_file,
        max_iters=int(config.get("max_iters", 5)),
        model=config.get("model", "gemini-2.5-flash"),
        coverage_type=coverage_type,
        coverage_threshold=float(config.get("coverage_threshold", 100.0)),
        objective=config.get("objective", "coverage"),
        mutation_threshold=float(config.get("mutation_threshold", 70.0)),
    )

    final_coverage, generated_tests = optimizer.run_optimization_loop()

    result = {
        "final_coverage": final_coverage.overall_percentage if final_coverage else 0.0,
        "coverage_type": coverage_type.value,
        "total_tests": len(generated_tests),
        "test_file_path": optimizer.test_file_path,
        "iteration_history": optimizer.iteration_history,
    }

    if os.path.exists(optimizer.test_file_path):
        with open(optimizer.test_file_path, "r", encoding="utf-8") as f:
            result["test_file_content"] = f.read()

    return final_coverage, generated_tests, result
