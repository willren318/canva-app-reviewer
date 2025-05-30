"""
Code quality analyzer for Canva app files.
Focuses on code structure, performance, maintainability, and best practices.
"""

from typing import Dict, Any
from .base_analyzer import BaseAnalyzer


class CodeQualityAnalyzer(BaseAnalyzer):
    """
    Analyzes Canva app files for code quality issues including:
    - Code structure and organization
    - Performance bottlenecks
    - Best practices adherence
    - Maintainability concerns
    - Error handling
    """
    
    def get_analyzer_name(self) -> str:
        return "Code Quality Analyzer"
    
    def get_analysis_prompt(self, file_content: str, file_metadata: Dict[str, Any]) -> str:
        """Generate code quality focused analysis prompt."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        code_quality_prompt = f"""
{base_info}

As an expert code quality analyst, please analyze this Canva app file for code quality, performance, and maintainability issues.

Focus on these code quality aspects:

1. **Code Structure & Organization**:
   - Function/component complexity and size
   - Proper separation of concerns
   - Clear naming conventions
   - Code duplication and reusability
   - Import organization and dependencies

2. **Performance Issues**:
   - Inefficient algorithms or data structures
   - Memory leaks and unnecessary re-renders
   - Blocking operations on main thread
   - Large bundle size contributors
   - Expensive operations without memoization

3. **React/TypeScript Best Practices**:
   - Proper use of hooks and lifecycle methods
   - Component composition patterns
   - State management efficiency
   - Props validation and TypeScript usage
   - Key prop usage in lists

4. **Error Handling**:
   - Missing try-catch blocks
   - Unhandled promise rejections
   - Inadequate error boundaries
   - Poor error messaging
   - Silent failures

5. **Code Maintainability**:
   - Magic numbers and hardcoded values
   - Commented out code
   - TODOs and incomplete implementations
   - Overly complex conditional logic
   - Inconsistent coding patterns

6. **Canva-specific Best Practices**:
   - Proper use of Canva SDK patterns
   - Efficient data fetching from Canva APIs
   - Appropriate use of Canva design tokens
   - Following Canva app architecture guidelines

7. **Documentation & Comments**:
   - Missing or outdated documentation
   - Unclear variable/function names
   - Complex logic without explanation
   - API usage without context

8. **Testing Considerations**:
   - Code that's difficult to test
   - Missing validation that should be tested
   - Tight coupling that prevents testing
   - Side effects that complicate testing

For each code quality issue found, assess:
- Severity: critical (breaks functionality), high (significant impact), medium (moderate impact), low (minor improvement)
- Impact on maintainability and team productivity
- Performance implications
- Difficulty to fix

Prioritize issues that:
- Could cause runtime errors or crashes
- Significantly impact performance
- Make the code hard to maintain or extend
- Violate established coding standards

{self._get_response_format_instructions()}
"""
        
        return code_quality_prompt 