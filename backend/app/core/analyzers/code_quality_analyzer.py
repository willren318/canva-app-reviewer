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

As an expert code quality analyst, please analyze this Canva app file ONLY for code quality, performance, and maintainability issues.

**IMPORTANT**: Focus EXCLUSIVELY on code quality aspects. Do NOT report:
- Security vulnerabilities (XSS, injection attacks, etc.)
- UI/UX design issues
- Accessibility concerns
- Business logic problems

**CODE QUALITY-FOCUSED ANALYSIS**:

1. **Code Structure & Organization**:
   - Function/component complexity and size (cyclomatic complexity)
   - Proper separation of concerns and single responsibility
   - Clear naming conventions and readability
   - Code duplication and reusability opportunities
   - Import organization and dependency management

2. **Performance Issues**:
   - Inefficient algorithms or data structures
   - Memory leaks and unnecessary re-renders
   - Blocking operations on main thread
   - Large bundle size contributors
   - Missing memoization for expensive operations

3. **React/TypeScript Best Practices**:
   - Proper use of hooks and lifecycle methods
   - Component composition patterns
   - State management efficiency
   - TypeScript usage and type safety
   - Key prop usage in lists

4. **Error Handling & Robustness**:
   - Missing try-catch blocks for error-prone operations
   - Unhandled promise rejections
   - Inadequate error boundaries
   - Poor error messaging for developers
   - Silent failures and debugging difficulties

5. **Code Maintainability**:
   - Magic numbers and hardcoded values
   - Commented out code and dead code
   - TODOs and incomplete implementations
   - Overly complex conditional logic
   - Inconsistent coding patterns

6. **Testing & Debugging**:
   - Code that's difficult to unit test
   - Tight coupling that prevents testing
   - Side effects that complicate testing
   - Missing assertions and validations
   - Poor debugging capabilities

7. **Standards & Conventions**:
   - Linting rule violations
   - Inconsistent code formatting
   - Non-standard patterns
   - Missing documentation for complex logic
   - Unclear variable/function names

8. **Canva-specific Code Quality**:
   - Proper use of Canva SDK patterns
   - Efficient data fetching from Canva APIs
   - Appropriate use of Canva design system
   - Following Canva app architecture guidelines

For each code quality issue found, assess:
- Severity: critical (breaks functionality/build), high (significant maintainability impact), medium (moderate impact), low (minor improvement)
- Impact on code maintainability and team productivity
- Performance implications
- Effort required to fix

ONLY report issues related to code structure, performance, maintainability, and best practices - NOT security vulnerabilities.

{self._get_response_format_instructions()}
"""
        
        return code_quality_prompt 