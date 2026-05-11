import os
import shutil
import tempfile
import time
import hashlib
import re
import subprocess
from typing import List, Tuple, Optional, TypedDict
from executor.compiler import compile_cpp
from executor.runner import run_test
from coverage.parser import run_gcov, parse_gcov
from llm.client import LLMClient
from llm.prompter import build_prompt, extract_cpp_code, SYSTEM_PROMPT
from core.types import CoverageData, CoverageType
from langgraph.graph import StateGraph, END


class OptimizerState(TypedDict):
    iteration: int
    current_tests_str: str
    current_coverage: Optional[CoverageData]
    compile_success: bool
    run_success: bool
    stop: bool
    missing_info: str
    status: str

class CoverageOptimizer:
    def __init__(self, source_file: str, max_iters: int = 5, api_key: str = None, model: str = "gemini-2.5-flash", seed_tests: bool = True, coverage_type: CoverageType = CoverageType.LINE, coverage_threshold: float = 100.0, focus_mode: str = "coverage"):
        self.source_file = source_file
        self.source_basename = os.path.basename(source_file)
        self.test_include_basename = self.source_basename
        self.max_iters = max_iters
        self.seed_tests = seed_tests
        self.coverage_type = coverage_type
        self.coverage_threshold = coverage_threshold
        self.focus_mode = focus_mode
        self.llm_client = LLMClient(api_key=api_key, model=model)
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
            
        self.generated_test_funcs: List[str] = []
        self.test_func_names: List[str] = []
        self.test_generation_reasons: List[dict] = []
        self.changed_lines: List[int] = []
        
        # Working directory for tests.
        #
        # Use a per-run temp dir to avoid:
        # - stale test_main.cpp from previous targets
        # - mixing gcov artifacts across runs
        # - modifying tracked `.coverage_run/*` files in the repo
        safe_stem = os.path.splitext(self.source_basename)[0]
        source_hash = hashlib.sha1(os.path.abspath(self.source_file).encode("utf-8")).hexdigest()[:10]
        run_id = str(int(time.time()))
        self.work_dir = os.path.join(tempfile.gettempdir(), "major_project_2_coverage", f"{safe_stem}_{source_hash}_{run_id}")
        os.makedirs(self.work_dir, exist_ok=True)
        self.test_file_path = os.path.join(self.work_dir, "test_main.cpp")
        
        # Copy source to working directory to avoid polluting original dir.
        # If source defines `main`, include a sanitized copy in tests to avoid
        # duplicate entrypoint collisions with generated `test_main.cpp`.
        source_in_workdir = os.path.join(self.work_dir, self.source_basename)
        shutil.copy(self.source_file, source_in_workdir)
        self._prepare_testable_source(source_in_workdir)
        self.changed_lines = self._get_changed_lines_from_git()
        self._graph = self._build_langgraph()

    def _get_changed_lines_from_git(self) -> List[int]:
        if self.focus_mode != "diff":
            return []

        try:
            rel = os.path.relpath(self.source_file, start=os.getcwd())
            cmd = ["git", "diff", "--unified=0", "--", rel]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return []

            changed = set()
            for line in result.stdout.splitlines():
                if not line.startswith("@@"):
                    continue
                m = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if not m:
                    continue
                start = int(m.group(1))
                count = int(m.group(2) or "1")
                if count <= 0:
                    continue
                for ln in range(start, start + count):
                    changed.add(ln)
            if changed:
                print(f"Diff-focused mode: detected {len(changed)} changed lines in {self.source_basename}")
            return sorted(changed)
        except Exception:
            return []

    def _prepare_testable_source(self, source_in_workdir: str) -> None:
        """
        Prepares the source file used by `test_main.cpp`.
        When a translation unit contains `main`, create a copy with `main`
        removed and include that copy from tests.
        """
        with open(source_in_workdir, "r", encoding="utf-8") as f:
            code = f.read()

        sanitized = self._remove_top_level_main(code)
        if sanitized == code:
            self.test_include_basename = self.source_basename
            return

        stem, ext = os.path.splitext(self.source_basename)
        sanitized_basename = f"{stem}__for_tests{ext}"
        sanitized_path = os.path.join(self.work_dir, sanitized_basename)
        with open(sanitized_path, "w", encoding="utf-8") as f:
            f.write(sanitized)
        self.test_include_basename = sanitized_basename

    @staticmethod
    def _remove_top_level_main(code: str) -> str:
        """
        Removes `main(...) { ... }` at top level using a lightweight scanner.
        Keeps everything else untouched.
        """
        pattern = re.compile(r"\b(?:int|auto|void)\s+main\s*\([^)]*\)\s*\{", re.MULTILINE)
        match = pattern.search(code)
        if not match:
            return code

        start = match.start()
        i = match.end() - 1  # position at opening '{'
        depth = 0
        while i < len(code):
            ch = code[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    # Also trim a trailing newline immediately after main block.
                    if end < len(code) and code[end] == "\n":
                        end += 1
                    return code[:start] + code[end:]
            i += 1
        return code

    def _build_langgraph(self):
        workflow = StateGraph(OptimizerState)
        workflow.add_node("prepare_iteration", self._node_prepare_iteration)
        workflow.add_node("compile", self._node_compile)
        workflow.add_node("run_tests", self._node_run_tests)
        workflow.add_node("measure_coverage", self._node_measure_coverage)
        workflow.add_node("query_llm", self._node_query_llm)
        workflow.add_node("advance_iteration", self._node_advance_iteration)

        workflow.set_entry_point("prepare_iteration")
        workflow.add_edge("prepare_iteration", "compile")
        workflow.add_conditional_edges(
            "compile",
            self._route_after_compile,
            {"run_tests": "run_tests", "advance_iteration": "advance_iteration"},
        )
        workflow.add_conditional_edges(
            "run_tests",
            self._route_after_run,
            {"measure_coverage": "measure_coverage", "advance_iteration": "advance_iteration"},
        )
        workflow.add_conditional_edges(
            "measure_coverage",
            self._route_after_coverage,
            {"query_llm": "query_llm", "end": END},
        )
        workflow.add_edge("query_llm", "advance_iteration")
        workflow.add_conditional_edges(
            "advance_iteration",
            self._route_after_advance,
            {"prepare_iteration": "prepare_iteration", "end": END},
        )
        return workflow.compile()

    def _maybe_add_seed_tests(self) -> None:
        """
        Add a small deterministic seed test to avoid 0% coverage when the LLM
        is unavailable. Only targets very simple free functions.
        """
        if not self.seed_tests:
            return
        if self.generated_test_funcs or self.test_func_names:
            return

        # Special-case the known sample `math_ops.cpp` shape:
        # int calculate(int a, int b, char op)
        match = re.search(
            r'(?m)^\s*int\s+calculate\s*\(\s*int\s+\w+\s*,\s*int\s+\w+\s*,\s*char\s+\w+\s*\)\s*\{',
            self.source_code
        )
        if not match:
            return

        func_name = "test_seed_0"
        func_code = (
            f"void {func_name}() {{\n"
            "    (void)calculate(1, 2, '+');\n"
            "    (void)calculate(5, 3, '-');\n"
            "    (void)calculate(3, 4, '*');\n"
            "    (void)calculate(8, 2, '/');\n"
            "    (void)calculate(8, 0, '/');\n"
            "    (void)calculate(1, 2, '?');\n"
            "}\n"
        )
        self.generated_test_funcs.append(func_code)
        self.test_func_names.append(func_name)

    def generate_test_file(self):
        """Generates the test_main.cpp file uniting all LLM generated tests."""
        includes = f'#include "{self.test_include_basename}"\n#include <cassert>\n#include <iostream>\n\n'
        
        funcs = "\n\n".join(self.generated_test_funcs)
        
        main_body = "int main() {\n"
        for call in self.test_func_names:
            main_body += f"    {call}();\n"
        main_body += '    std::cout << "All tests passed successfully!\\n";\n'
        main_body += "    return 0;\n"
        main_body += "}\n"
        
        full_code = includes + funcs + "\n\n" + main_body
        
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(full_code)
            
        return full_code

    def _node_prepare_iteration(self, state: OptimizerState) -> OptimizerState:
        print(f"\n--- Iteration {state['iteration']}/{self.max_iters} ---")
        current_tests_str = self.generate_test_file()
        return {
            **state,
            "current_tests_str": current_tests_str,
            "compile_success": False,
            "run_success": False,
            "stop": False,
            "status": "prepared",
        }

    def _node_compile(self, state: OptimizerState) -> OptimizerState:
        print("Compiling test executable...")
        success = compile_cpp(["test_main.cpp"], "a.out", cwd=self.work_dir)
        if not success:
            print("Compilation failed! The LLM may have generated invalid C++.")
            if self.generated_test_funcs:
                print("Rolling back last generated test...")
                self.generated_test_funcs.pop()
                self.test_func_names.pop()
        return {**state, "compile_success": success}

    def _node_run_tests(self, state: OptimizerState) -> OptimizerState:
        print("Running tests...")
        result = run_test("./a.out", cwd=self.work_dir)
        if not result.success:
            print(f"Test execution failed (Exit Code {result.exit_code}):\n{result.stderr}")
            if self.generated_test_funcs:
                print("Rolling back last generated test as it caused a crash/failure...")
                self.generated_test_funcs.pop()
                self.test_func_names.pop()
            return {**state, "run_success": False}
        return {**state, "run_success": True}

    def _node_measure_coverage(self, state: OptimizerState) -> OptimizerState:
        print(f"Running gcov and measuring {self.coverage_type.value} coverage...")
        run_gcov("test_main.cpp", cwd=self.work_dir, coverage_type=self.coverage_type)
        gcov_path = os.path.join(self.work_dir, f"{self.test_include_basename}.gcov")
        current_coverage = parse_gcov(gcov_path, coverage_type=self.coverage_type)
        print(f"Current {self.coverage_type.value.title()} Coverage: {current_coverage.overall_percentage:.2f}%")

        if self.coverage_type == CoverageType.LINE:
            missing_info = f"lines: {current_coverage.uncovered_lines}"
        elif self.coverage_type == CoverageType.BRANCH:
            missing_info = f"branches: {current_coverage.uncovered_branches}"
        else:
            missing_info = f"functions: {current_coverage.uncovered_functions}"

        stop = False
        if current_coverage.meets_threshold(self.coverage_threshold):
            print(f"Coverage threshold of {self.coverage_threshold:.1f}% reached! Stopping.")
            stop = True
        elif current_coverage.is_fully_covered:
            print("100% coverage achieved! Stopping.")
            stop = True
        elif state["iteration"] >= self.max_iters:
            print("Maximum iterations reached.")
            stop = True

        return {
            **state,
            "current_coverage": current_coverage,
            "missing_info": missing_info,
            "stop": stop,
            "status": "measured",
        }

    def _node_query_llm(self, state: OptimizerState) -> OptimizerState:
        current_coverage = state.get("current_coverage")
        if current_coverage is None:
            return state

        print(f"Missing coverage on {state.get('missing_info', '')}")
        print("Querying LLM for new test cases...")

        func_name = f"test_llm_gen_{state['iteration']}"
        custom_instruction = (
            SYSTEM_PROMPT
            + f"\nCRITICAL: Your response must be EXACTLY a void C++ function named '{func_name}()' containing the assertions.\n"
        )
        prompt = build_prompt(
            source_code=self.source_code,
            uncovered_lines=current_coverage.uncovered_lines,
            current_tests=state["current_tests_str"],
            prioritized_lines=sorted(set(current_coverage.uncovered_lines).intersection(self.changed_lines)) if self.changed_lines else None,
        )
        llm_response = self.llm_client.generate_content(prompt, system_instruction=custom_instruction)
        new_test_code = extract_cpp_code(llm_response)
        if new_test_code:
            print(f"LLM successfully generated {func_name}")
            self.generated_test_funcs.append(new_test_code)
            self.test_func_names.append(func_name)
            priority_targets = sorted(set(current_coverage.uncovered_lines).intersection(self.changed_lines)) if self.changed_lines else []
            self.test_generation_reasons.append(
                {
                    "function_name": func_name,
                    "iteration": state["iteration"],
                    "focus_mode": self.focus_mode,
                    "target_uncovered_lines": current_coverage.uncovered_lines[:30],
                    "priority_lines": priority_targets[:30],
                    "reason": (
                        "Prioritized uncovered changed lines from git diff first."
                        if priority_targets
                        else "Targeted currently uncovered executable lines from coverage report."
                    ),
                }
            )
        else:
            print("LLM failed to generate a valid C++ code block.")
        return {**state, "status": "llm_queried"}

    def _node_advance_iteration(self, state: OptimizerState) -> OptimizerState:
        return {**state, "iteration": state["iteration"] + 1}

    def _route_after_compile(self, state: OptimizerState) -> str:
        return "run_tests" if state.get("compile_success", False) else "advance_iteration"

    def _route_after_run(self, state: OptimizerState) -> str:
        return "measure_coverage" if state.get("run_success", False) else "advance_iteration"

    def _route_after_coverage(self, state: OptimizerState) -> str:
        return "end" if state.get("stop", False) else "query_llm"

    def _route_after_advance(self, state: OptimizerState) -> str:
        return "prepare_iteration" if state["iteration"] <= self.max_iters else "end"

    def run_optimization_loop(self) -> Tuple[CoverageData, List[str]]:
        """
        Runs the LLM coverage optimization loop.
        Returns the final CoverageData and the list of generated test function bodies.
        """
        print(f"Starting LLM coverage optimization for {self.source_file}")
        # Ensure the first iteration actually executes something for simple targets.
        self._maybe_add_seed_tests()
        final_state = self._graph.invoke(
            {
                "iteration": 1,
                "current_tests_str": "",
                "current_coverage": None,
                "compile_success": False,
                "run_success": False,
                "stop": False,
                "missing_info": "",
                "status": "init",
            }
        )

        current_coverage = final_state.get("current_coverage")
        if current_coverage is None:
            current_coverage = CoverageData(
                overall_percentage=0.0,
                line_counts={},
                uncovered_lines=[],
                coverage_type=self.coverage_type,
            )

        print("Optimization complete.")
        return current_coverage, self.generated_test_funcs
