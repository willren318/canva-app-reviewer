"""
UI & UX analyzer for Canva app files.
Focuses on user experience, accessibility, design patterns, and usability.
Enhanced with visual analysis using screenshots.
"""

import asyncio
from typing import Dict, Any, List
from .base_analyzer import BaseAnalyzer
from ...utils.js_screenshot_utils import capture_js_app_screenshot
from ...config import settings
import logging

logger = logging.getLogger(__name__)


class UIUXAnalyzer(BaseAnalyzer):
    """
    Analyzes Canva app files for UI/UX issues including:
    - Accessibility compliance
    - User experience patterns
    - Design consistency
    - Interaction design
    - Performance impact on UX
    - Visual design quality (via screenshots)
    """
    
    def get_analyzer_name(self) -> str:
        return "UI & UX Analyzer"
    
    async def analyze(self, file_content: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced analyze method that captures screenshots for visual analysis.
        Uses the new JavaScript-only screenshot system for .js files only.
        For .jsx/.tsx files, falls back to code-only analysis.
        """
        try:
            file_name = file_metadata.get('file_name', 'canva-app.js')
            file_extension = file_metadata.get('file_extension', '.js').lower()
            
            # Only use JavaScript screenshot system for .js files
            if file_extension == '.js':
                logger.info(f"Using JavaScript screenshot system for .js file: {file_name}")
                
                # Capture screenshot using the new JavaScript-only system
                logger.info(f"Capturing screenshot for visual analysis: {file_name}")
                screenshot_base64, visual_metrics = await capture_js_app_screenshot(
                    file_content, file_name, save_debug=True
                )
                
                # Generate the analysis prompt with visual context
                prompt = self.get_analysis_prompt(file_content, file_metadata, screenshot_base64, visual_metrics)
                
                # Analyze with Claude (including image if available)
                result = await self._analyze_with_claude(prompt, screenshot_base64)
                
                # Add visual metrics to the result
                if 'metadata' not in result:
                    result['metadata'] = {}
                result['metadata']['visual_analysis'] = {
                    'screenshot_captured': screenshot_base64 is not None,
                    'visual_metrics': visual_metrics,
                    'system_used': 'javascript_only',
                    'file_type': 'js'
                }
                
                return result
                
            else:
                # For .jsx/.tsx files, fall back to code-only analysis
                logger.info(f"Using code-only analysis for {file_extension} file: {file_name}")
                logger.info(f"JavaScript screenshot system only supports .js files. JSX/TSX requires transpilation.")
                
                return await self._fallback_code_analysis(file_content, file_metadata, reason="jsx_tsx_not_supported")
            
        except Exception as e:
            logger.error(f"UI/UX analysis failed: {str(e)}")
            # Fallback to code-only analysis
            return await self._fallback_code_analysis(file_content, file_metadata, reason="error")
    
    async def _analyze_with_claude(self, prompt: str, screenshot_base64: str = None) -> Dict[str, Any]:
        """
        Analyze with Claude, including image if available.
        """
        try:
            # Prepare messages for Claude
            messages = [{"role": "user", "content": []}]
            
            # Add text prompt
            messages[0]["content"].append({
                "type": "text", 
                "text": prompt
            })
            
            # Add screenshot if available
            if screenshot_base64:
                messages[0]["content"].append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot_base64
                    }
                })
                logger.info("Including screenshot in Claude analysis")
            
            # Call Claude API with multimodal input
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=4000,
                messages=messages
            )
            
            response_text = response.content[0].text
            
            # Debug logging for development/testing (same as base analyzer)
            logger.info(f"=== {self.get_analyzer_name()} Claude Response ===")
            logger.info(f"Model: {settings.claude_model}")
            logger.info(f"Response length: {len(response_text)} characters")
            logger.info(f"Raw response: {response_text[:500]}{'...' if len(response_text) > 500 else ''}")
            logger.info("=" * 50)
            
            # Also print to console for debugging
            print(f"\n🤖 === {self.get_analyzer_name()} Claude Response ===")
            print(f"📱 Model: {settings.claude_model}")
            print(f"📏 Length: {len(response_text)} characters")
            print(f"📄 Full Response:")
            print(response_text)
            print("=" * 50)
            
            # Parse Claude's response
            return self._parse_claude_response(response_text)
            
        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            raise
    
    async def _fallback_code_analysis(self, file_content: str, file_metadata: Dict[str, Any], reason: str = "unknown") -> Dict[str, Any]:
        """
        Fallback to code-only analysis if screenshot capture fails or for unsupported file types.
        """
        file_extension = file_metadata.get('file_extension', '.js').lower()
        
        if reason == "jsx_tsx_not_supported":
            logger.warning(f"Code-only analysis for {file_extension} file - JavaScript screenshot system only supports .js files")
        else:
            logger.warning(f"Falling back to code-only analysis. Reason: {reason}")
        
        prompt = self.get_analysis_prompt(file_content, file_metadata)
        
        try:
            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            
            # Debug logging for code-only analysis
            logger.info(f"=== {self.get_analyzer_name()} Claude Response (Code-Only) ===")
            logger.info(f"Model: {settings.claude_model}")
            logger.info(f"Response length: {len(response_text)} characters")
            logger.info(f"Raw response: {response_text[:500]}{'...' if len(response_text) > 500 else ''}")
            logger.info("=" * 50)
            
            # Also print to console for debugging
            print(f"\n🤖 === {self.get_analyzer_name()} Claude Response (Code-Only) ===")
            print(f"📱 Model: {settings.claude_model}")
            print(f"📏 Length: {len(response_text)} characters")
            print(f"📋 Analysis Type: Code-only ({reason})")
            print(f"📄 Full Response:")
            print(response_text)
            print("=" * 50)
            
            result = self._parse_claude_response(response_text)
            
            # Add appropriate metadata based on reason
            metadata = {
                'visual_analysis': {
                    'screenshot_captured': False,
                    'reason': reason,
                    'file_type': file_extension[1:] if file_extension.startswith('.') else file_extension
                }
            }
            
            if reason == "jsx_tsx_not_supported":
                metadata['visual_analysis'].update({
                    'system_used': 'code_only',
                    'note': f'{file_extension.upper()} files require transpilation - only .js files support direct screenshot capture',
                    'suggestion': 'Convert to vanilla JavaScript (.js) for visual analysis support'
                })
            else:
                metadata['visual_analysis'].update({
                    'system_used': 'code_only_fallback',
                    'note': 'Screenshot capture failed, using code-only analysis'
                })
            
            result['metadata'] = metadata
            return result
            
        except Exception as e:
            logger.error(f"Fallback analysis failed: {str(e)}")
            return self._create_error_result(str(e))
    
    def get_analysis_prompt(self, file_content: str, file_metadata: Dict[str, Any], 
                          screenshot_base64: str = None, visual_metrics: Dict[str, Any] = None) -> str:
        """Generate UI/UX focused analysis prompt with comprehensive Canva-specific design guidelines and visual analysis."""
        
        base_info = self._build_base_prompt(file_content, file_metadata)
        
        # Visual context information
        visual_context = ""
        if screenshot_base64:
            visual_context = f"""
**VISUAL ANALYSIS CONTEXT**:
I have captured a screenshot of your rendered Canva app which shows how it actually appears to users. 
The visual preview simulates the Canva app panel (350px width) with typical Canva styling.

Visual Metrics:
{f"- Dimensions: {visual_metrics.get('dimensions', 'N/A')}" if visual_metrics else ""}
{f"- Visual Complexity: {visual_metrics.get('visual_complexity', 'N/A')}" if visual_metrics else ""}
{f"- Whitespace Ratio: {visual_metrics.get('whitespace_ratio', 'N/A'):.2f}" if visual_metrics and 'whitespace_ratio' in visual_metrics else ""}
{f"- Unique Colors: {visual_metrics.get('unique_colors', 'N/A')}" if visual_metrics else ""}

Please analyze BOTH the code AND the visual appearance in the screenshot to provide comprehensive UI/UX feedback.
"""
        
        ui_ux_prompt = f"""
{base_info}

{visual_context}

As an expert UI/UX analyst specializing in Canva app design, analyze this file for user experience, accessibility, and design issues according to Canva's comprehensive design guidelines.

**IMPORTANT**: Focus EXCLUSIVELY on UI/UX issues. Do NOT report:
- Security vulnerabilities
- Code quality/performance issues  
- General programming practices

**COMPREHENSIVE CANVA DESIGN ANALYSIS**:

1. **Visual Design Assessment** (if screenshot available):
   - Overall visual appeal and professional appearance
   - Color scheme consistency with Canva's design language
   - Visual hierarchy and information architecture
   - Button and element spacing and alignment
   - Typography consistency and readability
   - Appropriate use of whitespace and breathing room
   - Visual clutter or overcrowding issues
   - Consistency with Canva's App UI Kit styling

2. **Canva Design Principles Compliance**:
   - Great defaults: Does the app provide excellent design out-of-the-box without user tweaks?
   - Just simple enough: Is it understandable by non-designers, avoiding jargon and complex controls?
   - Words are design: Are labels and content clear, meaningful, and well-written?
   - Human connection: Does the tone feel personal and appropriately playful/serious?
   - Beginner to expert progression: Good first-time experience that remains engaging for repeat users?

3. **Canva Layout Guidelines**:
   - App panel constraints: Proper handling of ~350px width on desktop, full-width on mobile
   - Vertical stacking: Components arranged vertically (not in narrow columns)
   - Grid layouts: Appropriate use for image/video galleries only
   - Full-width components: Buttons and form elements use full panel width
   - No horizontal scrolling: All content fits within iframe width
   - No cropped elements: Proper padding prevents edge cropping
   - Sticky positioning: Avoided unless information must always be visible
   - Single scrollbar: No nested scrollable areas causing multiple scrollbars
   - Responsive design: Tested across different device widths

4. **Typography System (Canva Sans)**:
   - Component usage: Uses Canva's Text and Title components instead of custom typography
   - Font hierarchy: Proper use of Canva Sans Display for medium/large titles (20px, 24px), Canva Sans for small titles (14px, 16px) and body text (10px-16px)
   - Typography colors: Uses functional colors like colorTypographyTertiary, colorTypographyPlaceholder
   - Size pairing: Like-sized title and body text properly paired
   - Text emphasis: No underlining (except links), uses bold or larger font instead
   - Semantic HTML: Proper use of h1-h6, p tags through Title/Text components

5. **Written Content Standards**:
   - US spelling: Uses "realize" not "realise", "colors" not "colours", "center" not "centre"
   - Sentence case: All UI content uses sentence case, not title case
   - Second-person perspective: Uses "your designs" not "my designs"
   - File extensions: Uses uppercase without periods (GIF, PDF, HTML, JPEG)
   - URL formatting: Avoids spelling out full URLs, uses "canva.com" not "http://www.canva.com"
   - Concise language: Short sentences, simple words, avoids unnecessary modifiers
   - Clear messaging: Avoids jargon, understandable by general users

6. **Canva Color System**:
   - Functional colors: Uses Canva's role-based color system instead of custom colors
   - Theme compatibility: Proper handling of dark/light mode switching
   - Color pairing: Appropriate use of complementary functional colors (colorPrimary with colorPrimaryFore)
   - Contrast accessibility: Sufficient contrast ratios maintained automatically
   - UI Kit integration: Colors accessed through proper Canva design tokens, not direct color setting

7. **Spacing Standards**:
   - Iframe margins: 16px across all devices
   - Search bar spacing: 16px above and below
   - Related components: 8px spacing within sections (grids, carousels)
   - Section separation: 24px between different sections
   - Label consistency: 4px spacing between labels and components
   - Padding management: Uses Box component for internal spacing, layout components for between-element spacing
   - No margins on individual elements: Spacing managed by layout components

8. **Comprehensive Accessibility (WCAG 2.1)**:
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

9. **Forms & Input Guidelines**:
   - Component usage: Uses pre-built Select, Checkbox, RadioGroup, SegmentedControl, FormField, TextInput, NumberInput, MultilineInput, FileInput
   - Label association: Proper htmlFor and id attributes linking labels to inputs
   - No placeholder reliance: Placeholders supplement, don't replace labels
   - Checkbox vs radio: Checkboxes for multiple selections, radio buttons for single selection
   - Error states: Clear error indication with helpful messages below inputs
   - Error messaging: Specific about what went wrong and how to fix it

10. **Error Handling & Messaging**:
    - Error prevention: Disables actions that would cause errors instead of showing error messages
    - Clear explanations: Avoids "unknown error" or "something went wrong", explains what failed
    - Actionable guidance: Tells users how to fix the problem or what to do next
    - Positive language: Avoids words like "error" and "problem", doesn't blame users
    - Human tone: Uses contractions (you're, we're), avoids exclamation marks
    - Appropriate specificity: Technical enough to be helpful, general enough for all users

11. **Empty States Design**:
    - Structure: Headline (Title/Small) + Body (Body/Small) + Primary action button
    - Content centering: All content centered in available space
    - Color scheme: colorTypographyPrimary for both headline and body
    - Spacing: 8px between headline and body, 16px between body and button
    - Action buttons: Uses primary button (not link button) for actions
    - No graphics: Avoids illustrations or graphics in empty states
    - Clear messaging: States what's empty and what's needed to fill the page

12. **Mobile Optimization**:
    - OS support: Supports iOS 12+ and Android 6.0+
    - Touch interactions: Optimized for finger touch, not just mouse precision
    - Low-power mode: Handles iOS requestAnimationFrame throttling
    - Content visibility: Considers "below the fold" content, updates entire screen for changes
    - Multi-step processes: Splits complex flows across separate screens for mobile
    - Real device testing: Tested on actual hardware, not just Chrome DevTools simulation
    - Bundle upload: Uses uploaded JavaScript bundle for mobile testing, not localhost

13. **Canva Component Consistency**:
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
- Visual appearance issues (if screenshot is provided)

Prioritize issues that:
- Violate Canva's specific layout constraints (panel width, scrolling, spacing requirements)
- Break Canva's design system consistency (typography, colors, components)
- Create accessibility barriers (WCAG compliance failures)
- Don't follow Canva's content and messaging standards
- Impact mobile usability and cross-device consistency
- Prevent proper integration with Canva's workflow and interface
- Have poor visual design or don't match Canva's aesthetic (based on screenshot)

{self._get_response_format_instructions()}
"""
        
        return ui_ux_prompt 
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        Create an error result when analysis fails.
        """
        return {
            "score": 0,
            "issues": [
                {
                    "severity": "critical",
                    "title": "Analysis Failed",
                    "description": f"UI/UX analysis could not be completed: {error_message}",
                    "line_number": None,
                    "code_snippet": None,
                    "recommendation": "Please check the file format and try again."
                }
            ],
            "recommendations": [
                "Ensure the file is a valid JavaScript or TypeScript React component",
                "Check that the file syntax is correct",
                "Try uploading the file again"
            ],
            "metadata": {
                "analyzer": self.get_analyzer_name(),
                "version": self.get_version(),
                "error": error_message,
                "visual_analysis": {"screenshot_captured": False}
            }
        } 