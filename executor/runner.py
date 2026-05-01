import subprocess
import os
from core.types import ExecutionResult

def clean_gcda(source_dir: str = ".") -> None:
    """
    Removes generated coverage data files (.gcda).
    These should be cleaned before running a binary to avoid cumulative coverage
    from previous runs that might skew results or include removed tests.
    """
    for file in os.listdir(source_dir):
        if file.endswith(".gcda"):
            try:
                os.remove(os.path.join(source_dir, file))
            except Exception as e:
                pass

def run_test(binary_path: str = "./a.out", timeout: int = 10, cwd: str = ".") -> ExecutionResult:
    """
    Executes the compiled C++ binary and captures the output.
    
    Args:
        binary_path: Path to the executable to run
        timeout: Maximum execution time in seconds
        cwd: Directory context for execution
        
    Returns:
        ExecutionResult containing exit code, stdout, stderr, and success status
    """
    # Clean previous run data
    clean_gcda(cwd)
    
    try:
        resolved_binary = binary_path
        candidate = binary_path if os.path.isabs(binary_path) else os.path.join(cwd, binary_path)
        if os.path.exists(candidate):
            resolved_binary = candidate
        elif os.name == "nt":
            exe_candidate = f"{candidate}.exe"
            if os.path.exists(exe_candidate):
                resolved_binary = exe_candidate

        result = subprocess.run(
            [resolved_binary],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        success = (result.returncode == 0)
        
        return ExecutionResult(
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            success=success
        )
        
    except subprocess.TimeoutExpired as e:
        return ExecutionResult(
            exit_code=-1,
            stdout=e.stdout.decode('utf-8') if e.stdout else "",
            stderr=f"Execution timed out after {timeout} seconds",
            success=False
        )
    except FileNotFoundError:
        return ExecutionResult(
            exit_code=-2,
            stdout="",
            stderr=f"Executable not found at {binary_path}",
            success=False
        )
    except Exception as e:
        return ExecutionResult(
            exit_code=-3,
            stdout="",
            stderr=f"Unknown execution error: {str(e)}",
            success=False
        )
