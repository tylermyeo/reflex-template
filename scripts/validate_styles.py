#!/usr/bin/env python3
"""
Design System Validation Script for PriceDuck

Checks for common violations of the design system patterns.
Run with: python scripts/validate_styles.py
"""

import re
import os
from pathlib import Path

def find_violations(file_path):
    """Find potential design system violations in a Python file."""
    violations = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Check for inline font_size usage
        if re.search(r'font_size\s*=\s*["\'][^"\']*["\']', line):
            violations.append({
                'line': line_num,
                'type': 'inline_font_size',
                'message': 'Use Typography tokens instead of inline font_size',
                'content': line.strip()
            })
        
        # Check for hardcoded colors
        color_patterns = [
            r'color\s*=\s*["\']#[0-9a-fA-F]{6}["\']',  # hex colors
            r'color\s*=\s*["\'][a-z]+\.[0-9]{3}["\']',   # color.500 patterns
            r'background_color\s*=\s*["\']#[0-9a-fA-F]{6}["\']'
        ]
        
        for pattern in color_patterns:
            if re.search(pattern, line):
                violations.append({
                    'line': line_num,
                    'type': 'hardcoded_color',
                    'message': 'Use Colors tokens instead of hardcoded colors',
                    'content': line.strip()
                })
        
        # Check for direct rx.heading/rx.text usage without styled components
        if 'rx.heading(' in line and 'from .styles import' not in content:
            violations.append({
                'line': line_num,
                'type': 'direct_heading',
                'message': 'Consider using heading_1(), heading_2(), or heading_3() instead',
                'content': line.strip()
            })
        
        # Check for hardcoded spacing
        spacing_patterns = [
            r'padding\s*=\s*["\'][0-9]+(?:px|em|rem)["\']',
            r'margin\s*=\s*["\'][0-9]+(?:px|em|rem)["\']'
        ]
        
        for pattern in spacing_patterns:
            if re.search(pattern, line):
                violations.append({
                    'line': line_num,
                    'type': 'hardcoded_spacing',
                    'message': 'Use Spacing tokens instead of hardcoded spacing',
                    'content': line.strip()
                })
    
    return violations

def validate_directory(directory):
    """Validate all Python files in a directory."""
    violations_by_file = {}
    
    for file_path in Path(directory).rglob('*.py'):
        # Skip the styles directory itself
        if 'styles' in str(file_path):
            continue
            
        violations = find_violations(file_path)
        if violations:
            violations_by_file[str(file_path)] = violations
    
    return violations_by_file

def main():
    """Main validation function."""
    print("🔍 PriceDuck Design System Validator")
    print("=" * 50)
    
    # Validate myapp directory
    violations = validate_directory('myapp')
    
    if not violations:
        print("✅ No design system violations found!")
        return
    
    total_violations = sum(len(v) for v in violations.values())
    print(f"❌ Found {total_violations} potential violations:\n")
    
    for file_path, file_violations in violations.items():
        print(f"📄 {file_path}")
        print("-" * len(file_path))
        
        for violation in file_violations:
            print(f"  Line {violation['line']}: {violation['message']}")
            print(f"    > {violation['content']}")
            print()
    
    print("💡 Tips:")
    print("  • Use 'from .styles import' to get styled components")
    print("  • Use Colors.* for all color values")
    print("  • Use Typography.* for font sizes and weights")
    print("  • Use Spacing.* for padding and margins")
    print("  • Check myapp/styles/README.md for examples")

if __name__ == "__main__":
    main() 