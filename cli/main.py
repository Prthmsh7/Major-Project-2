import argparse
import sys
import os
from core.loop import CoverageOptimizer
from core.types import CoverageType

def main():
    parser = argparse.ArgumentParser(description="LLM-Assisted Statement Coverage Testing Tool for C++")
    parser.add_argument("--source", required=True, help="Path to the C++ source file to test")
    parser.add_argument("--max-iters", type=int, default=5, help="Maximum number of LLM feedback iterations")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="LLM model to use")
    parser.add_argument(
        "--coverage-type", 
        type=str, 
        choices=["line", "branch", "function"], 
        default="line",
        help="Type of coverage to measure (default: line)"
    )
    parser.add_argument(
        "--coverage-threshold", 
        type=float, 
        default=100.0,
        help="Stop when coverage reaches this percentage (default: 100.0)"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.source):
        print(f"Error: Source file '{args.source}' does not exist.")
        sys.exit(1)
        
    try:
        coverage_type = CoverageType(args.coverage_type)
        optimizer = CoverageOptimizer(
            source_file=args.source,
            max_iters=args.max_iters,
            model=args.model,
            coverage_type=coverage_type,
            coverage_threshold=args.coverage_threshold
        )
        final_coverage, test_funcs = optimizer.run_optimization_loop()
        
        print("\n" + "="*40)
        print("          FINAL RESULTS")
        print("="*40)
        print(f"Target File: {args.source}")
        print(f"Coverage Type: {args.coverage_type}")
        print(f"Final {args.coverage_type.title()} Coverage: {final_coverage.overall_percentage:.2f}%")
        print(f"Coverage Threshold: {args.coverage_threshold:.1f}%")
        print(f"Total Test Cases Generated: {len(test_funcs)}")
        print(f"Final Test Suite Path: {optimizer.test_file_path}")
        print("="*40)
        
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
