import json
import re
from typing import Any

def clean_generated_text(generated_text: str) -> dict[str, Any]:
    """
    Extracts and cleans JSON from AI-generated text with robust error handling.
    Specifically handles common issues in AI-generated JSON.
    """
    try:
        # First try direct parsing
        try:
            return json.loads(generated_text)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks first
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', generated_text, re.DOTALL)
        if code_block_match:
            json_text = code_block_match.group(1)
        else:
            # Extract JSON content between curly braces
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found in generated text")
            json_text = json_match.group(0)
        
        # Debug: Show what we extracted
        print(f"Extracted JSON length: {len(json_text)}")
        print(f"First 200 chars: {json_text[:200]}")
        
        # Apply specific fixes for this AI's output patterns
        json_text = _fix_ai_json_issues(json_text)
        
        # Final parsing attempt
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            _log_json_error(e, json_text)
            raise ValueError(
                f"Failed to parse JSON after cleaning: {str(e)}\n"
                f"Problem area: {json_text[max(0,e.pos-50):e.pos+50]}"
            ) from e

    except Exception as e:
        if 'json_text' in locals():
            print(f"Full problematic JSON content:\n{json_text[:500]}...")
        raise ValueError(f"JSON processing failed: {str(e)}") from e

def _fix_ai_json_issues(json_text: str) -> str:
    """Fix specific issues found in this AI's JSON output"""
    
    # Debug: Print the original JSON to see what we're working with
    print(f"Original JSON snippet: {json_text[:200]}...")
    
    # MAIN FIX: Handle the specific pattern where commas are missing between key-value pairs
    # This is a more aggressive approach that looks for the exact pattern from the error
    
    # Step 1: Fix the most common pattern: "value""key": should be "value","key":
    # This handles cases like: "Indirect_CP_Violation""scenes":
    json_text = re.sub(r'("(?:[^"\\]|\\.)*")(\s*)("(?:[^"\\]|\\.)*"\s*:)', r'\1,\2\3', json_text)
    
    # Step 2: Fix missing commas after closing braces/brackets before keys
    json_text = re.sub(r'([}\]])(\s*)("(?:[^"\\]|\\.)*"\s*:)', r'\1,\2\3', json_text)
    
    # Step 3: Fix missing commas after numbers before keys
    json_text = re.sub(r'(\d)(\s*)("(?:[^"\\]|\\.)*"\s*:)', r'\1,\2\3', json_text)
    
    # Step 4: Fix missing commas after booleans/null before keys
    json_text = re.sub(r'(true|false|null)(\s*)("(?:[^"\\]|\\.)*"\s*:)', r'\1,\2\3', json_text)
    
    # Step 5: Remove trailing commas before closing braces/brackets
    json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
    
    # Step 6: Handle any remaining edge cases with a more general approach
    # Look for any case where we have two consecutive strings without comma
    lines = json_text.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Check if this line ends with a string and next line starts with a string (key)
        if i < len(lines) - 1:
            current_stripped = line.strip()
            next_stripped = lines[i + 1].strip()
            
            # Pattern: line ends with quoted string, next line starts with quoted string followed by colon
            if (current_stripped.endswith('"') and 
                next_stripped.startswith('"') and 
                ':' in next_stripped and
                not current_stripped.endswith(',') and
                not current_stripped.endswith(',"')):
                # Add comma to current line
                if current_stripped == line:
                    line = line + ','
                else:
                    line = line.replace(current_stripped, current_stripped + ',')
        
        fixed_lines.append(line)
    
    json_text = '\n'.join(fixed_lines)
    
    # Debug: Print the fixed JSON to see what changed
    print(f"Fixed JSON snippet: {json_text[:200]}...")
    
    return json_text

def _log_json_error(error: json.JSONDecodeError, json_text: str):
    """Enhanced error logging for JSON parsing issues"""
    error_context = json_text[max(0, error.pos-50):error.pos+50]
    print("\n--- JSON PARSE ERROR DETAILS ---")
    print(f"Error Type: {error.msg}")
    print(f"Position: {error.pos} (Line: {error.lineno}, Column: {error.colno})")
    print(f"Problem Area: ...{error_context}...")
    print("Suggested Fix: Check for:")
    print("- Missing quotes around values")
    print("- Missing commas between key-value pairs")
    print("- Stray commas inside quotes")
    print("- Unescaped special characters")