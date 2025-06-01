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
        """Generate security-focused analysis prompt with Canva-specific guidelines."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        security_prompt = f"""
{base_info}

As an expert security analyst specializing in Canva app security, analyze this file for vulnerabilities according to Canva's specific security requirements.

**IMPORTANT**: Focus EXCLUSIVELY on security issues. Do NOT report:
- Code quality issues (poor error handling, missing types, etc.)
- Performance problems
- UI/UX concerns
- General coding best practices

**CANVA-SPECIFIC SECURITY ANALYSIS**:

1. **Content Security Policy Violations**:
   - Loading JavaScript from third-party sources (PROHIBITED)
   - Using frames, web workers, or nested browsing contexts (PROHIBITED)
   - Loading external CSS stylesheets (PROHIBITED)
   - Using the `base` element (PROHIBITED)
   - Using the `form` element's `action` attribute (PROHIBITED)
   - Improper handling of form submissions (should use onSubmit with preventDefault)

2. **Cross-Origin Resource Sharing Issues**:
   - Frontend assumes incorrect origin (should use https://app-CANVA_APP_ID.canva-apps.com)
   - Missing or insufficient CORS handling in backend code
   - Not handling preflight (OPTIONS) requests properly
   - Lack of proper Access-Control-Allow-Origin headers

3. **Authentication & HTTP Request Verification**:
   - Not requesting JWT from Canva before making backend calls
   - Missing JWT verification in backend requests
   - Not including JWT in Authorization header (Bearer token format)
   - Not validating required JWT properties (aud, brandId, userId)
   - Improper token handling or exposure

4. **Data Security**:
   - Hardcoded secrets, API keys, tokens
   - Sensitive data exposure in logs or console
   - Insecure data transmission (HTTP vs HTTPS)
   - Local storage of sensitive data without encryption

5. **Code Injection Vulnerabilities**:
   - Use of eval(), Function(), setTimeout with dynamic strings
   - Dynamic code generation with user input
   - Template injection risks

6. **Cross-Site Scripting (XSS)**:
   - Unsafe use of dangerouslySetInnerHTML or innerHTML
   - Unescaped user input rendering
   - Dynamic script/style generation with user data

7. **Input Validation Security**:
   - Missing input sanitization leading to security issues
   - Unsafe regular expressions (ReDoS attacks)
   - File upload security vulnerabilities
   - Form validation bypasses with security implications

8. **Third-party Dependencies**:
   - Usage of known vulnerable packages
   - Supply chain security risks
   - Unauthorized external API calls

For each security issue found, assess:
- Severity: critical (immediate exploitable vulnerability), high (significant security risk), medium (moderate security concern), low (minor security issue)
- Attack vector and exploitability
- Potential impact on user data, privacy, or system integrity
- Specific Canva security policy violated

ONLY report issues that have actual security implications, not general code quality problems.

{self._get_response_format_instructions()}
"""
        
        return security_prompt 