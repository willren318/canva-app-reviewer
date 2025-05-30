"""
File processing and validation for Canva app files.
"""

import logging
import re
import ast
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file processing and validation for uploaded Canva app files."""
    
    def __init__(self, file_path: Path, file_id: str):
        self.file_path = file_path
        self.file_id = file_id
        self.file_extension = file_path.suffix.lower()
        self._content: Optional[str] = None
    
    async def get_content(self) -> str:
        """Read and return file content."""
        if self._content is None:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._content = f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    self._content = f.read()
        return self._content
    
    async def validate_content(self) -> Dict[str, Any]:
        """
        Validate file content for syntax and basic structure.
        
        Returns:
            Dict with validation results and file type information.
        """
        try:
            content = await self.get_content()
            
            # Determine file type
            file_type = self._determine_file_type(content)
            
            # Basic syntax validation
            validation_result = await self._validate_syntax(content, file_type)
            
            # Check for Canva-specific patterns
            canva_patterns = self._check_canva_patterns(content)
            
            return {
                "valid": validation_result["valid"],
                "error": validation_result.get("error"),
                "file_type": file_type,
                "canva_patterns": canva_patterns,
                "content_info": {
                    "lines": len(content.splitlines()),
                    "size_bytes": len(content.encode('utf-8')),
                    "has_imports": "import" in content,
                    "has_exports": "export" in content,
                    "has_react": any(pattern in content for pattern in ["React", "jsx", "tsx"])
                }
            }
            
        except Exception as e:
            logger.error(f"Content validation failed: {str(e)}")
            return {
                "valid": False,
                "error": f"Failed to validate content: {str(e)}",
                "file_type": "unknown"
            }
    
    def _determine_file_type(self, content: str) -> str:
        """Determine the type of JavaScript/TypeScript file."""
        if self.file_extension == '.tsx':
            return 'typescript-react'
        elif self.file_extension == '.ts':
            return 'typescript'
        elif self.file_extension == '.jsx':
            return 'javascript-react'
        elif self.file_extension == '.js':
            # Check if it contains JSX or TypeScript-like syntax
            if any(pattern in content for pattern in ['</', 'jsx', 'React.createElement']):
                return 'javascript-react'
            elif any(pattern in content for pattern in [': string', ': number', 'interface ', 'type ']):
                return 'typescript'
            else:
                return 'javascript'
        else:
            return 'unknown'
    
    async def _validate_syntax(self, content: str, file_type: str) -> Dict[str, Any]:
        """Basic syntax validation for JavaScript/TypeScript files."""
        try:
            # Basic checks for common syntax errors
            
            # Check for balanced brackets
            if not self._check_balanced_brackets(content):
                return {
                    "valid": False,
                    "error": "Unbalanced brackets detected"
                }
            
            # Check for basic JavaScript/TypeScript syntax patterns
            if not self._check_basic_syntax(content):
                return {
                    "valid": False,
                    "error": "Invalid JavaScript/TypeScript syntax detected"
                }
            
            # File-type specific validation
            if file_type.endswith('-react'):
                if not self._validate_react_syntax(content):
                    return {
                        "valid": False,
                        "error": "Invalid React component syntax"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Syntax validation error: {str(e)}"
            }
    
    def _check_balanced_brackets(self, content: str) -> bool:
        """Check if brackets are properly balanced."""
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        # Remove string literals and comments to avoid false positives
        cleaned_content = re.sub(r'["\'].*?["\']', '', content)
        cleaned_content = re.sub(r'//.*?\n', '', cleaned_content)
        cleaned_content = re.sub(r'/\*.*?\*/', '', cleaned_content, flags=re.DOTALL)
        
        for char in cleaned_content:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack:
                    return False
                if pairs[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    def _check_basic_syntax(self, content: str) -> bool:
        """Check for basic JavaScript/TypeScript syntax validity."""
        # Look for obvious syntax errors
        error_patterns = [
            r'function\s*\(\)',  # function without name in declaration
            r'}\s*{',  # Adjacent closing and opening braces without statement
            r';;+',  # Multiple semicolons
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, content):
                return False
        
        # Check for required patterns in a valid JS/TS file
        if not any(pattern in content for pattern in ['function', 'const', 'let', 'var', 'class', '=>']):
            return False
        
        return True
    
    def _validate_react_syntax(self, content: str) -> bool:
        """Validate React component syntax."""
        # Check for JSX patterns
        jsx_patterns = [
            r'<\w+',  # Opening tags
            r'</\w+>',  # Closing tags
            r'React\.',  # React namespace
            r'return\s*\(',  # Return statement with JSX
        ]
        
        return any(re.search(pattern, content) for pattern in jsx_patterns)
    
    def _check_canva_patterns(self, content: str) -> Dict[str, bool]:
        """Check for Canva-specific patterns and imports."""
        patterns = {
            "canva_imports": bool(re.search(r'from\s+["\']@canva/', content)),
            "app_ui_kit": bool(re.search(r'@canva/app-ui-kit', content)),
            "canva_api": bool(re.search(r'@canva/platform', content) or re.search(r'@canva/design', content)),
            "canva_hooks": bool(re.search(r'use\w+.*canva', content, re.IGNORECASE)),
            "export_app": bool(re.search(r'export.*App', content)),
            "canvas_elements": bool(re.search(r'addNativeElement|addText|addImage', content)),
        }
        
        return patterns
    
    async def get_analysis_metadata(self) -> Dict[str, Any]:
        """Get metadata for analysis purposes."""
        content = await self.get_content()
        
        return {
            "file_id": self.file_id,
            "file_path": str(self.file_path),
            "file_extension": self.file_extension,
            "file_size": self.file_path.stat().st_size,
            "line_count": len(content.splitlines()),
            "char_count": len(content),
            "upload_timestamp": self.file_path.stat().st_ctime,
        } 