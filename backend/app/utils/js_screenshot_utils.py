"""
Simplified screenshot utilities for vanilla JavaScript Canva apps.
Fast, reliable, and dependency-free screenshot capture.
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


class JavaScriptScreenshotCapture:
    """
    Fast screenshot capture for vanilla JavaScript Canva apps.
    No transpilation, no React complexity - just execute JS directly.
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
    
    def _create_html_wrapper(self, js_code: str, file_name: str) -> str:
        """
        Create HTML wrapper for direct JavaScript execution.
        Simple and reliable - no transpilation needed.
        """
        
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
            padding: 16px;
            box-sizing: border-box;
        }}
        
        /* Canva default styles */
        * {{
            box-sizing: border-box;
        }}
        
        button {{
            cursor: pointer;
            font-family: inherit;
        }}
        
        input {{
            font-family: inherit;
        }}
    </style>
</head>
<body>
    <div id="app-root"></div>
    
    <script>
        // Mock Canva SDK for testing
        window.canva = {{
            auth: {{
                getCanvaUserToken: () => Promise.resolve('mock-token-12345')
            }},
            ui: {{
                startDrag: (options) => {{
                    console.log('Drag started:', options);
                    return Promise.resolve();
                }},
                addNativeElement: (element) => {{
                    console.log('Native element added:', element);
                    return Promise.resolve();
                }},
                Button: function(props) {{
                    const button = document.createElement('button');
                    Object.assign(button.style, props.style || {{}});
                    button.textContent = props.children || props.text || 'Button';
                    if (props.onClick) button.addEventListener('click', props.onClick);
                    return button;
                }},
                Text: function(props) {{
                    const span = document.createElement('span');
                    Object.assign(span.style, props.style || {{}});
                    span.textContent = props.children || props.text || 'Text';
                    return span;
                }}
            }}
        }};
        
        // Console capture for debugging
        const originalLog = console.log;
        const originalError = console.error;
        let logs = [];
        
        console.log = (...args) => {{
            logs.push(['log', ...args]);
            originalLog(...args);
        }};
        
        console.error = (...args) => {{
            logs.push(['error', ...args]);
            originalError(...args);
        }};
        
        try {{
            // Execute user's JavaScript code directly
            {js_code}
            
            // Display logs if needed (for debugging)
            if (logs.length > 0 && document.getElementById('app-root').children.length === 0) {{
                const logContainer = document.createElement('div');
                logContainer.style.padding = '16px';
                logContainer.style.backgroundColor = '#f8f9fa';
                logContainer.style.fontFamily = 'monospace';
                logContainer.style.fontSize = '12px';
                
                const title = document.createElement('h3');
                title.textContent = 'App Execution Logs';
                logContainer.appendChild(title);
                
                logs.forEach(([type, ...messages]) => {{
                    const logEntry = document.createElement('div');
                    logEntry.style.color = type === 'error' ? '#dc2626' : '#374151';
                    logEntry.textContent = `[${{type.toUpperCase()}}] ${{messages.join(' ')}}`;
                    logContainer.appendChild(logEntry);
                }});
                
                document.getElementById('app-root').appendChild(logContainer);
            }}
            
        }} catch (error) {{
            console.error('JavaScript execution error:', error);
            
            // Display error in UI
            const errorContainer = document.createElement('div');
            errorContainer.style.padding = '16px';
            errorContainer.style.backgroundColor = '#fef2f2';
            errorContainer.style.border = '1px solid #fecaca';
            errorContainer.style.borderRadius = '8px';
            errorContainer.style.color = '#dc2626';
            
            const title = document.createElement('h3');
            title.textContent = 'JavaScript Error';
            title.style.margin = '0 0 8px 0';
            
            const message = document.createElement('p');
            message.textContent = error.message;
            message.style.margin = '0';
            message.style.fontFamily = 'monospace';
            
            errorContainer.appendChild(title);
            errorContainer.appendChild(message);
            
            document.getElementById('app-root').appendChild(errorContainer);
        }}
    </script>
</body>
</html>
        """
        
        return html_content
    
    async def capture_screenshot(self, js_code: str, file_name: str, save_debug: bool = True) -> Optional[str]:
        """
        Capture screenshot of vanilla JavaScript Canva app.
        
        Args:
            js_code: The vanilla JavaScript code of the app
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
            html_content = self._create_html_wrapper(js_code, file_name)
            
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
                
                # Wait for JavaScript execution
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
                    file_hash = hash(js_code[:100]) % 10000
                    
                    # Save screenshot
                    screenshot_path = debug_dir / f"js_{safe_filename}_{file_hash}.png"
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    # Save HTML preview for inspection
                    html_path = debug_dir / f"js_preview_{safe_filename}_{file_hash}.html"
                    with open(html_path, 'w') as f:
                        f.write(html_content)
                    
                    logger.info(f"Debug files saved - Screenshot: {screenshot_path}, HTML: {html_path}")
                    print(f"🖼️  Screenshot saved: {screenshot_path}")
                    print(f"📄  HTML preview saved: {html_path}")
                    print(f"💡  Open the HTML file in a browser to see how the app renders")
                
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
        Simplified version without OpenCV complexity.
        """
        try:
            # Basic metrics without OpenCV
            import math
            
            # Calculate approximate visual complexity from base64 size
            base64_size = len(screenshot_base64)
            
            # Estimate compression ratio (higher = more complex visuals)
            estimated_complexity = min(base64_size / 20000, 1.0)  # Normalize to 0-1
            
            complexity_level = "low"
            if estimated_complexity > 0.7:
                complexity_level = "high"
            elif estimated_complexity > 0.4:
                complexity_level = "medium"
            
            return {
                "screenshot_size_bytes": base64_size,
                "estimated_visual_complexity": complexity_level,
                "complexity_score": estimated_complexity,
                "analysis_method": "base64_size_estimation",
                "note": "Simplified analysis for vanilla JS apps"
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze visual metrics: {str(e)}")
            return {
                "error": str(e),
                "analysis_method": "failed"
            }


async def capture_js_app_screenshot(js_code: str, file_name: str, save_debug: bool = True) -> tuple[Optional[str], Dict[str, Any]]:
    """
    Convenience function to capture screenshot and analyze visual metrics for vanilla JS apps.
    
    Args:
        js_code: The vanilla JavaScript code of the app
        file_name: Name of the app file
        save_debug: Whether to save screenshot to debug directory for inspection
    
    Returns:
        tuple: (base64_screenshot, visual_metrics)
    """
    async with JavaScriptScreenshotCapture() as capture:
        screenshot = await capture.capture_screenshot(js_code, file_name, save_debug)
        if screenshot:
            metrics = await capture.analyze_visual_metrics(screenshot)
            return screenshot, metrics
        return None, {"error": "Screenshot capture failed"} 