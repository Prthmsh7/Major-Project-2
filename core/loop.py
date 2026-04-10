import os
import shutil
from typing import List, Tuple
from executor.compiler import compile_cpp
from executor.runner import run_test
from coverage.parser import run_gcov, parse_gcov
from llm.client import LLMClient
from llm.prompter import build_prompt, extract_cpp_code, SYSTEM_PROMPT
from core.types import CoverageData, CoverageType

class CoverageOptimizer:
    def __init__(self, source_file: str, max_iters: int = 5, api_key: str = None, model: str = "gemini-2.5-flash", coverage_type: CoverageType = CoverageType.LINE, coverage_threshold: float = 100.0):
        self.source_file = source_file
        self.source_basename = os.path.basename(source_file)
        self.max_iters = max_iters
        self.coverage_type = coverage_type
        self.coverage_threshold = coverage_threshold
        self.llm_client = LLMClient(api_key=api_key, model=model)
        
        with open(self.source_file, 'r', encoding='utf-8') as f:
            self.source_code = f.read()
            
        self.generated_test_funcs: List[str] = []
        self.test_func_names: List[str] = []
        
        # Working directory for tests
        self.work_dir = ".coverage_run"
        os.makedirs(self.work_dir, exist_ok=True)
        self.test_file_path = os.path.join(self.work_dir, "test_main.cpp")
        
        # Copy source to working directory to avoid polluting original dir
        shutil.copy(self.source_file, self.work_dir)

    def generate_test_file(self):
        """Generates the test_main.cpp file uniting all LLM generated tests."""
        includes = f'#include "{self.source_basename}"\n#include <cassert>\n#include <iostream>\n\n'
        
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
        
        for iteration in range(1, self.max_iters + 1):
            print(f"\n--- Iteration {iteration}/{self.max_iters} ---")
            
            # 1. Generate current test file
            current_tests_str = self.generate_test_file()
            
            # 2. Compile
            print("Compiling test executable...")
            # We only compile test_main.cpp since it #includes the target file
            success = compile_cpp(["test_main.cpp"], "a.out", cwd=self.work_dir)
            if not success:
                print("Compilation failed! The LLM may have generated invalid C++.")
                # We could rollback the last generated test here, but for simplicity we stop
                # or we just pop the last test and try again.
                if self.generated_test_funcs:
                    print("Rolling back last generated test...")
                    self.generated_test_funcs.pop()
                    self.test_func_names.pop()
                continue
                
            # 3. Run Test
            print("Running tests...")
            result = run_test("./a.out", cwd=self.work_dir)
            if not result.success:
                print(f"Test execution failed (Exit Code {result.exit_code}):\n{result.stderr}")
                if self.generated_test_funcs:
                    print("Rolling back last generated test as it caused a crash/failure...")
                    self.generated_test_funcs.pop()
                    self.test_func_names.pop()
                continue
                
            # 4. Measure Coverage
            print(f"Running gcov and measuring {self.coverage_type.value} coverage...")
            run_gcov("test_main.cpp", cwd=self.work_dir, coverage_type=self.coverage_type)
            gcov_path = os.path.join(self.work_dir, f"{self.source_basename}.gcov")
            
            current_coverage = parse_gcov(gcov_path, coverage_type=self.coverage_type)
            print(f"Current {self.coverage_type.value.title()} Coverage: {current_coverage.overall_percentage:.2f}%")
            
            # 5. Check Stopping Criteria
            if current_coverage.meets_threshold(self.coverage_threshold):
                print(f"Coverage threshold of {self.coverage_threshold:.1f}% reached! Stopping.")
                break
                
            if current_coverage.is_fully_covered:
                print("100% coverage achieved! Stopping.")
                break
                
            if iteration == self.max_iters:
                print("Maximum iterations reached.")
                break
                
            # 6. Query LLM
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
            else:
                print("LLM failed to generate a valid C++ code block.")
                
        # Clean up
        print("Optimization complete.")
        return current_coverage, self.generated_test_funcs
