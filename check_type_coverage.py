#!/usr/bin/env python3
"""
Script to validate and report on type hints coverage across the codebase.
"""

import os
import ast
from typing import Dict, List, Any, Optional


def count_type_hints_in_file(file_path: str) -> Dict[str, int]:
    """Count functions with and without type hints in a file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        total_functions = 0
        functions_with_return_hints = 0
        functions_with_param_hints = 0
        __init__methods = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                
                if node.name == '__init__':
                    __init__methods += 1
                
                # Check return type
                if node.returns is not None:
                    functions_with_return_hints += 1
                
                # Check parameter types (excluding 'self')
                params_with_hints = 0
                total_params = len([arg for arg in node.args.args if arg.arg != 'self'])
                
                for arg in node.args.args:
                    if arg.arg != 'self' and arg.annotation is not None:
                        params_with_hints += 1
                
                if total_params > 0 and params_with_hints == total_params:
                    functions_with_param_hints += 1
                elif total_params == 0:  # No params except self
                    functions_with_param_hints += 1
        
        return {
            'total_functions': total_functions,
            'functions_with_return_hints': functions_with_return_hints,
            'functions_with_param_hints': functions_with_param_hints,
            '__init__methods': __init__methods
        }
    
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return {'total_functions': 0, 'functions_with_return_hints': 0, 'functions_with_param_hints': 0, '__init__methods': 0}


def main():
    """Main function to analyze type hints coverage."""
    print("Analyzing type hints coverage...")
    
    directories = ['agents/', 'config/', 'shared/', 'webgui/']
    total_stats = {
        'total_functions': 0,
        'functions_with_return_hints': 0,
        'functions_with_param_hints': 0,
        '__init__methods': 0,
        'files_processed': 0
    }
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        python_files = [
            os.path.join(directory, f) 
            for f in os.listdir(directory) 
            if f.endswith('.py') and not f.startswith('__')
        ]
        
        for file_path in sorted(python_files):
            stats = count_type_hints_in_file(file_path)
            
            if stats['total_functions'] > 0:
                total_stats['files_processed'] += 1
                
                for key in total_stats:
                    if key != 'files_processed':
                        total_stats[key] += stats[key]
                
                return_coverage = (stats['functions_with_return_hints'] / stats['total_functions']) * 100 if stats['total_functions'] > 0 else 100
                param_coverage = (stats['functions_with_param_hints'] / stats['total_functions']) * 100 if stats['total_functions'] > 0 else 100
                
                print(f"\n{file_path}:")
                print(f"  Functions: {stats['total_functions']}")
                print(f"  Return type hints: {stats['functions_with_return_hints']} ({return_coverage:.1f}%)")
                print(f"  Param type hints: {stats['functions_with_param_hints']} ({param_coverage:.1f}%)")
    
    print(f"\n{'='*60}")
    print("OVERALL TYPE HINTS COVERAGE")
    print(f"{'='*60}")
    print(f"Files processed: {total_stats['files_processed']}")
    print(f"Total functions: {total_stats['total_functions']}")
    print(f"Total __init__ methods: {total_stats['__init__methods']}")
    
    if total_stats['total_functions'] > 0:
        overall_return_coverage = (total_stats['functions_with_return_hints'] / total_stats['total_functions']) * 100
        overall_param_coverage = (total_stats['functions_with_param_hints'] / total_stats['total_functions']) * 100
        
        print(f"Overall return type coverage: {overall_return_coverage:.1f}%")
        print(f"Overall param type coverage: {overall_param_coverage:.1f}%")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    main()