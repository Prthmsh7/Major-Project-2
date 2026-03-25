import subprocess
import os
import re
from core.types import CoverageData

def run_gcov(source_file: str, cwd: str = ".") -> bool:
    """
    Runs gcov on the specified source file.
    Expects the corresponding .gcno and .gcda files to be present in cwd.
    
    Args:
        source_file: Path to the .cpp source file
        cwd: Directory where the command will be run
        
    Returns:
        bool: True if gcov ran successfully, False otherwise
    """
    try:
        # gcov generates a target.cpp.gcov file in the current working directory
        result = subprocess.run(
            ["gcov", source_file],
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running gcov: {e}")
        return False

def parse_gcov(gcov_file: str) -> CoverageData:
    """
    Parses a .gcov file and extracts execution counts.
    
    Args:
        gcov_file: Path to the .gcov file
        
    Returns:
        CoverageData object
    """
    line_counts = {}
    uncovered_lines = []
    total_executable = 0
    
    if not os.path.exists(gcov_file):
        print(f"Error: {gcov_file} not found.")
        return CoverageData(overall_percentage=0.0, line_counts={}, uncovered_lines=[])

    with open(gcov_file, 'r', encoding='utf-8') as f:
        for line in f:
            # gcov format is roughly: "execution_count:line_number:code"
            # e.g., "    #####:   10:    return 0;"
            # e.g., "        1:   11:}"
            # e.g., "        -:   12:// comment"
            parts = line.split(':', 2)
            if len(parts) < 3:
                continue
                
            count_str = parts[0].strip()
            line_str = parts[1].strip()
            
            try:
                line_num = int(line_str)
            except ValueError:
                continue
                
            if line_num == 0:
                # Meta lines like "0:Source:math_ops.cpp"
                continue
                
            if count_str == '-':
                # Not executable code
                continue
                
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
                
    if total_executable == 0:
        overall_percentage = 100.0  # Nothing to cover
    else:
        covered = total_executable - len(uncovered_lines)
        overall_percentage = (covered / total_executable) * 100.0
        
    return CoverageData(
        overall_percentage=overall_percentage,
        line_counts=line_counts,
        uncovered_lines=uncovered_lines
    )
