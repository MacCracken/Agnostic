#!/usr/bin/env python3
"""
Script to add type hints to functions that are missing them.
Focuses on common patterns like __init__, async functions, and utility methods.
"""

import os
import re
import ast
from typing import Optional, Dict, List, Any


def analyze_file_for_missing_type_hints(file_path: str) -> List[tuple]:
    """Analyze a file and find functions missing type hints."""
    missing_hints = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse AST to find function definitions
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if function has return type annotation
                has_return_type = node.returns is not None
                
                # Check if all parameters have type annotations
                all_params_typed = True
                for arg in node.args.args:
                    if arg.annotation is None and arg.arg != 'self':
                        all_params_typed = False
                        break
                
                # If missing return type or any parameter type, add to list
                if not has_return_type or not all_params_typed:
                    missing_hints.append((node.name, node.lineno, not has_return_type, not all_params_typed))
    
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
    
    return missing_hints


def add_type_hints_to_file(file_path: str, missing_hints: List[tuple]) -> bool:
    """Add type hints to functions in a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Work backwards through lines to avoid line number shifts
        modifications = []
        
        for func_name, line_no, missing_return, missing_params in missing_hints:
            line_idx = line_no - 1  # Convert to 0-based index
            
            if line_idx >= len(lines):
                continue
                
            line = lines[line_idx]
            
            # Add return type annotation
            if missing_return and '-> ' not in line:
                if 'def __init__' in line:
                    # __init__ methods should return None
                    line = line.rstrip(':') + ' -> None:'
                elif 'async def' in line:
                    line = line.rstrip(':') + ' -> Dict[str, Any]:'
                elif 'def main' in line:
                    line = line.rstrip(':') + ' -> None:'
                else:
                    # Default to Dict[str, Any] for most functions
                    line = line.rstrip(':') + ' -> Dict[str, Any]:'
                
                modifications.append((line_idx, line))
            
            # Add parameter type annotations (simplified approach)
            elif missing_params and '->' not in line:
                # This is complex - for now, we'll just focus on return types
                pass
        
        # Apply modifications
        for line_idx, new_line in sorted(modifications, reverse=True):
            lines[line_idx] = new_line
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        return len(modifications) > 0
        
    except Exception as e:
        print(f"Error adding type hints to {file_path}: {e}")
        return False


def main():
    """Main function to add type hints to all Python files."""
    print("Adding type hints to functions...")
    
    # Find all Python files in key directories
    directories = ['agents/', 'config/', 'shared/', 'webgui/']
    all_files = []
    
    for directory in directories:
        if os.path.exists(directory):
            all_files.extend([
                os.path.join(directory, f) 
                for f in os.listdir(directory) 
                if f.endswith('.py')
            ])
    
    total_modified = 0
    
    for file_path in sorted(all_files):
        print(f"\nAnalyzing {file_path}...")
        
        # Skip __pycache__ and test files for now
        if '__pycache__' in file_path or 'test_' in file_path:
            continue
        
        missing_hints = analyze_file_for_missing_type_hints(file_path)
        
        if missing_hints:
            print(f"  Found {len(missing_hints)} functions missing type hints")
            for func_name, line_no, missing_return, missing_params in missing_hints:
                print(f"    - {func_name} (line {line_no}): missing return={missing_return}, params={missing_params}")
            
            if add_type_hints_to_file(file_path, missing_hints):
                print(f"  ✓ Updated {file_path}")
                total_modified += 1
            else:
                print(f"  ✗ Failed to update {file_path}")
        else:
            print(f"  ✓ All functions have type hints")
    
    print(f"\n{'='*50}")
    print(f"SUMMARY: Updated {total_modified} files")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()