import re
from typing import List, Optional

SYSTEM_PROMPT = """You are an expert C++ Software Testing Engineer.
Your goal is to maximize statement coverage for a given piece of C++ code.
You will be provided with:
1. The original C++ source code.
2. A list of exact line numbers that are currently missing test coverage.
3. The existing C++ test code (so you do not duplicate tests).

IMPORTANT: The original source file already contains a main() function. You MUST NOT write another main() function.
Write ONLY a void function named 'test_llm_generated_X()' where X is the iteration number.
This function should contain assertions or test code that exercises the uncovered lines.

Only output C++ code. Do not output anything else.
Wrap your code in a single ```cpp codeblock.
Assume standard includes like <iostream>, <cassert>, and the original source file are already included.
"""

def build_prompt(
    source_code: str,
    uncovered_lines: List[int],
    current_tests: str = "",
    prioritized_lines: Optional[List[int]] = None,
) -> str:
    """
    Constructs the prompt for the LLM.
    """
    prompt = "--- ORIGINAL C++ SOURCE CODE ---\n"
    # Provide the source with line numbers for context
    lines = source_code.split('\n')
    for i, line in enumerate(lines, 1):
        prompt += f"{i:4d}: {line}\n"
        
    prompt += "\n--- UNCOVERED LINES ---\n"
    prompt += "The following line numbers are executable but have NOT been covered yet:\n"
    prompt += ", ".join(map(str, uncovered_lines)) + "\n"

    if prioritized_lines:
        prompt += "\n--- PRIORITY LINES (DIFF-FOCUSED MODE) ---\n"
        prompt += "Prioritize these uncovered changed lines first:\n"
        prompt += ", ".join(map(str, prioritized_lines)) + "\n"
    
    if current_tests:
        prompt += "\n--- EXISTING TEST CODE ---\n"
        prompt += current_tests + "\n"
        
    prompt += "\n--- INSTRUCTIONS ---\n"
    prompt += "Write C++ testing code (assertions or function calls) to cover the lines explicitly listed above.\n"
    if prioritized_lines:
        prompt += "PRIORITY: Maximize coverage for the PRIORITY LINES first, then remaining uncovered lines.\n"
    prompt += "CRITICAL: Do NOT write a main() function as it already exists in the source file.\n"
    prompt += "Write ONLY a void function named 'test_llm_generated_X()' where X is the iteration number.\n"
    prompt += "Provide ONLY the C++ code block. No explanations.\n"
    
    return prompt

def extract_cpp_code(response_text: str) -> str:
    """
    Extracts the C++ code from the LLM's markdown response.
    Looks for ```cpp ... ``` blocks. If none found, tries to strip backticks or return raw text.
    """
    if not response_text:
        return ""
        
    # Find all cpp code blocks
    cpp_matches = re.findall(r'```(?:cpp|c\+\+)\n(.*?)\n```', response_text, re.DOTALL | re.IGNORECASE)
    
    if cpp_matches:
        # Join them if the LLM provided multiple snippets
        return "\n".join(cpp_matches)
        
    # Fallback to generic codeblocks
    generic_matches = re.findall(r'```\n(.*?)\n```', response_text, re.DOTALL)
    if generic_matches:
        return "\n".join(generic_matches)
        
    # Final fallback, just return the raw text assuming the LLM followed instructions perfectly
    clean_text = response_text.replace('```cpp', '').replace('```', '').strip()
    return clean_text
