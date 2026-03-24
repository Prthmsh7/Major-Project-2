import subprocess
import os
from typing import List

def compile_cpp(source_files: List[str], output_binary: str = "a.out", cwd: str = ".") -> bool:
    """
    Compiles the given C++ source files with gcov coverage flags.
    First compiles to object files to ensure standard .gcno naming, then links.
    
    Args:
        source_files: List of paths to .cpp files
        output_binary: Path for the compiled executable
        cwd: Directory context for execution
        
    Returns:
        bool: True if compilation succeeded, False otherwise
    """
    try:
        # Step 1: Compile to object files
        for src in source_files:
            cmd1 = ["g++", "-fprofile-arcs", "-ftest-coverage", "-c", src]
            res1 = subprocess.run(cmd1, capture_output=True, text=True, cwd=cwd)
            if res1.returncode != 0:
                print(f"Compilation Failed for {src}:\n{res1.stderr}")
                return False
                
        # Step 2: Link object files into executable
        obj_files = [src.replace(".cpp", ".o") for src in source_files]
        cmd2 = ["g++", "-fprofile-arcs", "-ftest-coverage", "-o", output_binary] + obj_files
        res2 = subprocess.run(cmd2, capture_output=True, text=True, cwd=cwd)
        if res2.returncode != 0:
            print(f"Linking Failed:\n{res2.stderr}")
            return False
            
        return True
        
    except FileNotFoundError:
        print("Error: 'g++' not found. Ensure GCC is installed.")
        return False
    except Exception as e:
        print(f"Compilation error: {e}")
        return False

def clean_coverage_artifacts(source_dir: str = ".") -> None:
    """
    Removes generated coverage files (.gcda, .gcno) and object files.
    """
    for file in os.listdir(source_dir):
        if file.endswith(".gcda") or file.endswith(".gcno") or file.endswith(".o") or file == "a.out":
            try:
                os.remove(os.path.join(source_dir, file))
            except Exception as e:
                pass
