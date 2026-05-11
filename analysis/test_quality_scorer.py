import re
import ast
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class QualityAspect(Enum):
    COVERAGE = "coverage"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    ROBUSTNESS = "robustness"

@dataclass
class QualityScore:
    overall_score: float
    coverage_score: float
    readability_score: float
    maintainability_score: float
    performance_score: float
    robustness_score: float
    suggestions: List[str]
    strengths: List[str]
    weaknesses: List[str]

class TestQualityScorer:
    def __init__(self):
        self.weights = {
            QualityAspect.COVERAGE: 0.3,
            QualityAspect.READABILITY: 0.2,
            QualityAspect.MAINTAINABILITY: 0.2,
            QualityAspect.PERFORMANCE: 0.15,
            QualityAspect.ROBUSTNESS: 0.15
        }
    
    def score_test_suite(self, test_content: str, coverage_data: Dict[str, Any]) -> QualityScore:
        """Comprehensive test quality scoring"""
        
        # Coverage score
        coverage_score = self._score_coverage(coverage_data)
        
        # Readability score
        readability_score = self._score_readability(test_content)
        
        # Maintainability score
        maintainability_score = self._score_maintainability(test_content)
        
        # Performance score
        performance_score = self._score_performance(test_content)
        
        # Robustness score
        robustness_score = self._score_robustness(test_content)
        
        # Calculate overall score
        overall_score = (
            coverage_score * self.weights[QualityAspect.COVERAGE] +
            readability_score * self.weights[QualityAspect.READABILITY] +
            maintainability_score * self.weights[QualityAspect.MAINTAINABILITY] +
            performance_score * self.weights[QualityAspect.PERFORMANCE] +
            robustness_score * self.weights[QualityAspect.ROBUSTNESS]
        )
        
        # Generate suggestions
        suggestions, strengths, weaknesses = self._generate_feedback(
            test_content, coverage_score, readability_score, 
            maintainability_score, performance_score, robustness_score
        )
        
        return QualityScore(
            overall_score=overall_score,
            coverage_score=coverage_score,
            readability_score=readability_score,
            maintainability_score=maintainability_score,
            performance_score=performance_score,
            robustness_score=robustness_score,
            suggestions=suggestions,
            strengths=strengths,
            weaknesses=weaknesses
        )
    
    def _score_coverage(self, coverage_data: Dict[str, Any]) -> float:
        """Score test coverage"""
        coverage_percentage = coverage_data.get('overall_percentage', 0)
        
        # Base score from coverage percentage
        base_score = coverage_percentage / 100.0
        
        # Bonus for high coverage
        if coverage_percentage >= 90:
            bonus = 0.1
        elif coverage_percentage >= 80:
            bonus = 0.05
        elif coverage_percentage >= 70:
            bonus = 0.02
        else:
            bonus = 0.0
        
        return min(1.0, base_score + bonus)
    
    def _score_readability(self, test_content: str) -> float:
        """Score test code readability"""
        score = 0.5  # Base score
        lines = test_content.split('\n')
        
        # Function naming
        test_functions = re.findall(r'void\s+(\w+)\s*\(', test_content)
        good_names = sum(1 for name in test_functions if any(word in name.lower() for word in ['test', 'check', 'verify']))
        if test_functions:
            score += 0.2 * (good_names / len(test_functions))
        
        # Assertion clarity
        assertions = re.findall(r'assert\(([^)]+)\)', test_content)
        clear_assertions = sum(1 for assertion in assertions if len(str(assertion)) < 100)
        if assertions:
            score += 0.2 * (clear_assertions / len(assertions))
        
        # Comments
        comment_lines = sum(1 for line in lines if line.strip().startswith('//') or line.strip().startswith('/*'))
        if len(lines) > 0:
            comment_ratio = comment_lines / len(lines)
            if comment_ratio >= 0.1:  # At least 10% comments
                score += 0.1
        
        return min(1.0, score)
    
    def _score_maintainability(self, test_content: str) -> float:
        """Score test maintainability"""
        score = 0.5  # Base score
        
        # Test function length
        test_functions = re.finditer(r'void\s+\w+\s*\([^)]*\)\s*\{', test_content)
        for match in test_functions:
            start_pos = match.start()
            # Find matching closing brace
            brace_count = 1
            pos = match.end()
            while pos < len(test_content) and brace_count > 0:
                if test_content[pos] == '{':
                    brace_count += 1
                elif test_content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            function_content = test_content[match.start():pos]
            function_lines = len(function_content.split('\n'))
            
            # Penalize very long test functions
            if function_lines <= 20:
                score += 0.1
            elif function_lines <= 40:
                score += 0.05
            else:
                score -= 0.1
        
        # DRY principle - check for duplicated assertions
        assertions = re.findall(r'assert\([^)]+\)', test_content)
        unique_assertions = len(set(assertions))
        if assertions:
            duplication_ratio = 1 - (unique_assertions / len(assertions))
            score -= 0.2 * duplication_ratio  # Penalize duplication
        
        # Test organization
        if 'TEST(' in test_content or 'SECTION(' in test_content:
            score += 0.1  # Bonus for organized tests
        
        return min(1.0, max(0.0, score))
    
    def _score_performance(self, test_content: str) -> float:
        """Score test performance characteristics"""
        score = 0.7  # Base score - assume reasonable performance
        
        # Check for performance anti-patterns
        anti_patterns = [
            (r'sleep\(', 0.1),  # Sleep in tests
            (r'while\s*\(.*\)\s*\{', 0.05),  # Potential infinite loops
            (r'recursive', 0.05),  # Recursive tests might be slow
        ]
        
        for pattern, penalty in anti_patterns:
            if re.search(pattern, test_content):
                score -= penalty
        
        # Check for efficient testing patterns
        efficient_patterns = [
            (r'assert_eq', 0.05),  # Using assertion helpers
            (r'assert_true|assert_false', 0.05),  # Specific assertions
        ]
        
        for pattern, bonus in efficient_patterns:
            if re.search(pattern, test_content):
                score += bonus
        
        return min(1.0, max(0.0, score))
    
    def _score_robustness(self, test_content: str) -> float:
        """Score test robustness"""
        score = 0.5  # Base score
        
        # Edge case testing
        edge_case_patterns = [
            (r'0\b', 0.05),  # Zero values
            (r'-1\b', 0.05),  # Negative values
            (r'\bINT_MAX\b|int\s+\w+\s*=\s*2147483647', 0.05),  # Max values
            (r'\bnullptr\b|NULL', 0.05),  # Null pointers
            (r'empty\(\)|size\(\s*0\s*\)', 0.05),  # Empty containers
        ]
        
        for pattern, bonus in edge_case_patterns:
            if re.search(pattern, test_content):
                score += bonus
        
        # Exception handling
        if re.search(r'try\s*\{|catch\s*\(', test_content):
            score += 0.1  # Bonus for exception testing
        
        # Multiple assertion types
        assertion_types = set()
        if 'assert(' in test_content:
            assertion_types.add('assert')
        if 'assert_eq' in test_content:
            assertion_types.add('assert_eq')
        if 'assert_true' in test_content or 'assert_false' in test_content:
            assertion_types.add('assert_bool')
        
        score += 0.1 * len(assertion_types)
        
        return min(1.0, score)
    
    def _generate_feedback(self, test_content: str, coverage_score: float, 
                          readability_score: float, maintainability_score: float,
                          performance_score: float, robustness_score: float) -> Tuple[List[str], List[str], List[str]]:
        """Generate comprehensive feedback"""
        suggestions = []
        strengths = []
        weaknesses = []
        
        # Coverage feedback
        if coverage_score < 0.7:
            suggestions.append("Consider adding more test cases to improve coverage")
            weaknesses.append("Low test coverage")
        elif coverage_score >= 0.9:
            strengths.append("Excellent test coverage")
        
        # Readability feedback
        if readability_score < 0.6:
            suggestions.append("Improve test function naming and add comments")
            weaknesses.append("Poor test readability")
        elif readability_score >= 0.8:
            strengths.append("Well-written, readable tests")
        
        # Maintainability feedback
        if maintainability_score < 0.6:
            suggestions.append("Break down long test functions and reduce code duplication")
            weaknesses.append("Tests may be hard to maintain")
        elif maintainability_score >= 0.8:
            strengths.append("Well-organized, maintainable tests")
        
        # Performance feedback
        if performance_score < 0.6:
            suggestions.append("Remove performance anti-patterns from tests")
            weaknesses.append("Tests may have performance issues")
        elif performance_score >= 0.8:
            strengths.append("Efficient test implementation")
        
        # Robustness feedback
        if robustness_score < 0.6:
            suggestions.append("Add more edge case and exception testing")
            weaknesses.append("Limited robustness testing")
        elif robustness_score >= 0.8:
            strengths.append("Comprehensive edge case testing")
        
        # Specific suggestions based on content analysis
        if not re.search(r'//.*test|//.*Test', test_content):
            suggestions.append("Add comments to explain test purposes")
        
        test_functions = re.findall(r'void\s+(\w+)\s*\(', test_content)
        if test_functions and all('test' not in name.lower() for name in test_functions):
            suggestions.append("Use descriptive test function names with 'test' prefix")
        
        assertions = re.findall(r'assert\(([^)]+)\)', test_content)
        long_assertions = [a for a in assertions if len(a) > 80]
        if long_assertions:
            suggestions.append("Break down complex assertions for better readability")
        
        return suggestions, strengths, weaknesses
