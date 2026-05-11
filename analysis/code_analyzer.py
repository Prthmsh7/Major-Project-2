import re
import ast
import os
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class ComplexityType(Enum):
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"

@dataclass
class ComplexityMetrics:
    cyclomatic_complexity: int
    cognitive_complexity: int
    halstead_volume: float
    halstead_difficulty: float
    maintainability_index: float

@dataclass
class CodeSmell:
    type: str
    line: int
    description: str
    severity: str  # low, medium, high, critical
    suggestion: str

@dataclass
class CodeAnalysis:
    total_lines: int
    code_lines: int
    comment_lines: int
    empty_lines: int
    functions: List[Dict[str, Any]]
    complexity: ComplexityMetrics
    smells: List[CodeSmell]
    dependencies: List[str]

class CppCodeAnalyzer:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.current_function = None
        self.functions = []
        self.complexity_stack = []
        self.nesting_level = 0
    
    def analyze_file(self, file_path: str) -> CodeAnalysis:
        """Comprehensive code analysis for C++ files"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # Basic metrics
        total_lines = len(lines)
        code_lines = 0
        comment_lines = 0
        empty_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                empty_lines += 1
            elif stripped.startswith('//') or stripped.startswith('/*') or '*/' in stripped:
                comment_lines += 1
            else:
                code_lines += 1
        
        # Function analysis
        functions = self.extract_functions(content)
        
        # Complexity metrics
        complexity = self.calculate_complexity(content, functions)
        
        # Code smell detection
        smells = self.detect_code_smells(content, functions)
        
        # Dependencies
        dependencies = self.extract_dependencies(content)
        
        return CodeAnalysis(
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            empty_lines=empty_lines,
            functions=functions,
            complexity=complexity,
            smells=smells,
            dependencies=dependencies
        )
    
    def extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function information from C++ code"""
        functions = []
        
        # Pattern to match function definitions
        function_pattern = r'''
            (?:template\s*<[^>]*>\s*)?  # Template
            (?:inline\s+|virtual\s+|static\s+)?  # Specifiers
            (?:[\w:<>]+\s+)?  # Return type
            (\w+)\s*  # Function name
            \([^)]*\)  # Parameters
            (?:\s*const\s*)?  # Const qualifier
            (?:\s*override\s*)?  # Override
            \s*\{  # Opening brace
        '''
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if re.search(function_pattern, line, re.VERBOSE):
                # Extract function name
                name_match = re.search(r'(\w+)\s*\(', line)
                if name_match:
                    func_name = name_match.group(1)
                    
                    # Find function body
                    brace_count = 0
                    start_line = i
                    end_line = i
                    
                    for j in range(i-1, len(lines)):
                        brace_count += lines[j].count('{')
                        brace_count -= lines[j].count('}')
                        if brace_count == 0 and j >= i:
                            end_line = j + 1
                            break
                    
                    # Calculate function complexity
                    func_lines = lines[i-1:end_line]
                    func_content = '\n'.join(func_lines)
                    cyclomatic = self.calculate_cyclomatic_complexity(func_content)
                    
                    functions.append({
                        'name': func_name,
                        'line': i,
                        'start_line': start_line,
                        'end_line': end_line,
                        'lines': end_line - start_line + 1,
                        'cyclomatic_complexity': cyclomatic,
                        'parameters': self.extract_parameters(line)
                    })
        
        return functions
    
    def calculate_complexity(self, content: str, functions: List[Dict]) -> ComplexityMetrics:
        """Calculate various complexity metrics"""
        # Cyclomatic complexity
        total_cyclomatic = sum(f['cyclomatic_complexity'] for f in functions)
        avg_cyclomatic = total_cyclomatic / len(functions) if functions else 0
        
        # Cognitive complexity (simplified)
        cognitive_complexity = self.calculate_cognitive_complexity(content)
        
        # Halstead metrics (simplified)
        halstead_volume, halstead_difficulty = self.calculate_halstead_metrics(content)
        
        # Maintainability index (simplified formula)
        maintainability = max(0, 171 - 5.2 * (avg_cyclomatic ** 0.23) - 0.23 * cognitive_complexity - 16.2 * (len(content) / 1000))
        
        return ComplexityMetrics(
            cyclomatic_complexity=total_cyclomatic,
            cognitive_complexity=cognitive_complexity,
            halstead_volume=halstead_volume,
            halstead_difficulty=halstead_difficulty,
            maintainability_index=maintainability
        )
    
    def calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        
        # Decision points
        decision_keywords = ['if', 'else', 'elif', 'while', 'for', 'switch', 'case', 'catch', '&&', '||']
        
        for keyword in decision_keywords:
            complexity += len(re.findall(r'\b' + keyword + r'\b', content))
        
        # Ternary operators
        complexity += len(re.findall(r'\?', content))
        
        return complexity
    
    def calculate_cognitive_complexity(self, content: str) -> int:
        """Calculate cognitive complexity"""
        complexity = 0
        nesting_level = 0
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            # Increment for nesting
            if any(keyword in stripped for keyword in ['if', 'for', 'while', 'switch', 'catch']):
                nesting_level += 1
                complexity += nesting_level
            
            # Decrement for closing braces
            if '}' in stripped:
                nesting_level = max(0, nesting_level - 1)
            
            # Add complexity for logical operators
            complexity += stripped.count('&&') + stripped.count('||')
        
        return complexity
    
    def calculate_halstead_metrics(self, content: str) -> Tuple[float, float]:
        """Calculate simplified Halstead metrics"""
        # Extract operators and operands (simplified)
        operators = set(re.findall(r'[+\-*/%=<>!&|^~]', content))
        operands = set(re.findall(r'\b[a-zA-Z_]\w*\b', content))
        
        # Remove keywords from operands
        cpp_keywords = {'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 
                       'return', 'int', 'float', 'double', 'char', 'bool', 'void', 'const', 'static'}
        operands = {op for op in operands if op not in cpp_keywords}
        
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)    # Number of distinct operands
        
        # Count total occurrences
        N1 = sum(content.count(op) for op in operators)
        N2 = sum(len(re.findall(r'\b' + re.escape(op) + r'\b', content)) for op in operands)
        
        # Calculate metrics
        if n1 > 0 and n2 > 0 and N1 > 0 and N2 > 0:
            vocabulary = n1 + n2
            length = N1 + N2
            volume = length * (vocabulary.bit_length() / vocabulary)  # Simplified
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        else:
            volume = 0
            difficulty = 0
        
        return volume, difficulty
    
    def detect_code_smells(self, content: str, functions: List[Dict]) -> List[CodeSmell]:
        """Detect various code smells"""
        smells = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Long method
            for func in functions:
                if func['lines'] > 50:
                    smells.append(CodeSmell(
                        type="Long Method",
                        line=func['line'],
                        description=f"Function '{func['name']}' is too long ({func['lines']} lines)",
                        severity="medium",
                        suggestion="Consider breaking this function into smaller, more focused functions"
                    ))
            
            # Complex method
            for func in functions:
                if func['cyclomatic_complexity'] > 10:
                    smells.append(CodeSmell(
                        type="Complex Method",
                        line=func['line'],
                        description=f"Function '{func['name']}' has high cyclomatic complexity ({func['cyclomatic_complexity']})",
                        severity="high",
                        suggestion="Consider simplifying the logic or extracting helper methods"
                    ))
            
            # Magic numbers
            magic_numbers = re.findall(r'\b(?!0|1)\d+\b', stripped)
            for num in magic_numbers:
                if not any(keyword in stripped for keyword in ['return', 'case', 'sizeof']):
                    smells.append(CodeSmell(
                        type="Magic Number",
                        line=i,
                        description=f"Magic number '{num}' found",
                        severity="low",
                        suggestion="Consider replacing with a named constant"
                    ))
            
            # Long parameter list
            for func in functions:
                if func['parameters'] > 5:
                    smells.append(CodeSmell(
                        type="Long Parameter List",
                        line=func['line'],
                        description=f"Function '{func['name']}' has too many parameters ({func['parameters']})",
                        severity="medium",
                        suggestion="Consider using a struct or class to group related parameters"
                    ))
        
        return smells
    
    def extract_parameters(self, function_line: str) -> int:
        """Extract number of parameters from function signature"""
        param_match = re.search(r'\(([^)]*)\)', function_line)
        if param_match:
            params = param_match.group(1).strip()
            if not params:
                return 0
            return len([p.strip() for p in params.split(',') if p.strip()])
        return 0
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract #include dependencies"""
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', content)
        return includes
