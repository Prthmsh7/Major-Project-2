import subprocess
import os
import re
from core.types import CoverageData, CoverageType

def run_gcov(source_file: str, cwd: str = ".", coverage_type: CoverageType = CoverageType.LINE) -> bool:
    """
    Runs gcov on the specified source file with appropriate options for coverage type.
    
    Args:
        source_file: Path to the .cpp source file
        cwd: Directory where the command will be run
        coverage_type: Type of coverage to measure
        
    Returns:
        bool: True if gcov ran successfully, False otherwise
    """
    try:
        cmd = ["gcov"]
        if coverage_type == CoverageType.BRANCH:
            cmd.append("-b")  # Enable branch coverage
        elif coverage_type == CoverageType.FUNCTION:
            cmd.append("-f")  # Enable function coverage
        cmd.append(source_file)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running gcov: {e}")
        return False

def parse_gcov(gcov_file: str, coverage_type: CoverageType = CoverageType.LINE) -> CoverageData:
    """
    Parses a .gcov file and extracts execution counts for the specified coverage type.
    
    Args:
        gcov_file: Path to the .gcov file
        coverage_type: Type of coverage to parse
        
    Returns:
        CoverageData object
    """
    line_counts = {}
    uncovered_lines = []
    branch_counts = {}
    uncovered_branches = []
    function_counts = {}
    uncovered_functions = []
    
    total_executable = 0
    total_branches = 0
    total_functions = 0
    
    if not os.path.exists(gcov_file):
        print(f"Error: {gcov_file} not found.")
        return CoverageData(
            overall_percentage=0.0, 
            line_counts={}, 
            uncovered_lines=[],
            coverage_type=coverage_type
        )

    with open(gcov_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
                
            count_str = parts[0].strip()
            line_str = parts[1].strip()
            code = parts[2].strip()
            
            try:
                line_num = int(line_str)
            except ValueError:
                continue
                
            if line_num == 0:
                # Handle branch and function summary lines
                if "branch" in code.lower() and coverage_type == CoverageType.BRANCH:
                    # Parse branch coverage summary
                    if "taken" in code.lower() or "never" in code.lower():
                        branch_match = re.search(r'branch\s+(\d+)\s+(taken|never)', code.lower())
                        if branch_match:
                            branch_id = branch_match.group(1)
                            taken = branch_match.group(2) == "taken"
                            total_branches += 1
                            if taken:
                                branch_counts[branch_id] = 1
                            else:
                                uncovered_branches.append(branch_id)
                                branch_counts[branch_id] = 0
                
                if "function" in code.lower() and coverage_type == CoverageType.FUNCTION:
                    # Parse function coverage summary
                    func_match = re.search(r'function\s+(\w+)\s+(called|never)', code.lower())
                    if func_match:
                        func_name = func_match.group(1)
                        called = func_match.group(2) == "called"
                        total_functions += 1
                        if called:
                            function_counts[func_name] = 1
                        else:
                            uncovered_functions.append(func_name)
                            function_counts[func_name] = 0
                continue
                
            if count_str == '-':
                # Not executable code
                continue
                
            # Line coverage parsing (default)
            total_executable += 1
            
            if count_str.startswith('#') or count_str.startswith('='):
                # Uncovered executable line
                line_counts[line_num] = 0
                uncovered_lines.append(line_num)
            else:
                try:
                    # sometimes there's an asterisk indicating a branch
                    count_val = int(count_str.replace('*', ''))
                    line_counts[line_num] = count_val
                except ValueError:
                    # Fallback for unexpected formats
                    line_counts[line_num] = 0
                    uncovered_lines.append(line_num)
    
    # Calculate overall percentage based on coverage type
    overall_percentage = 0.0
    
    if coverage_type == CoverageType.LINE:
        if total_executable == 0:
            overall_percentage = 100.0
        else:
            covered = total_executable - len(uncovered_lines)
            overall_percentage = (covered / total_executable) * 100.0
    elif coverage_type == CoverageType.BRANCH:
        if total_branches == 0:
            overall_percentage = 100.0
        else:
            covered = total_branches - len(uncovered_branches)
            overall_percentage = (covered / total_branches) * 100.0
    elif coverage_type == CoverageType.FUNCTION:
        if total_functions == 0:
            overall_percentage = 100.0
        else:
            covered = total_functions - len(uncovered_functions)
            overall_percentage = (covered / total_functions) * 100.0
        
    return CoverageData(
        overall_percentage=overall_percentage,
        line_counts=line_counts,
        uncovered_lines=uncovered_lines,
        coverage_type=coverage_type,
        branch_counts=branch_counts,
        uncovered_branches=uncovered_branches,
        function_counts=function_counts,
        uncovered_functions=uncovered_functions
    )
