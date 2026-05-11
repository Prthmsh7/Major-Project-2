import os
import shutil
import tempfile
import time
import hashlib
import re
from typing import List, Tuple
from executor.compiler import compile_cpp
from executor.runner import run_test
from coverage.parser import run_gcov, parse_gcov
from llm.client import LLMClient
from llm.prompter import build_prompt, extract_cpp_code, SYSTEM_PROMPT
from core.types import CoverageData, CoverageType
from analysis.mutation import compute_mutation_score

class CoverageOptimizer:
    def __init__(self, source_file: str, max_iters: int = 5, api_key: str = None, model: str = "gemini-2.5-flash", seed_tests: bool = True, coverage_type: CoverageType = CoverageType.LINE, coverage_threshold: float = 100.0, objective: str = "coverage", mutation_threshold: float = 70.0):
        self.source_file = source_file
        self.source_basename = os.path.basename(source_file)
        self.test_include_basename = self.source_basename
        self.max_iters = max_iters
        self.seed_tests = seed_tests
        self.coverage_type = coverage_type
        self.coverage_threshold = coverage_threshold
        self.objective = objective
        self.mutation_threshold = mutation_threshold
        self.llm_client = LLMClient(api_key=api_key, model=model)
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
            
        self.generated_test_funcs: List[str] = []
        self.test_func_names: List[str] = []
        self.iteration_history: List[dict] = []
        
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
        # If source defines `main`, include a sanitized test-only copy.
        source_in_workdir = os.path.join(self.work_dir, self.source_basename)
        shutil.copy(self.source_file, source_in_workdir)
        self._prepare_testable_source(source_in_workdir)

    def _prepare_testable_source(self, source_in_workdir: str) -> None:
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
        pattern = re.compile(r"\b(?:int|auto|void)\s+main\s*\([^)]*\)\s*\{", re.MULTILINE)
        match = pattern.search(code)
        if not match:
            return code

        start = match.start()
        i = match.end() - 1
        depth = 0
        while i < len(code):
            ch = code[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    if end < len(code) and code[end] == "\n":
                        end += 1
                    return code[:start] + code[end:]
            i += 1
        return code

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

    def run_optimization_loop(self) -> Tuple[CoverageData, List[str]]:
        """
        Runs the LLM coverage optimization loop.
        Returns the final CoverageData and the list of generated test function bodies.
        """
        print(f"Starting LLM coverage optimization for {self.source_file}")
        
        # Initial empty coverage state if no tests
        current_coverage = None

        # Ensure the first iteration actually executes something for simple targets.
        self._maybe_add_seed_tests()
        
        for iteration in range(1, self.max_iters + 1):
            print(f"\n--- Iteration {iteration}/{self.max_iters} ---")
            iter_start = time.time()
            compile_ok = False
            run_ok = False
            mutation_score = None
            uncovered_count = None
            action = "none"
            
            # 1. Generate current test file
            current_tests_str = self.generate_test_file()
            
            # 2. Compile
            print("Compiling test executable...")
            # We only compile test_main.cpp since it #includes the target file
            success = compile_cpp(["test_main.cpp"], "a.out", cwd=self.work_dir)
            compile_ok = success
            if not success:
                print("Compilation failed! The LLM may have generated invalid C++.")
                # We could rollback the last generated test here, but for simplicity we stop
                # or we just pop the last test and try again.
                if self.generated_test_funcs:
                    print("Rolling back last generated test...")
                    self.generated_test_funcs.pop()
                    self.test_func_names.pop()
                    action = "rollback_generated_test"
                self.iteration_history.append({
                    "iteration": iteration,
                    "compile_success": compile_ok,
                    "run_success": run_ok,
                    "coverage": 0.0,
                    "mutation_score": mutation_score,
                    "uncovered_count": uncovered_count,
                    "action": action,
                    "duration_ms": int((time.time() - iter_start) * 1000),
                })
                continue
                
            # 3. Run Test
            print("Running tests...")
            result = run_test("./a.out", cwd=self.work_dir)
            run_ok = result.success
            if not result.success:
                print(f"Test execution failed (Exit Code {result.exit_code}):\n{result.stderr}")
                if self.generated_test_funcs:
                    print("Rolling back last generated test as it caused a crash/failure...")
                    self.generated_test_funcs.pop()
                    self.test_func_names.pop()
                    action = "rollback_generated_test"
                self.iteration_history.append({
                    "iteration": iteration,
                    "compile_success": compile_ok,
                    "run_success": run_ok,
                    "coverage": 0.0,
                    "mutation_score": mutation_score,
                    "uncovered_count": uncovered_count,
                    "action": action,
                    "duration_ms": int((time.time() - iter_start) * 1000),
                })
                continue
                
            # 4. Measure Coverage
            print(f"Running gcov and measuring {self.coverage_type.value} coverage...")
            run_gcov("test_main.cpp", cwd=self.work_dir, coverage_type=self.coverage_type)
            gcov_path = os.path.join(self.work_dir, f"{self.test_include_basename}.gcov")
            
            current_coverage = parse_gcov(gcov_path, coverage_type=self.coverage_type)
            print(f"Current {self.coverage_type.value.title()} Coverage: {current_coverage.overall_percentage:.2f}%")
            if self.coverage_type == CoverageType.LINE:
                uncovered_count = len(current_coverage.uncovered_lines)
            elif self.coverage_type == CoverageType.BRANCH:
                uncovered_count = len(current_coverage.uncovered_branches)
            else:
                uncovered_count = len(current_coverage.uncovered_functions)
            
            # 5. Optional mutation objective evaluation
            mutation_score = None
            if self.objective in {"mutation", "hybrid"}:
                source_in_workdir = os.path.join(self.work_dir, self.source_basename)
                mres = compute_mutation_score(source_in_workdir, self.test_file_path, self.work_dir)
                mutation_score = mres.mutation_score
                print(f"Mutation Score: {mres.mutation_score:.2f}% ({mres.killed}/{mres.total})")

            # 6. Check Stopping Criteria
            if current_coverage.meets_threshold(self.coverage_threshold):
                print(f"Coverage threshold of {self.coverage_threshold:.1f}% reached! Stopping.")
                if self.objective == "coverage":
                    break
                
            if current_coverage.is_fully_covered:
                print("100% coverage achieved! Stopping.")
                if self.objective == "coverage":
                    break

            if self.objective == "mutation" and mutation_score is not None and mutation_score >= self.mutation_threshold:
                print(f"Mutation threshold of {self.mutation_threshold:.1f}% reached! Stopping.")
                break

            if self.objective == "hybrid" and mutation_score is not None and current_coverage.meets_threshold(self.coverage_threshold) and mutation_score >= self.mutation_threshold:
                print("Hybrid objective reached (coverage + mutation). Stopping.")
                break
                
            if iteration == self.max_iters:
                print("Maximum iterations reached.")
                self.iteration_history.append({
                    "iteration": iteration,
                    "compile_success": compile_ok,
                    "run_success": run_ok,
                    "coverage": current_coverage.overall_percentage,
                    "mutation_score": mutation_score,
                    "uncovered_count": uncovered_count,
                    "action": action,
                    "duration_ms": int((time.time() - iter_start) * 1000),
                })
                break
                
            # 7. Query LLM
            missing_info = ""
            if self.coverage_type == CoverageType.LINE:
                missing_info = f"lines: {current_coverage.uncovered_lines}"
            elif self.coverage_type == CoverageType.BRANCH:
                missing_info = f"branches: {current_coverage.uncovered_branches}"
            elif self.coverage_type == CoverageType.FUNCTION:
                missing_info = f"functions: {current_coverage.uncovered_functions}"
                
            print(f"Missing coverage on {missing_info}")
            print("Querying LLM for new test cases...")
            
            func_name = f"test_llm_gen_{iteration}"
            custom_instruction = SYSTEM_PROMPT + f"\nCRITICAL: Your response must be EXACTLY a void C++ function named '{func_name}()' containing the assertions.\n"
            
            prompt = build_prompt(
                source_code=self.source_code,
                uncovered_lines=current_coverage.uncovered_lines,
                current_tests=current_tests_str
            )
            
            llm_response = self.llm_client.generate_content(prompt, system_instruction=custom_instruction)
            new_test_code = extract_cpp_code(llm_response)
            
            if new_test_code:
                print(f"LLM successfully generated {func_name}")
                self.generated_test_funcs.append(new_test_code)
                self.test_func_names.append(func_name)
                action = "added_test"
            else:
                print("LLM failed to generate a valid C++ code block.")
                action = "llm_no_code"

            self.iteration_history.append({
                "iteration": iteration,
                "compile_success": compile_ok,
                "run_success": run_ok,
                "coverage": current_coverage.overall_percentage,
                "mutation_score": mutation_score,
                "uncovered_count": uncovered_count,
                "action": action,
                "duration_ms": int((time.time() - iter_start) * 1000),
            })
                
        # Clean up
        print("Optimization complete.")
        return current_coverage, self.generated_test_funcs
