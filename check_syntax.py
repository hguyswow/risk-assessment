import json
import os

file_path = 'd:/dang/data/DATABASE20250617.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check 1: Validity
    try:
        data = json.loads(content)
        print("JSON is valid.")
    except json.JSONDecodeError as e:
        print(f"JSON invalid: {e}")
        exit(1)

    # Check 2: Problematic strings
    if "</script>" in content.lower():
        print("WARNING: Found </script> in JSON data!")
    else:
        print("No </script> found.")
        
    # Check 3: Line separators (U+2028, U+2029) which are valid in JSON but not in JS strings (historically)
    # Modern browsers support them but older ones didn't. Best to be safe.
    if '\u2028' in content or '\u2029' in content:
        print("WARNING: Found U+2028 or U+2029!")
    else:
        print("No line separators found.")

except Exception as e:
    print(f"Error: {e}")
