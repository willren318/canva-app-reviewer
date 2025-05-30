"""
UI & UX analyzer for Canva app files.
Focuses on user experience, accessibility, design patterns, and usability.
"""

from typing import Dict, Any
from .base_analyzer import BaseAnalyzer


class UIUXAnalyzer(BaseAnalyzer):
    """
    Analyzes Canva app files for UI/UX issues including:
    - Accessibility compliance
    - User experience patterns
    - Design consistency
    - Interaction design
    - Performance impact on UX
    """
    
    def get_analyzer_name(self) -> str:
        return "UI & UX Analyzer"
    
    def get_analysis_prompt(self, file_content: str, file_metadata: Dict[str, Any]) -> str:
        """Generate UI/UX focused analysis prompt."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        ui_ux_prompt = f"""
{base_info}

As an expert UI/UX analyst, please analyze this Canva app file for user experience, accessibility, and design issues.

Focus on these UI/UX aspects:

1. **Accessibility (WCAG 2.1 Compliance)**:
   - Missing alt text for images and icons
   - Insufficient color contrast
   - Missing ARIA labels and roles
   - Keyboard navigation support
   - Screen reader compatibility
   - Focus management and visual indicators

2. **User Experience Patterns**:
   - Intuitive navigation and information architecture
   - Clear user feedback and status indicators
   - Appropriate loading states and error messages
   - Consistent interaction patterns
   - Logical workflow and user journey

3. **Design Consistency**:
   - Consistent spacing, typography, and colors
   - Proper use of Canva design system components
   - Brand alignment with Canva guidelines
   - Visual hierarchy and layout structure
   - Responsive design considerations

4. **Interaction Design**:
   - Button states and hover effects
   - Form validation and user guidance
   - Drag and drop usability
   - Touch targets and mobile optimization
   - Animation and transition appropriateness

5. **Performance Impact on UX**:
   - Smooth animations and transitions
   - Fast rendering and response times
   - Efficient image and asset loading
   - Progressive enhancement strategies
   - Perceived performance optimizations

6. **Canva-specific UX Guidelines**:
   - Integration with Canva's design workflow
   - Consistency with Canva's interaction patterns
   - Proper use of Canva's design tokens and themes
   - Seamless embedding within Canva interface
   - Following Canva's content and tone guidelines

7. **Information Architecture**:
   - Clear content hierarchy and organization
   - Scannable and digestible information layout
   - Appropriate use of headings and structure
   - Logical grouping of related elements
   - Effective use of white space

8. **User Input & Forms**:
   - Clear labeling and instructions
   - Appropriate input types and validation
   - Helpful error messages and recovery
   - Progress indication for multi-step processes
   - Auto-completion and user assistance

9. **Mobile & Touch Experience**:
   - Touch-friendly interface elements
   - Appropriate gesture support
   - Mobile-optimized layouts
   - Thumb-friendly navigation zones
   - Cross-device consistency

For each UI/UX issue found, assess:
- Severity: critical (breaks usability), high (significant UX impact), medium (moderate impact), low (minor improvement)
- Impact on user satisfaction and task completion
- Accessibility compliance level
- Alignment with Canva design principles

Prioritize issues that:
- Prevent users from completing core tasks
- Create accessibility barriers
- Cause confusion or frustration
- Break established design patterns
- Impact user trust and confidence

{self._get_response_format_instructions()}
"""
        
        return ui_ux_prompt 