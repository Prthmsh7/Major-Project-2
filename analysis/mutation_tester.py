import os
import re
import subprocess
import tempfile
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class MutationType(Enum):
    ARITHMETIC = "arithmetic"
    LOGICAL = "logical"
    CONDITIONAL = "conditional"
    ASSIGNMENT = "assignment"
    RETURN = "return"
    UNARY = "unary"

@dataclass
class Mutation:
    type: MutationType
    line: int
    original: str
    mutated: str
    description: str

@dataclass
class MutationResult:
    mutation: Mutation
    killed: bool
    test_output: str
    error_output: str

class MutationTester:
    def __init__(self, source_file: str, test_file: str):
        self.source_file = source_file
        self.test_file = test_file
        self.source_content = None
        self.mutations = []
        
    def load_source(self):
        """Load the source file content"""
        with open(self.source_file, 'r', encoding='utf-8') as f:
            self.source_content = f.read()
    
    def generate_mutations(self) -> List[Mutation]:
        """Generate all possible mutations for the source code"""
        self.load_source()
        mutations = []
        lines = self.source_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # Arithmetic mutations
            mutations.extend(self._generate_arithmetic_mutations(i, line))
            
            # Logical mutations
            mutations.extend(self._generate_logical_mutations(i, line))
            
            # Conditional mutations
            mutations.extend(self._generate_conditional_mutations(i, line))
            
            # Assignment mutations
            mutations.extend(self._generate_assignment_mutations(i, line))
            
            # Return mutations
            mutations.extend(self._generate_return_mutations(i, line))
            
            # Unary mutations
            mutations.extend(self._generate_unary_mutations(i, line))
        
        self.mutations = mutations
        return mutations
    
    def _generate_arithmetic_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate arithmetic operator mutations"""
        mutations = []
        operators = ['+', '-', '*', '/', '%']
        
        for op in operators:
            if op in line:
                # Replace with other operators
                replacements = {'+': '-', '-': '+', '*': '/', '/': '*', '%': '+'}
                if op in replacements:
                    mutated_line = line.replace(op, replacements[op])
                    mutations.append(Mutation(
                        type=MutationType.ARITHMETIC,
                        line=line_num,
                        original=line,
                        mutated=mutated_line,
                        description=f"Changed '{op}' to '{replacements[op]}'"
                    ))
        
        return mutations
    
    def _generate_logical_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate logical operator mutations"""
        mutations = []
        
        if '&&' in line:
            mutations.append(Mutation(
                type=MutationType.LOGICAL,
                line=line_num,
                original=line,
                mutated=line.replace('&&', '||'),
                description="Changed '&&' to '||'"
            ))
        
        if '||' in line:
            mutations.append(Mutation(
                type=MutationType.LOGICAL,
                line=line_num,
                original=line,
                mutated=line.replace('||', '&&'),
                description="Changed '||' to '&&'"
            ))
        
        return mutations
    
    def _generate_conditional_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate conditional operator mutations"""
        mutations = []
        
        # Relational operators
        operators = ['<', '>', '<=', '>=', '==', '!=']
        replacements = {'<': '>=', '>': '<=', '<=': '>', '>=': '<', '==': '!=', '!=': '=='}
        
        for op in operators:
            if op in line:
                mutated_line = line.replace(op, replacements[op])
                mutations.append(Mutation(
                    type=MutationType.CONDITIONAL,
                    line=line_num,
                    original=line,
                    mutated=mutated_line,
                    description=f"Changed '{op}' to '{replacements[op]}'"
                ))
        
        return mutations
    
    def _generate_assignment_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate assignment operator mutations"""
        mutations = []
        
        if '=' in line and not any(op in line for op in ['==', '!=', '<=', '>=']):
            # Replace assignment with other assignment operators
            replacements = ['+=', '-=', '*=', '/=']
            for repl in replacements:
                if repl not in line:  # Avoid creating compound assignments that don't make sense
                    mutated_line = line.replace('=', repl, 1)
                    mutations.append(Mutation(
                        type=MutationType.ASSIGNMENT,
                        line=line_num,
                        original=line,
                        mutated=mutated_line,
                        description=f"Changed '=' to '{repl}'"
                    ))
        
        return mutations
    
    def _generate_return_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate return statement mutations"""
        mutations = []
        
        if 'return' in line and 'return 0' in line:
            # Change return 0 to return 1
            mutated_line = line.replace('return 0', 'return 1')
            mutations.append(Mutation(
                type=MutationType.RETURN,
                line=line_num,
                original=line,
                mutated=mutated_line,
                description="Changed 'return 0' to 'return 1'"
            ))
        
        if 'return true' in line:
            mutated_line = line.replace('return true', 'return false')
            mutations.append(Mutation(
                type=MutationType.RETURN,
                line=line_num,
                original=line,
                mutated=mutated_line,
                description="Changed 'return true' to 'return false'"
            ))
        
        if 'return false' in line:
            mutated_line = line.replace('return false', 'return true')
            mutations.append(Mutation(
                type=MutationType.RETURN,
                line=line_num,
                original=line,
                mutated=mutated_line,
                description="Changed 'return false' to 'return true'"
            ))
        
        return mutations
    
    def _generate_unary_mutations(self, line_num: int, line: str) -> List[Mutation]:
        """Generate unary operator mutations"""
        mutations = []
        
        # Negate boolean conditions
        if '!' in line and '!=' not in line:
            # Remove negation
            mutated_line = line.replace('!', '', 1)
            mutations.append(Mutation(
                type=MutationType.UNARY,
                line=line_num,
                original=line,
                mutated=mutated_line,
                description="Removed '!' operator"
            ))
        
        return mutations
    
    def apply_mutation(self, mutation: Mutation) -> str:
        """Apply a single mutation to create a mutated version"""
        lines = self.source_content.split('\n')
        lines[mutation.line - 1] = mutation.mutated
        return '\n'.join(lines)
    
    def run_mutation_test(self, mutation: Mutation) -> MutationResult:
        """Run tests with a mutated version of the code"""
        # Create temporary mutated file
        mutated_content = self.apply_mutation(mutation)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as temp_file:
            temp_file.write(mutated_content)
            temp_source = temp_file.name
        
        try:
            # Compile mutated source with test file
            work_dir = os.path.dirname(self.source_file)
            compile_cmd = ['g++', '-std=c++11', '-O0', '-g', 
                          os.path.basename(temp_source), 
                          os.path.basename(self.test_file), 
                          '-o', 'mutated_test']
            
            result = subprocess.run(compile_cmd, cwd=work_dir, 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return MutationResult(
                    mutation=mutation,
                    killed=False,
                    test_output="",
                    error_output=f"Compilation failed: {result.stderr}"
                )
            
            # Run the tests
            test_cmd = ['./mutated_test']
            result = subprocess.run(test_cmd, cwd=work_dir, 
                                  capture_output=True, text=True, timeout=30)
            
            # Mutation is killed if tests fail (different behavior from original)
            killed = result.returncode != 0 or "All tests passed" not in result.stdout
            
            return MutationResult(
                mutation=mutation,
                killed=killed,
                test_output=result.stdout,
                error_output=result.stderr
            )
            
        except subprocess.TimeoutExpired:
            return MutationResult(
                mutation=mutation,
                killed=False,
                test_output="",
                error_output="Test execution timed out"
            )
        
        finally:
            # Clean up temporary files
            if os.path.exists(temp_source):
                os.unlink(temp_source)
            
            mutated_exe = os.path.join(os.path.dirname(self.source_file), 'mutated_test')
            if os.path.exists(mutated_exe):
                os.unlink(mutated_exe)
    
    def run_mutation_analysis(self, max_mutations: int = 50) -> Dict[str, Any]:
        """Run complete mutation analysis"""
        mutations = self.generate_mutations()
        
        # Limit mutations to avoid excessive runtime
        if len(mutations) > max_mutations:
            mutations = mutations[:max_mutations]
        
        results = []
        killed_count = 0
        
        for mutation in mutations:
            result = self.run_mutation_test(mutation)
            results.append(result)
            if result.killed:
                killed_count += 1
        
        # Calculate mutation score
        mutation_score = (killed_count / len(mutations)) * 100 if mutations else 0
        
        # Group results by mutation type
        results_by_type = {}
        for result in results:
            mut_type = result.mutation.type.value
            if mut_type not in results_by_type:
                results_by_type[mut_type] = []
            results_by_type[mut_type].append(result)
        
        return {
            'total_mutations': len(mutations),
            'killed_mutations': killed_count,
            'mutation_score': mutation_score,
            'results': results,
            'results_by_type': results_by_type,
            'survived_mutations': [r for r in results if not r.killed]
        }
