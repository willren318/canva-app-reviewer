"""
Security analyzer for Canva app files.
Focuses on security vulnerabilities, unsafe practices, and data protection.
"""

from typing import Dict, Any
from .base_analyzer import BaseAnalyzer


class SecurityAnalyzer(BaseAnalyzer):
    """
    Analyzes Canva app files for security issues including:
    - XSS vulnerabilities
    - Unsafe API usage
    - Data exposure risks
    - Authentication issues
    - Input validation problems
    """
    
    def get_analyzer_name(self) -> str:
        return "Security Analyzer"
    
    def get_analysis_prompt(self, file_content: str, file_metadata: Dict[str, Any]) -> str:
        """Generate security-focused analysis prompt."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        security_prompt = f"""
{base_info}

As an expert security analyst, please analyze this Canva app file ONLY for security vulnerabilities and risks.

**IMPORTANT**: Focus EXCLUSIVELY on security issues. Do NOT report:
- Code quality issues (poor error handling, missing types, etc.)
- Performance problems
- UI/UX concerns
- General coding best practices

**SECURITY-FOCUSED ANALYSIS**:

1. **Cross-Site Scripting (XSS)**:
   - Unsafe use of dangerouslySetInnerHTML or innerHTML
   - Unescaped user input rendering
   - Dynamic script/style generation with user data

2. **Data Security**:
   - Hardcoded secrets, API keys, tokens
   - Sensitive data exposure in logs or console
   - Insecure data transmission (HTTP vs HTTPS)
   - Local storage of sensitive data without encryption

3. **Code Injection Vulnerabilities**:
   - Use of eval(), Function(), setTimeout with dynamic strings
   - Dynamic code generation with user input
   - Template injection risks

4. **Authentication & Authorization**:
   - Missing authentication checks
   - Improper session handling
   - Privilege escalation risks
   - Token exposure or misuse

5. **Input Validation Security**:
   - Missing input sanitization leading to security issues
   - Unsafe regular expressions (ReDoS attacks)
   - File upload security vulnerabilities
   - Form validation bypasses with security implications

6. **Third-party Security Risks**:
   - Usage of known vulnerable packages
   - Unsafe imports or CDN usage
   - Supply chain security risks

7. **Canva-specific Security**:
   - Improper use of Canva APIs that could expose data
   - Missing permission checks for sensitive operations
   - User data handling violations
   - App sandbox security violations

For each security issue found, assess:
- Severity: critical (immediate exploitable vulnerability), high (significant security risk), medium (moderate security concern), low (minor security issue)
- Attack vector and exploitability
- Potential impact on user data, privacy, or system integrity
- OWASP category if applicable

ONLY report issues that have actual security implications, not general code quality problems.

{self._get_response_format_instructions()}
"""
        
        return security_prompt 