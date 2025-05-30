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

As an expert security analyst, please analyze this Canva app file for security vulnerabilities and risks.

Focus on these security aspects:

1. **Cross-Site Scripting (XSS)**:
   - Unsafe use of dangerouslySetInnerHTML
   - Unescaped user input rendering
   - Dynamic script/style generation

2. **Data Security**:
   - Hardcoded secrets, API keys, tokens
   - Sensitive data exposure in logs
   - Insecure data transmission
   - Local storage of sensitive data

3. **API Security**:
   - Unsafe API calls without validation
   - Missing authentication checks
   - Improper error handling exposing internals
   - CORS misconfigurations

4. **Input Validation**:
   - Missing input sanitization
   - Unsafe regular expressions (ReDoS)
   - File upload vulnerabilities
   - Form validation bypasses

5. **Third-party Dependencies**:
   - Usage of known vulnerable packages
   - Unsafe imports or requires
   - CDN security risks

6. **Canva-specific Security**:
   - Improper use of Canva APIs
   - Missing permission checks
   - User data handling violations
   - App sandbox escapes

7. **Code Injection**:
   - Use of eval(), Function(), setTimeout with strings
   - Dynamic code generation
   - Template injection risks

For each security issue found, assess:
- Severity: critical (immediate risk), high (significant risk), medium (moderate risk), low (minor risk)
- Attack vector and exploitability
- Potential impact on users and data
- OWASP category if applicable

Prioritize issues that could:
- Expose user data or credentials
- Allow unauthorized access
- Enable code injection attacks
- Compromise app integrity

{self._get_response_format_instructions()}
"""
        
        return security_prompt 