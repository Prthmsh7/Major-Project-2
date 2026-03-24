import argparse
import sys
import os
from core.loop import CoverageOptimizer

def main():
    parser = argparse.ArgumentParser(description="LLM-Assisted Statement Coverage Testing Tool for C++")
    parser.add_argument("--source", required=True, help="Path to the C++ source file to test")
    parser.add_argument("--max-iters", type=int, default=5, help="Maximum number of LLM feedback iterations")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="LLM model to use")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.source):
        print(f"Error: Source file '{args.source}' does not exist.")
        sys.exit(1)
        
    try:
        optimizer = CoverageOptimizer(
            source_file=args.source,
            max_iters=args.max_iters,
            model=args.model
        )
        final_coverage, test_funcs = optimizer.run_optimization_loop()
        
        print("\n" + "="*40)
        print("          FINAL RESULTS")
        print("="*40)
        print(f"Target File: {args.source}")
        print(f"Final Statement Coverage: {final_coverage.overall_percentage:.2f}%")
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
