from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class CoverageType(Enum):
    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"

@dataclass
class CoverageData:
    """Contains information parsed from gcov."""
    overall_percentage: float
    # Mapping of line number -> execution count (0 means uncovered)
    line_counts: Dict[int, int]
    # List of line numbers that are executable but were hit 0 times
    uncovered_lines: List[int]
    # Type of coverage measurement
    coverage_type: CoverageType = CoverageType.LINE
    # Branch coverage data (if applicable)
    branch_counts: Dict[str, int] = field(default_factory=dict)
    uncovered_branches: List[str] = field(default_factory=list)
    # Function coverage data (if applicable)
    function_counts: Dict[str, int] = field(default_factory=dict)
    uncovered_functions: List[str] = field(default_factory=list)

    @property
    def is_fully_covered(self) -> bool:
        """Returns True if there are zero uncovered executable lines."""
        if self.coverage_type == CoverageType.LINE:
            return len(self.uncovered_lines) == 0
        elif self.coverage_type == CoverageType.BRANCH:
            return len(self.uncovered_branches) == 0
        elif self.coverage_type == CoverageType.FUNCTION:
            return len(self.uncovered_functions) == 0
        return False
    
    def meets_threshold(self, threshold: float) -> bool:
        """Returns True if coverage meets or exceeds the threshold."""
        return self.overall_percentage >= threshold

@dataclass
class ExecutionResult:
    """Result of running a compiled C++ binary."""
    exit_code: int
    stdout: str
    stderr: str
    success: bool

@dataclass
class TestCase:
    """A generated C++ test case from the LLM."""
    code: str
    target_uncovered_lines: List[int] = field(default_factory=list)
