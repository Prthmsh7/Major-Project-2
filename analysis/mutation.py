import os
from dataclasses import dataclass
from typing import List, Tuple

from executor.compiler import compile_cpp
from executor.runner import run_test


@dataclass
class MutationResult:
    mutation_score: float
    killed: int
    total: int


def _apply_mutation(text: str, start: int, old: str, new: str) -> str:
    return text[:start] + new + text[start + len(old):]


def _candidate_mutations(source: str, max_mutants: int) -> List[Tuple[int, str, str]]:
    # Keep this intentionally simple and deterministic for fast scoring.
    # Includes arithmetic and logical flips used in mutation testing demos.
    pairs = [
        ("==", "!="),
        ("!=", "=="),
        (">=", ">"),
        ("<=", "<"),
        (">", ">="),
        ("<", "<="),
        ("+", "-"),
        ("-", "+"),
        ("&&", "||"),
        ("||", "&&"),
    ]
    out: List[Tuple[int, str, str]] = []
    for old, new in pairs:
        idx = 0
        while idx < len(source):
            pos = source.find(old, idx)
            if pos == -1:
                break
            out.append((pos, old, new))
            idx = pos + len(old)
            if len(out) >= max_mutants:
                return out
    return out


def compute_mutation_score(source_file: str, test_file: str, cwd: str, max_mutants: int = 20) -> MutationResult:
    with open(source_file, "r", encoding="utf-8") as f:
        original = f.read()

    mutants = _candidate_mutations(original, max_mutants=max_mutants)
    if not mutants:
        return MutationResult(mutation_score=0.0, killed=0, total=0)

    killed = 0
    for pos, old, new in mutants:
        mutated = _apply_mutation(original, pos, old, new)
        with open(source_file, "w", encoding="utf-8") as f:
            f.write(mutated)

        if not compile_cpp([os.path.basename(test_file)], "a.out", cwd=cwd):
            killed += 1
            continue

        result = run_test("./a.out", cwd=cwd)
        if not result.success:
            killed += 1

    with open(source_file, "w", encoding="utf-8") as f:
        f.write(original)

    total = len(mutants)
    score = (killed / total) * 100.0 if total else 0.0
    return MutationResult(mutation_score=score, killed=killed, total=total)
