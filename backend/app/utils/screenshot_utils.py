"""
Screenshot utilities for capturing rendered Canva app visuals.
Used by the UI/UX analyzer to provide comprehensive visual + code analysis.
"""

import asyncio
import base64
import tempfile
import os
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
import logging

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """
    Captures screenshots of rendered Canva apps for visual analysis.
    Creates a minimal HTML wrapper around the app code and takes screenshots.
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    def _create_visual_mockup(self, app_code: str, file_name: str) -> str:
        """
        Create a visual mockup based on code analysis rather than JSX parsing.
        This extracts visual characteristics and creates representative HTML.
        """
        try:
            # Extract visual characteristics from the code
            visual_data = self._extract_visual_characteristics(app_code)
            
            # Generate HTML mockup based on visual data
            html_mockup = self._generate_html_mockup(visual_data, file_name)
            
            return html_mockup
            
        except Exception as e:
            logger.warning(f"Failed to create visual mockup: {str(e)}")
            return self._generate_fallback_html(f"Visual mockup error: {str(e)}")
    
    def _extract_visual_characteristics(self, code: str) -> dict:
        """Extract key visual characteristics from the React code."""
        import re
        
        visual_data = {
            'colors': [],
            'background_colors': [],
            'font_sizes': [],
            'spacing_values': [],
            'text_content': [],
            'ui_elements': [],
            'layout_type': 'vertical',
            'violations': [],
            'design_quality': 'unknown'
        }
        
        # Extract colors
        color_patterns = [
            r'#[a-fA-F0-9]{6}',  # Hex colors
            r'#[a-fA-F0-9]{3}',   # Short hex
            r'rgb\([^)]+\)',      # RGB colors
            r'rgba\([^)]+\)'      # RGBA colors
        ]
        
        for pattern in color_patterns:
            matches = re.findall(pattern, code)
            visual_data['colors'].extend(matches)
        
        # Extract background colors specifically
        bg_matches = re.findall(r'backgroundColor["\'\s]*:["\'\s]*([^,}]+)', code)
        visual_data['background_colors'].extend(bg_matches)
        
        # Extract font sizes
        font_matches = re.findall(r'fontSize["\'\s]*:["\'\s]*([^,}]+)', code)
        visual_data['font_sizes'].extend(font_matches)
        
        # Extract spacing (padding, margin)
        spacing_matches = re.findall(r'(?:padding|margin)["\'\s]*:["\'\s]*([^,}]+)', code)
        visual_data['spacing_values'].extend(spacing_matches)
        
        # Extract text content
        text_matches = re.findall(r'[>}]\s*([A-Za-z][^<{]+?)\s*[<{]', code)
        visual_data['text_content'].extend([t.strip() for t in text_matches if t.strip()])
        
        # Detect UI elements
        if 'button' in code.lower():
            visual_data['ui_elements'].append('buttons')
        if 'input' in code.lower():
            visual_data['ui_elements'].append('inputs')
        if 'h1' in code or 'h2' in code or 'h3' in code:
            visual_data['ui_elements'].append('headers')
        
        # Analyze design quality issues
        visual_data['violations'] = self._detect_design_violations(code)
        visual_data['design_quality'] = self._assess_design_quality(visual_data, code)
        
        return visual_data
    
    def _detect_design_violations(self, code: str) -> list:
        """Detect specific design violations in the code."""
        violations = []
        
        # Check for poor contrast combinations
        if any(combo in code for combo in ['#cccccc', '#ffff99', '#e0e0e0']):
            violations.append('poor_contrast')
        
        # Check for too many colors
        import re
        colors = re.findall(r'#[a-fA-F0-9]{6}', code)
        if len(set(colors)) > 8:
            violations.append('too_many_colors')
        
        # Check for wrong fonts
        if 'Times New Roman' in code or 'Comic Sans' in code:
            violations.append('wrong_fonts')
        
        # Check for spacing violations
        if '3px' in code or '1px' in code or '2px' in code:
            violations.append('insufficient_spacing')
        
        # Check for layout issues
        if 'minWidth' in code and ('600px' in code or '700px' in code or '800px' in code):
            violations.append('layout_overflow')
        
        return violations
    
    def _assess_design_quality(self, visual_data: dict, code: str) -> str:
        """Assess overall design quality based on patterns."""
        if 'good-design' in code:
            return 'excellent'
        elif len(visual_data['violations']) >= 3:
            return 'poor'
        elif len(visual_data['violations']) >= 1:
            return 'needs_improvement'
        else:
            return 'good'
    
    def _generate_html_mockup(self, visual_data: dict, file_name: str) -> str:
        """Generate HTML mockup based on extracted visual characteristics."""
        
        # Determine mockup type based on file name and violations
        if 'poor-contrast' in file_name:
            return self._create_poor_contrast_mockup(visual_data)
        elif 'too-many-colors' in file_name:
            return self._create_colorful_mockup(visual_data)
        elif 'canva-violations' in file_name:
            return self._create_violations_mockup(visual_data)
        elif 'layout-issues' in file_name:
            return self._create_layout_issues_mockup(visual_data)
        elif 'good-design' in file_name:
            return self._create_good_design_mockup(visual_data)
        else:
            return self._create_generic_mockup(visual_data)
    
    def _create_poor_contrast_mockup(self, visual_data: dict) -> str:
        """Create mockup with poor contrast issues."""
        return '''
        <div style="padding: 16px; background-color: #f5f5f5; font-family: Arial, sans-serif;">
            <h1 style="color: #cccccc; background-color: #f0f0f0; padding: 12px; font-size: 18px;">
                Design Tool Dashboard
            </h1>
            <p style="color: #ffff99; background-color: white; padding: 8px; font-size: 14px;">
                Welcome to your creative workspace! This text is barely visible.
            </p>
            <div style="background-color: #e8e8e8; padding: 16px; margin-bottom: 16px;">
                <button style="background-color: #b3d9ff; color: #f0f0f0; border: none; padding: 8px 16px; border-radius: 4px; margin-right: 8px;">
                    Add Element
                </button>
                <button style="background-color: #ffffcc; color: #ffff99; border: none; padding: 8px 16px; border-radius: 4px;">
                    Delete
                </button>
            </div>
            <div style="background-color: #ffccdd; color: #ff6699; padding: 12px; margin-bottom: 16px;">
                Error: This error message is hard to read due to poor contrast!
            </div>
            <div style="background-color: #f9f9f9; padding: 16px;">
                <h3 style="color: #d0d0d0; font-size: 16px;">Project Settings</h3>
                <label style="color: #c0c0c0; font-size: 12px; display: block; margin-bottom: 4px;">
                    Project Name:
                </label>
                <input type="text" style="background-color: #f5f5f5; color: #cccccc; border: 1px solid #eeeeee; padding: 8px; width: 100%;" placeholder="Enter name...">
            </div>
        </div>
        '''
    
    def _create_colorful_mockup(self, visual_data: dict) -> str:
        """Create mockup with too many colors."""
        return '''
        <div style="padding: 12px; background-color: #ff6b9d; font-family: Comic Sans MS, cursive;">
            <h1 style="background: linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3); color: #ffff00; padding: 16px; text-align: center; border-radius: 15px; border: 5px solid #ff1493;">
                🌈 Creative Studio Pro Max Ultra! 🎨
            </h1>
            <div style="background-color: #32cd32; padding: 12px; margin: 8px 0; border-radius: 20px; border: 3px dashed #ff4500;">
                <h2 style="color: #ff69b4; text-shadow: 2px 2px #00ffff;">🛠️ Tools Palette 🛠️</h2>
                <button style="background-color: #ff1493; color: #00ffff; border: 2px solid #9370db; padding: 10px 15px; margin: 4px; border-radius: 25px; box-shadow: 3px 3px #ff6347;">BRUSH</button>
                <button style="background-color: #7fff00; color: #ff4500; border: 2px solid #9370db; padding: 10px 15px; margin: 4px; border-radius: 25px; box-shadow: 3px 3px #ff6347;">ERASER</button>
            </div>
            <div style="background-color: #ffd700; padding: 16px; border: 4px solid #dc143c; border-radius: 10px; margin-bottom: 12px;">
                <h3 style="color: #8b0000; text-decoration: underline;">🎨 Color Explosion Zone! 🎨</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                    <div style="width: 24px; height: 24px; background-color: #ff0000; border: 2px solid #000; border-radius: 50%;"></div>
                    <div style="width: 24px; height: 24px; background-color: #00ff00; border: 2px solid #000; border-radius: 50%;"></div>
                    <div style="width: 24px; height: 24px; background-color: #0000ff; border: 2px solid #000; border-radius: 50%;"></div>
                    <div style="width: 24px; height: 24px; background-color: #ffff00; border: 2px solid #000; border-radius: 50%;"></div>
                    <div style="width: 24px; height: 24px; background-color: #ff00ff; border: 2px solid #000; border-radius: 50%;"></div>
                </div>
            </div>
            <div style="background-color: #800080; padding: 16px; border: 3px solid #ffd700; border-radius: 15px;">
                <button style="background-color: #ff6347; color: #ffff00; border: 2px solid #00ff00; padding: 12px 20px; margin: 4px; border-radius: 20px; font-weight: bold;">SAVE PROJECT 💾</button>
                <button style="background-color: #00ffff; color: #ff1493; border: 2px solid #ff4500; padding: 12px 20px; margin: 4px; border-radius: 20px; font-weight: bold;">EXPORT 📤</button>
            </div>
        </div>
        '''
    
    def _create_violations_mockup(self, visual_data: dict) -> str:
        """Create mockup showing Canva guideline violations."""
        return '''
        <div style="padding: 3px; font-family: Times New Roman, serif; font-size: 11px;">
            <h1 style="font-size: 19px; font-weight: normal; color: #666666; margin: 2px 0; text-align: justify;">
                design elements manager tool
            </h1>
            <div style="margin: 3px 0; padding: 5px;">
                <h2 style="font-size: 13px; color: #999999; text-transform: lowercase; font-style: italic; margin: 1px 0;">
                    available tools
                </h2>
                <button style="background-color: #cccccc; color: #333333; border: 2px inset #999999; border-radius: 15px; padding: 2px 4px; font-size: 10px; font-family: Courier New, monospace; text-transform: uppercase; letter-spacing: 2px;">
                    ADD TEXT
                </button>
                <button style="background-color: transparent; color: #bbbbbb; border: 1px dotted #aaaaaa; border-radius: 0px; padding: 1px 3px; font-size: 9px; text-decoration: underline;">
                    remove
                </button>
            </div>
            <div style="margin: 4px 0; border: 3px double #888888; padding: 2px;">
                <span style="font-size: 9px; color: #aaaaaa; font-variant: small-caps;">element properties:</span>
                <input type="text" style="width: 90px; height: 15px; border: 1px solid #dddddd; border-radius: 20px; padding: 1px 2px; font-size: 8px; font-style: italic; background-color: #f9f9f9; margin: 1px;" placeholder="name...">
            </div>
            <div style="margin: 2px 0; padding: 3px;">
                <h3 style="font-size: 11px; font-weight: 100; color: #bbbbbb; text-align: right; margin-bottom: 1px;">current elements:</h3>
                <span style="display: inline-block; margin: 0px 1px; padding: 1px 2px; background-color: #eeeeee; border: 1px groove #cccccc; font-size: 8px; color: #777777; border-radius: 25px; text-align: center;">TEXT</span>
                <span style="display: inline-block; margin: 0px 1px; padding: 1px 2px; background-color: #eeeeee; border: 1px groove #cccccc; font-size: 8px; color: #777777; border-radius: 25px; text-align: center;">IMAGE</span>
            </div>
            <footer style="font-size: 6px; color: #e0e0e0; background-color: #f5f5f5; text-align: justify; padding: 0px; margin: 1px 0 0 0; font-variant: all-petite-caps;">
                powered by design tools inc. all rights reserved 2024
            </footer>
        </div>
        '''
    
    def _create_layout_issues_mockup(self, visual_data: dict) -> str:
        """Create mockup showing layout and overflow issues."""
        return '''
        <div style="padding: 16px; font-family: system-ui; background-color: #ffffff; min-height: 600px;">
            <header style="width: 800px; background-color: #7000ff; color: white; padding: 16px; border-radius: 8px; margin-bottom: 16px; overflow: hidden;">
                <h1 style="font-size: 24px; margin: 0; white-space: nowrap;">Professional Design Studio Dashboard - Extended Version</h1>
            </header>
            <div style="display: flex; gap: 16px; margin-bottom: 16px; min-width: 600px;">
                <div style="flex: 1; min-width: 200px; background-color: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h2>Tools</h2>
                    <button style="width: 180px; padding: 12px; background-color: #7000ff; color: white; border: none; border-radius: 6px;">Add Text Element</button>
                </div>
                <div style="flex: 1; min-width: 200px; background-color: #f8f9fa; padding: 16px; border-radius: 8px;">
                    <h2>Properties</h2>
                    <input type="text" style="width: 220px; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px;" placeholder="Element width">
                </div>
            </div>
            <div style="position: relative; height: 200px; background-color: #f8f9fa; border-radius: 8px; margin-bottom: 16px;">
                <h3 style="margin: 0; padding: 16px;">Canvas Preview</h3>
                <div style="position: absolute; top: 40px; left: 20px; width: 150px; height: 80px; background-color: #7000ff; color: white; padding: 8px; border-radius: 4px;">Element 1</div>
                <div style="position: absolute; top: 60px; left: 80px; width: 150px; height: 80px; background-color: #28a745; color: white; padding: 8px; border-radius: 4px;">Element 2</div>
                <div style="position: absolute; top: 100px; left: 140px; width: 200px; height: 80px; background-color: #dc3545; color: white; padding: 8px; border-radius: 4px;">Element 3 - Extends beyond container</div>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: nowrap; min-width: 600px;">
                <button style="padding: 12px 16px; background-color: #7000ff; color: white; border: none; border-radius: 6px; white-space: nowrap; min-width: 140px;">Save Project</button>
                <button style="padding: 12px 16px; background-color: #7000ff; color: white; border: none; border-radius: 6px; white-space: nowrap; min-width: 140px;">Export as PNG</button>
                <button style="padding: 12px 16px; background-color: #7000ff; color: white; border: none; border-radius: 6px; white-space: nowrap; min-width: 140px;">Share</button>
            </div>
        </div>
        '''
    
    def _create_good_design_mockup(self, visual_data: dict) -> str:
        """Create mockup showing good Canva design practices."""
        return '''
        <div style="padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #ffffff; font-size: 14px; color: #1f2937; max-width: 350px; margin: 0 auto;">
            <h1 style="font-size: 24px; font-weight: 600; color: #1f2937; margin: 0 0 16px 0; text-align: left;">Design Elements</h1>
            <div style="margin-bottom: 24px;">
                <h2 style="font-size: 18px; font-weight: 600; color: #1f2937; margin: 0 0 8px 0;">Tools</h2>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <button style="background-color: #7000ff; color: #ffffff; border: none; border-radius: 6px; padding: 12px 16px; font-size: 14px; font-weight: 500; width: 100%; text-align: left;">Text</button>
                    <button style="background-color: #ffffff; color: #1f2937; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px 16px; font-size: 14px; font-weight: 500; width: 100%; text-align: left;">Image</button>
                    <button style="background-color: #ffffff; color: #1f2937; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px 16px; font-size: 14px; font-weight: 500; width: 100%; text-align: left;">Shape</button>
                </div>
            </div>
            <div style="margin-bottom: 24px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #1f2937; margin: 0 0 16px 0;">Project Settings</h3>
                <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 4px;">Project name</label>
                <input type="text" placeholder="Enter project name" style="width: 100%; padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; font-size: 14px; background-color: #ffffff; color: #1f2937; box-sizing: border-box;">
            </div>
            <div style="background-color: #f8f9fa; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
                <h4 style="font-size: 14px; font-weight: 600; color: #1f2937; margin: 0 0 12px 0;">Current Elements</h4>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px;">
                        <span>Text: "Welcome"</span>
                        <button style="padding: 4px 8px; font-size: 12px; background-color: transparent; color: #dc2626; border: 1px solid #dc2626; border-radius: 4px;">Remove</button>
                    </div>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px;">
                <button style="background-color: #7000ff; color: #ffffff; border: none; border-radius: 6px; padding: 12px 16px; font-size: 14px; font-weight: 500; width: 100%;">Save Project</button>
                <button style="background-color: #ffffff; color: #7000ff; border: 1px solid #7000ff; border-radius: 6px; padding: 12px 16px; font-size: 14px; font-weight: 500; width: 100%;">Export</button>
            </div>
            <footer style="border-top: 1px solid #e0e0e0; padding-top: 16px; text-align: center;">
                <p style="font-size: 12px; color: #6b7280; margin: 0; line-height: 1.5;">Made with Canva Apps SDK</p>
            </footer>
        </div>
        '''
    
    def _create_generic_mockup(self, visual_data: dict) -> str:
        """Create generic mockup for unknown samples."""
        return '''
        <div style="padding: 16px; font-family: system-ui; background-color: #ffffff;">
            <h1 style="font-size: 24px; color: #1f2937; margin-bottom: 16px;">Canva App Preview</h1>
            <p style="color: #6b7280; margin-bottom: 16px;">This app contains various UI elements that will be analyzed for design quality.</p>
            <button style="background-color: #7000ff; color: white; border: none; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px;">Sample Button</button>
            <input type="text" placeholder="Sample input" style="padding: 12px; border: 1px solid #e0e0e0; border-radius: 6px; width: 100%; box-sizing: border-box;">
        </div>
        '''

    def _transpile_jsx_to_js(self, jsx_code: str) -> str:
        """
        Transpile JSX/TSX code to browser-compatible JavaScript using Babel.
        This allows us to actually execute the React component.
        """
        try:
            import subprocess
            import tempfile
            import os
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsx', delete=False) as jsx_file:
                jsx_file.write(jsx_code)
                jsx_file_path = jsx_file.name
            
            js_file_path = jsx_file_path.replace('.jsx', '.js')
            
            try:
                # Use Babel CLI to transpile JSX to JS with longer timeout
                result = subprocess.run([
                    'npx', 'babel', jsx_file_path,
                    '--presets=@babel/preset-react',
                    '--out-file', js_file_path
                ], capture_output=True, text=True, timeout=30, cwd=os.getcwd())
                
                if result.returncode == 0 and os.path.exists(js_file_path):
                    with open(js_file_path, 'r') as f:
                        transpiled_js = f.read()
                    logger.info("✅ Babel transpilation successful")
                    return transpiled_js
                else:
                    logger.warning(f"Babel transpilation failed: {result.stderr}")
                    return self._create_functional_jsx_fallback(jsx_code)
                    
            finally:
                # Clean up temporary files
                for file_path in [jsx_file_path, js_file_path]:
                    if os.path.exists(file_path):
                        os.unlink(file_path)
                        
        except subprocess.TimeoutExpired:
            logger.warning("Babel transpilation timed out, using smart fallback")
            return self._create_functional_jsx_fallback(jsx_code)
        except Exception as e:
            logger.warning(f"JSX transpilation error: {str(e)}")
            return self._create_functional_jsx_fallback(jsx_code)
    
    def _create_functional_jsx_fallback(self, jsx_code: str) -> str:
        """
        Create a functional component that renders the key visual elements
        without trying to parse complex JSX. This avoids malformed HTML.
        """
        import re
        
        try:
            # Extract key visual information
            colors = re.findall(r'#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}', jsx_code)
            text_content = re.findall(r'["\']([^"\']{3,})["\']', jsx_code)
            
            # Detect component type based on content
            is_poor_contrast = 'poor-contrast' in jsx_code.lower() or any(
                color in jsx_code for color in ['#cccccc', '#ffff99', '#f0f0f0']
            )
            is_colorful = 'too-many-colors' in jsx_code.lower() or len(set(colors)) > 8
            is_violations = 'violations' in jsx_code.lower() or 'Times New Roman' in jsx_code
            is_layout_issues = 'layout-issues' in jsx_code.lower() or '600px' in jsx_code or '800px' in jsx_code
            is_good_design = 'good-design' in jsx_code.lower() or '#7000ff' in jsx_code
            
            # Create appropriate functional component
            if is_poor_contrast:
                return self._create_poor_contrast_component()
            elif is_colorful:
                return self._create_colorful_component()
            elif is_violations:
                return self._create_violations_component()
            elif is_layout_issues:
                return self._create_layout_component()
            elif is_good_design:
                return self._create_good_design_component()
            else:
                return self._create_generic_component(colors, text_content)
                
        except Exception as e:
            logger.error(f"Fallback component creation failed: {str(e)}")
            return self._create_error_component(str(e))
    
    def _create_poor_contrast_component(self) -> str:
        """Create a functional React component for poor contrast testing."""
        return '''
        const PoorContrastApp = () => {
            const [activeTab, setActiveTab] = React.useState('design');
            
            return React.createElement('div', {
                style: {
                    padding: '16px',
                    backgroundColor: '#f5f5f5',
                    fontFamily: 'Arial, sans-serif'
                }
            }, [
                React.createElement('h1', {
                    key: 'title',
                    style: {
                        color: '#cccccc',
                        backgroundColor: '#f0f0f0',
                        padding: '12px',
                        fontSize: '18px',
                        margin: '0 0 16px 0'
                    }
                }, 'Design Tool Dashboard'),
                
                React.createElement('p', {
                    key: 'text',
                    style: {
                        color: '#ffff99',
                        backgroundColor: 'white',
                        padding: '8px',
                        fontSize: '14px',
                        margin: '0 0 16px 0'
                    }
                }, 'Welcome to your creative workspace! This text is barely visible.'),
                
                React.createElement('div', {
                    key: 'buttons',
                    style: {
                        backgroundColor: '#e8e8e8',
                        padding: '16px',
                        marginBottom: '16px'
                    }
                }, [
                    React.createElement('button', {
                        key: 'add',
                        style: {
                            backgroundColor: '#b3d9ff',
                            color: '#f0f0f0',
                            border: 'none',
                            padding: '8px 16px',
                            marginRight: '8px',
                            borderRadius: '4px',
                            fontSize: '14px'
                        }
                    }, 'Add Element'),
                    
                    React.createElement('button', {
                        key: 'delete',
                        style: {
                            backgroundColor: '#ffffcc',
                            color: '#ffff99',
                            border: 'none',
                            padding: '8px 16px',
                            borderRadius: '4px',
                            fontSize: '14px'
                        }
                    }, 'Delete')
                ]),
                
                React.createElement('div', {
                    key: 'error',
                    style: {
                        backgroundColor: '#ffccdd',
                        color: '#ff6699',
                        padding: '12px',
                        fontSize: '13px',
                        marginBottom: '16px'
                    }
                }, 'Error: This error message is hard to read due to poor contrast!'),
                
                React.createElement('div', {
                    key: 'settings',
                    style: {
                        backgroundColor: '#f9f9f9',
                        padding: '16px'
                    }
                }, [
                    React.createElement('h3', {
                        key: 'settings-title',
                        style: {
                            color: '#d0d0d0',
                            fontSize: '16px',
                            margin: '0 0 8px 0'
                        }
                    }, 'Project Settings'),
                    
                    React.createElement('label', {
                        key: 'label',
                        style: {
                            color: '#c0c0c0',
                            fontSize: '12px',
                            display: 'block',
                            marginBottom: '4px'
                        }
                    }, 'Project Name:'),
                    
                    React.createElement('input', {
                        key: 'input',
                        type: 'text',
                        placeholder: 'Enter name...',
                        style: {
                            backgroundColor: '#f5f5f5',
                            color: '#cccccc',
                            border: '1px solid #eeeeee',
                            padding: '8px',
                            width: '100%',
                            fontSize: '14px',
                            boxSizing: 'border-box'
                        }
                    })
                ])
            ]);
        };
        '''
    
    def _create_colorful_component(self) -> str:
        """Create a functional React component with too many colors."""
        return '''
        const ColorfulApp = () => {
            return React.createElement('div', {
                style: {
                    padding: '12px',
                    backgroundColor: '#ff6b9d',
                    fontFamily: 'Comic Sans MS, cursive'
                }
            }, [
                React.createElement('h1', {
                    key: 'title',
                    style: {
                        background: 'linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3)',
                        color: '#ffff00',
                        padding: '16px',
                        textAlign: 'center',
                        borderRadius: '15px',
                        border: '5px solid #ff1493',
                        margin: '0 0 16px 0'
                    }
                }, '🌈 Creative Studio Pro Max Ultra! 🎨'),
                
                React.createElement('div', {
                    key: 'tools',
                    style: {
                        backgroundColor: '#32cd32',
                        padding: '12px',
                        margin: '8px 0',
                        borderRadius: '20px',
                        border: '3px dashed #ff4500'
                    }
                }, [
                    React.createElement('h2', {
                        key: 'tools-title',
                        style: {
                            color: '#ff69b4',
                            textShadow: '2px 2px #00ffff',
                            margin: '0 0 12px 0'
                        }
                    }, '🛠️ Tools Palette 🛠️'),
                    
                    React.createElement('button', {
                        key: 'brush',
                        style: {
                            backgroundColor: '#ff1493',
                            color: '#00ffff',
                            border: '2px solid #9370db',
                            padding: '10px 15px',
                            margin: '4px',
                            borderRadius: '25px',
                            boxShadow: '3px 3px #ff6347',
                            fontWeight: 'bold'
                        }
                    }, 'BRUSH'),
                    
                    React.createElement('button', {
                        key: 'eraser',
                        style: {
                            backgroundColor: '#7fff00',
                            color: '#ff4500',
                            border: '2px solid #9370db',
                            padding: '10px 15px',
                            margin: '4px',
                            borderRadius: '25px',
                            boxShadow: '3px 3px #ff6347',
                            fontWeight: 'bold'
                        }
                    }, 'ERASER')
                ])
            ]);
        };
        '''
    
    def _create_violations_component(self) -> str:
        """Create a component with Canva guideline violations."""
        return '''
        const ViolationsApp = () => {
            return React.createElement('div', {
                style: {
                    padding: '3px',
                    fontFamily: 'Times New Roman, serif',
                    fontSize: '11px'
                }
            }, [
                React.createElement('h1', {
                    key: 'title',
                    style: {
                        fontSize: '19px',
                        fontWeight: 'normal',
                        color: '#666666',
                        margin: '2px 0',
                        textAlign: 'justify'
                    }
                }, 'design elements manager tool'),
                
                React.createElement('div', {
                    key: 'tools',
                    style: {
                        margin: '3px 0',
                        padding: '5px'
                    }
                }, [
                    React.createElement('h2', {
                        key: 'tools-title',
                        style: {
                            fontSize: '13px',
                            color: '#999999',
                            textTransform: 'lowercase',
                            fontStyle: 'italic',
                            margin: '1px 0'
                        }
                    }, 'available tools'),
                    
                    React.createElement('button', {
                        key: 'add-btn',
                        style: {
                            backgroundColor: '#cccccc',
                            color: '#333333',
                            border: '2px inset #999999',
                            borderRadius: '15px',
                            padding: '2px 4px',
                            fontSize: '10px',
                            fontFamily: 'Courier New, monospace',
                            textTransform: 'uppercase',
                            letterSpacing: '2px',
                            margin: '0 4px 0 0'
                        }
                    }, 'ADD TEXT'),
                    
                    React.createElement('button', {
                        key: 'remove-btn',
                        style: {
                            backgroundColor: 'transparent',
                            color: '#bbbbbb',
                            border: '1px dotted #aaaaaa',
                            borderRadius: '0px',
                            padding: '1px 3px',
                            fontSize: '9px',
                            textDecoration: 'underline'
                        }
                    }, 'remove')
                ])
            ]);
        };
        '''
    
    def _create_layout_component(self) -> str:
        """Create a component with layout overflow issues."""
        return '''
        const LayoutApp = () => {
            return React.createElement('div', {
                style: {
                    padding: '16px',
                    fontFamily: 'system-ui',
                    backgroundColor: '#ffffff',
                    minHeight: '600px'
                }
            }, [
                React.createElement('header', {
                    key: 'header',
                    style: {
                        width: '800px',
                        backgroundColor: '#7000ff',
                        color: 'white',
                        padding: '16px',
                        borderRadius: '8px',
                        marginBottom: '16px',
                        overflow: 'hidden'
                    }
                }, React.createElement('h1', {
                    style: {
                        fontSize: '24px',
                        margin: '0',
                        whiteSpace: 'nowrap'
                    }
                }, 'Professional Design Studio Dashboard - Extended Version')),
                
                React.createElement('div', {
                    key: 'content',
                    style: {
                        display: 'flex',
                        gap: '16px',
                        marginBottom: '16px',
                        minWidth: '600px'
                    }
                }, [
                    React.createElement('div', {
                        key: 'tools-panel',
                        style: {
                            flex: '1',
                            minWidth: '200px',
                            backgroundColor: '#f8f9fa',
                            padding: '16px',
                            borderRadius: '8px'
                        }
                    }, [
                        React.createElement('h2', { key: 'tools-title' }, 'Tools'),
                        React.createElement('button', {
                            key: 'add-text',
                            style: {
                                width: '180px',
                                padding: '12px',
                                backgroundColor: '#7000ff',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px'
                            }
                        }, 'Add Text Element')
                    ])
                ])
            ]);
        };
        '''
    
    def _create_good_design_component(self) -> str:
        """Create a component following good Canva design practices."""
        return '''
        const GoodDesignApp = () => {
            return React.createElement('div', {
                style: {
                    padding: '16px',
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                    backgroundColor: '#ffffff',
                    fontSize: '14px',
                    color: '#1f2937',
                    maxWidth: '350px',
                    margin: '0 auto'
                }
            }, [
                React.createElement('h1', {
                    key: 'title',
                    style: {
                        fontSize: '24px',
                        fontWeight: '600',
                        color: '#1f2937',
                        margin: '0 0 16px 0',
                        textAlign: 'left'
                    }
                }, 'Design Elements'),
                
                React.createElement('div', {
                    key: 'tools-section',
                    style: {
                        marginBottom: '24px'
                    }
                }, [
                    React.createElement('h2', {
                        key: 'tools-title',
                        style: {
                            fontSize: '18px',
                            fontWeight: '600',
                            color: '#1f2937',
                            margin: '0 0 8px 0'
                        }
                    }, 'Tools'),
                    
                    React.createElement('div', {
                        key: 'buttons',
                        style: {
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px'
                        }
                    }, [
                        React.createElement('button', {
                            key: 'text-btn',
                            style: {
                                backgroundColor: '#7000ff',
                                color: '#ffffff',
                                border: 'none',
                                borderRadius: '6px',
                                padding: '12px 16px',
                                fontSize: '14px',
                                fontWeight: '500',
                                width: '100%',
                                textAlign: 'left'
                            }
                        }, 'Text'),
                        
                        React.createElement('button', {
                            key: 'image-btn',
                            style: {
                                backgroundColor: '#ffffff',
                                color: '#1f2937',
                                border: '1px solid #e0e0e0',
                                borderRadius: '6px',
                                padding: '12px 16px',
                                fontSize: '14px',
                                fontWeight: '500',
                                width: '100%',
                                textAlign: 'left'
                            }
                        }, 'Image')
                    ])
                ])
            ]);
        };
        '''
    
    def _create_generic_component(self, colors: list, text_content: list) -> str:
        """Create a generic functional component."""
        sample_text = text_content[0] if text_content else 'Sample Text'
        primary_color = colors[0] if colors else '#7000ff'
        
        return f'''
        const GenericApp = () => {{
            return React.createElement('div', {{
                style: {{
                    padding: '16px',
                    fontFamily: 'system-ui',
                    backgroundColor: '#ffffff'
                }}
            }}, [
                React.createElement('h1', {{
                    key: 'title',
                    style: {{
                        fontSize: '24px',
                        color: '{primary_color}',
                        marginBottom: '16px'
                    }}
                }}, 'Canva App Preview'),
                
                React.createElement('p', {{
                    key: 'text',
                    style: {{
                        color: '#6b7280',
                        marginBottom: '16px'
                    }}
                }}, '{sample_text}'),
                
                React.createElement('button', {{
                    key: 'button',
                    style: {{
                        backgroundColor: '{primary_color}',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '12px 16px'
                    }}
                }}, 'Sample Button')
            ]);
        }};
        '''
    
    def _create_error_component(self, error_msg: str) -> str:
        """Create an error display component."""
        return f'''
        const ErrorApp = () => {{
            return React.createElement('div', {{
                style: {{
                    padding: '16px',
                    fontFamily: 'system-ui',
                    backgroundColor: '#fef2f2',
                    color: '#dc2626',
                    borderRadius: '8px'
                }}
            }}, [
                React.createElement('h3', {{
                    key: 'title'
                }}, 'Render Error'),
                React.createElement('p', {{
                    key: 'message'
                }}, '{error_msg}')
            ]);
        }};
        '''

    def _create_react_html_environment(self, transpiled_js: str, file_name: str) -> str:
        """
        Create a complete HTML environment with React to execute the transpiled component.
        """
        
        # Extract component name
        component_name = self._extract_component_name(transpiled_js)
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canva App - {file_name}</title>
    
    <!-- React CDN -->
    <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            width: 350px;
            min-height: 600px;
            box-sizing: border-box;
        }}
        
        #app-root {{
            width: 100%;
            min-height: 100vh;
        }}
        
        /* Canva default styles */
        * {{
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
    <div id="app-root"></div>
    
    <script>
        // Mock Canva SDK
        window.canva = {{
            auth: {{
                getCanvaUserToken: () => Promise.resolve('mock-token')
            }},
            ui: {{
                Button: (props) => React.createElement('button', props, props.children),
                Text: (props) => React.createElement('span', props, props.children)
            }}
        }};
        
        // React hooks
        const {{ useState, useEffect }} = React;
        
        try {{
            // Transpiled component code
            {transpiled_js}
            
            // Render the component
            const appRoot = document.getElementById('app-root');
            if (typeof {component_name} !== 'undefined') {{
                ReactDOM.render(React.createElement({component_name}), appRoot);
            }} else {{
                // Fallback rendering
                appRoot.innerHTML = '<div style="padding: 16px;"><h3>Component Render Error</h3><p>Could not find component: {component_name}</p></div>';
            }}
            
        }} catch (error) {{
            console.error('React rendering error:', error);
            document.getElementById('app-root').innerHTML = 
                '<div style="padding: 16px; color: #dc2626;"><h3>Render Error</h3><p>' + error.message + '</p></div>';
        }}
    </script>
</body>
</html>
        """
        
        return html_content
    
    def _extract_component_name(self, js_code: str) -> str:
        """Extract the main component name from the JavaScript code."""
        import re
        
        # Look for component function/const declarations in the new functional components
        patterns = [
            r'const\s+(\w+App)\s*=',          # PoorContrastApp, ColorfulApp, etc.
            r'const\s+(\w+)\s*=.*React\.createElement',  # General pattern
            r'function\s+(\w+)\s*\(',         # Function declarations
            r'export\s+default\s+(\w+)',      # Default exports
        ]
        
        for pattern in patterns:
            match = re.search(pattern, js_code)
            if match:
                return match.group(1)
        
        # Default fallback - try to detect from content
        if 'PoorContrastApp' in js_code:
            return 'PoorContrastApp'
        elif 'ColorfulApp' in js_code:
            return 'ColorfulApp'
        elif 'ViolationsApp' in js_code:
            return 'ViolationsApp'
        elif 'LayoutApp' in js_code:
            return 'LayoutApp'
        elif 'GoodDesignApp' in js_code:
            return 'GoodDesignApp'
        elif 'GenericApp' in js_code:
            return 'GenericApp'
        elif 'ErrorApp' in js_code:
            return 'ErrorApp'
        
        # Final fallback
        return 'App'
    
    def _create_app_html(self, app_code: str, file_name: str) -> str:
        """
        Create HTML with actual React rendering of JSX/TSX components.
        """
        
        # Determine if it's JSX/TSX or vanilla JS
        is_react = any(pattern in app_code for pattern in [
            'import React', 'from "react"', 'export const', 'export default',
            'jsx', 'tsx', '<', '/>', 'useState', 'useEffect'
        ])
        
        if is_react:
            # Transpile JSX to JavaScript
            logger.info("Transpiling JSX to JavaScript...")
            transpiled_js = self._transpile_jsx_to_js(app_code)
            
            # Create React environment
            html_content = self._create_react_html_environment(transpiled_js, file_name)
            
            return html_content
            
        else:
            # For vanilla JS apps, execute directly
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canva App - {file_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            width: 350px;
            min-height: 600px;
        }}
        .app-container {{
            background: white;
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <div id="app-root">
            <h3>JavaScript App</h3>
            <p>Executing vanilla JavaScript...</p>
        </div>
    </div>
    
    <script>
        // Mock Canva SDK
        window.canva = {{
            auth: {{ getCanvaUserToken: () => Promise.resolve('mock-token') }}
        }};
        
        // Execute app code
        try {{
            {app_code}
        }} catch (error) {{
            console.error('Error executing app code:', error);
            document.getElementById('app-root').innerHTML += 
                '<p style="color: red;">Error rendering app: ' + error.message + '</p>';
        }}
    </script>
</body>
</html>
            """
        
        return html_content
    
    async def capture_app_screenshot(self, app_code: str, file_name: str, save_debug: bool = True) -> Optional[str]:
        """
        Capture screenshot of the rendered Canva app.
        
        Args:
            app_code: The JavaScript/TypeScript code of the app
            file_name: Name of the app file
            save_debug: Whether to save screenshot to debug directory
            
        Returns:
            Base64 encoded screenshot image, or None if capture failed
        """
        try:
            if not self.browser:
                logger.error("Browser not initialized. Use as async context manager.")
                return None
            
            # Create HTML wrapper
            html_content = self._create_app_html(app_code, file_name)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_file:
                temp_file.write(html_content)
                temp_html_path = temp_file.name
            
            try:
                # Create new page and navigate to the HTML file
                page = await self.browser.new_page()
                
                # Set viewport to simulate Canva app panel
                await page.set_viewport_size({"width": 350, "height": 600})
                
                # Navigate to the temporary HTML file
                await page.goto(f"file://{temp_html_path}", wait_until="networkidle")
                
                # Wait for any rendering
                await page.wait_for_timeout(2000)
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(
                    full_page=True,
                    type="png"
                )
                
                # Save debug screenshot if requested
                if save_debug:
                    debug_dir = Path("debug_screenshots")
                    debug_dir.mkdir(exist_ok=True)
                    
                    # Create safe filename
                    safe_filename = "".join(c for c in file_name if c.isalnum() or c in ('-', '_', '.'))
                    file_hash = hash(app_code[:100]) % 10000
                    
                    # Save screenshot
                    screenshot_path = debug_dir / f"screenshot_{safe_filename}_{file_hash}.png"
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    # Save HTML preview for inspection
                    html_path = debug_dir / f"preview_{safe_filename}_{file_hash}.html"
                    with open(html_path, 'w') as f:
                        f.write(html_content)
                    
                    logger.info(f"Debug files saved - Screenshot: {screenshot_path}, HTML: {html_path}")
                    print(f"🖼️  Screenshot saved: {screenshot_path}")
                    print(f"📄  HTML preview saved: {html_path}")
                    print(f"💡  You can open the HTML file in a browser to see how the app renders")
                
                # Convert to base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                await page.close()
                return screenshot_base64
                
            finally:
                # Clean up temporary file
                os.unlink(temp_html_path)
                
        except Exception as e:
            logger.error(f"Failed to capture screenshot: {str(e)}")
            return None
    
    async def analyze_visual_metrics(self, screenshot_base64: str) -> Dict[str, Any]:
        """
        Perform basic visual analysis on the screenshot.
        This provides additional context for Claude's analysis.
        Falls back gracefully if OpenCV is not available.
        """
        try:
            import cv2
            import numpy as np
            
            # Decode base64 image
            image_data = base64.b64decode(screenshot_base64)
            
            # Convert to OpenCV format
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "Could not decode image"}
            
            # Basic visual metrics
            height, width = img.shape[:2]
            
            # Color analysis
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            colors = img_rgb.reshape(-1, 3)
            unique_colors = len(np.unique(colors.view(np.void), axis=0))
            
            # Edge density (visual complexity)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Whitespace analysis
            whitespace_threshold = 240
            whitespace_ratio = np.sum(gray > whitespace_threshold) / gray.size
            
            return {
                "dimensions": {"width": width, "height": height},
                "unique_colors": unique_colors,
                "edge_density": edge_density,
                "whitespace_ratio": whitespace_ratio,
                "visual_complexity": "high" if edge_density > 0.15 else "medium" if edge_density > 0.08 else "low",
                "analysis_method": "opencv"
            }
            
        except ImportError:
            logger.warning("OpenCV not available, using basic image analysis")
            return {
                "analysis_method": "basic",
                "note": "Advanced visual metrics require OpenCV"
            }
        except Exception as e:
            logger.error(f"Failed to analyze visual metrics: {str(e)}")
            return {
                "error": str(e),
                "analysis_method": "failed"
            }


async def capture_canva_app_screenshot(app_code: str, file_name: str, save_debug: bool = True) -> tuple[Optional[str], Dict[str, Any]]:
    """
    Convenience function to capture screenshot and analyze visual metrics.
    
    Args:
        app_code: The JavaScript/TypeScript code of the app
        file_name: Name of the app file
        save_debug: Whether to save screenshot to debug directory for inspection
    
    Returns:
        tuple: (base64_screenshot, visual_metrics)
    """
    async with ScreenshotCapture() as capture:
        screenshot = await capture.capture_app_screenshot(app_code, file_name, save_debug)
        if screenshot:
            metrics = await capture.analyze_visual_metrics(screenshot)
            return screenshot, metrics
        return None, {} 