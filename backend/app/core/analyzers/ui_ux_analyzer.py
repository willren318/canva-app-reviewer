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
        """Generate UI/UX focused analysis prompt with comprehensive Canva-specific design guidelines."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        ui_ux_prompt = f"""
{base_info}

As an expert UI/UX analyst specializing in Canva app design, analyze this file for user experience, accessibility, and design issues according to Canva's comprehensive design guidelines.

**IMPORTANT**: Focus EXCLUSIVELY on UI/UX issues. Do NOT report:
- Security vulnerabilities
- Code quality/performance issues  
- General programming practices

**COMPREHENSIVE CANVA DESIGN ANALYSIS**:

1. **Canva Design Principles Compliance**:
   - Great defaults: Does the app provide excellent design out-of-the-box without user tweaks?
   - Just simple enough: Is it understandable by non-designers, avoiding jargon and complex controls?
   - Words are design: Are labels and content clear, meaningful, and well-written?
   - Human connection: Does the tone feel personal and appropriately playful/serious?
   - Beginner to expert progression: Good first-time experience that remains engaging for repeat users?

2. **Canva Layout Guidelines**:
   - App panel constraints: Proper handling of ~350px width on desktop, full-width on mobile
   - Vertical stacking: Components arranged vertically (not in narrow columns)
   - Grid layouts: Appropriate use for image/video galleries only
   - Full-width components: Buttons and form elements use full panel width
   - No horizontal scrolling: All content fits within iframe width
   - No cropped elements: Proper padding prevents edge cropping
   - Sticky positioning: Avoided unless information must always be visible
   - Single scrollbar: No nested scrollable areas causing multiple scrollbars
   - Responsive design: Tested across different device widths

3. **Typography System (Canva Sans)**:
   - Component usage: Uses Canva's Text and Title components instead of custom typography
   - Font hierarchy: Proper use of Canva Sans Display for medium/large titles (20px, 24px), Canva Sans for small titles (14px, 16px) and body text (10px-16px)
   - Typography colors: Uses functional colors like colorTypographyTertiary, colorTypographyPlaceholder
   - Size pairing: Like-sized title and body text properly paired
   - Text emphasis: No underlining (except links), uses bold or larger font instead
   - Semantic HTML: Proper use of h1-h6, p tags through Title/Text components

4. **Written Content Standards**:
   - US spelling: Uses "realize" not "realise", "colors" not "colours", "center" not "centre"
   - Sentence case: All UI content uses sentence case, not title case
   - Second-person perspective: Uses "your designs" not "my designs"
   - File extensions: Uses uppercase without periods (GIF, PDF, HTML, JPEG)
   - URL formatting: Avoids spelling out full URLs, uses "canva.com" not "http://www.canva.com"
   - Concise language: Short sentences, simple words, avoids unnecessary modifiers
   - Clear messaging: Avoids jargon, understandable by general users

5. **Canva Color System**:
   - Functional colors: Uses Canva's role-based color system instead of custom colors
   - Theme compatibility: Proper handling of dark/light mode switching
   - Color pairing: Appropriate use of complementary functional colors (colorPrimary with colorPrimaryFore)
   - Contrast accessibility: Sufficient contrast ratios maintained automatically
   - UI Kit integration: Colors accessed through proper Canva design tokens, not direct color setting

6. **Spacing Standards**:
   - Iframe margins: 16px across all devices
   - Search bar spacing: 16px above and below
   - Related components: 8px spacing within sections (grids, carousels)
   - Section separation: 24px between different sections
   - Label consistency: 4px spacing between labels and components
   - Padding management: Uses Box component for internal spacing, layout components for between-element spacing
   - No margins on individual elements: Spacing managed by layout components

7. **Comprehensive Accessibility (WCAG 2.1)**:
   - Lighthouse audit: Passes Chrome DevTools Lighthouse accessibility audit
   - Semantic HTML: Proper use of form, table, p, h1, article elements
   - ARIA attributes: Proper aria-controls, aria-expanded, aria-labelledby for relationships
   - Interactive labels: All interactive components have proper labels, not just placeholders
   - Keyboard navigation: All interactive elements support Tab, Shift+Tab, Enter, Escape
   - Focus management: Logical focus order matching DOM order, visible focus indicators
   - Touch targets: Sufficiently large click radius for mobile
   - Media alternatives: Alt text describing onClick actions rather than just media
   - Animation controls: Stop/pause mechanism for animations over 5 seconds
   - Color contrast: WCAG 2.0 AA compliance (automatically handled by functional colors)

8. **Forms & Input Guidelines**:
   - Component usage: Uses pre-built Select, Checkbox, RadioGroup, SegmentedControl, FormField, TextInput, NumberInput, MultilineInput, FileInput
   - Label association: Proper htmlFor and id attributes linking labels to inputs
   - No placeholder reliance: Placeholders supplement, don't replace labels
   - Checkbox vs radio: Checkboxes for multiple selections, radio buttons for single selection
   - Error states: Clear error indication with helpful messages below inputs
   - Error messaging: Specific about what went wrong and how to fix it

9. **Error Handling & Messaging**:
   - Error prevention: Disables actions that would cause errors instead of showing error messages
   - Clear explanations: Avoids "unknown error" or "something went wrong", explains what failed
   - Actionable guidance: Tells users how to fix the problem or what to do next
   - Positive language: Avoids words like "error" and "problem", doesn't blame users
   - Human tone: Uses contractions (you're, we're), avoids exclamation marks
   - Appropriate specificity: Technical enough to be helpful, general enough for all users

10. **Empty States Design**:
    - Structure: Headline (Title/Small) + Body (Body/Small) + Primary action button
    - Content centering: All content centered in available space
    - Color scheme: colorTypographyPrimary for both headline and body
    - Spacing: 8px between headline and body, 16px between body and button
    - Action buttons: Uses primary button (not link button) for actions
    - No graphics: Avoids illustrations or graphics in empty states
    - Clear messaging: States what's empty and what's needed to fill the page

11. **Mobile Optimization**:
    - OS support: Supports iOS 12+ and Android 6.0+
    - Touch interactions: Optimized for finger touch, not just mouse precision
    - Low-power mode: Handles iOS requestAnimationFrame throttling
    - Content visibility: Considers "below the fold" content, updates entire screen for changes
    - Multi-step processes: Splits complex flows across separate screens for mobile
    - Real device testing: Tested on actual hardware, not just Chrome DevTools simulation
    - Bundle upload: Uses uploaded JavaScript bundle for mobile testing, not localhost

12. **Canva Component Consistency**:
    - App UI Kit: Proper use of Rows, Columns, Box, and other Canva layout components
    - Design system alignment: Maintains consistency with Canva's existing interface patterns
    - Design tokens: Uses consistent spacing, typography, and visual elements from Canva's system
    - Brand alignment: Follows Canva's visual identity and interaction patterns

For each UI/UX issue found, assess:
- Severity: critical (breaks core usability), high (significant UX impact), medium (moderate friction), low (minor improvement)
- Impact on user task completion within Canva's workflow
- Accessibility compliance level (WCAG 2.1 standards)
- Alignment with specific Canva design principles and constraints
- Mobile/responsive design considerations
- Consistency with Canva's design system

Prioritize issues that:
- Violate Canva's specific layout constraints (panel width, scrolling, spacing requirements)
- Break Canva's design system consistency (typography, colors, components)
- Create accessibility barriers (WCAG compliance failures)
- Don't follow Canva's content and messaging standards
- Impact mobile usability and cross-device consistency
- Prevent proper integration with Canva's workflow and interface

{self._get_response_format_instructions()}
"""
        
        return ui_ux_prompt 