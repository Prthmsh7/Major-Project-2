from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class CoverageData:
    """Contains information parsed from gcov."""
    overall_percentage: float
    # Mapping of line number -> execution count (0 means uncovered)
    line_counts: Dict[int, int]
    # List of line numbers that are executable but were hit 0 times
    uncovered_lines: List[int]

    @property
    def is_fully_covered(self) -> bool:
        """Returns True if there are zero uncovered executable lines."""
        return len(self.uncovered_lines) == 0

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
