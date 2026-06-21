import json
import os

# Define input/output paths
INPUT_FILE = 'd:/dang/data/DATABASE20250617.json'
OUTPUT_FILE = 'd:/dang/data/DATABASE20250617.json'

def adjust_grade(possibility, severity, max_grade=4):
    """
    Adjust possibility and severity so that possibility * severity <= max_grade.
    Prioritize keeping numbers as high as possible.
    """
    try:
        p = int(possibility)
        s = int(severity)
    except (ValueError, TypeError):
        return possibility, severity

    if p * s <= max_grade:
        return p, s

    # Strategies to reduce grade:
    # 1. Cap at max_grade if p or s is 1? No.
    # We want closest product <= 4.
    # Possibilities for <= 4:
    # 1*1=1, 1*2=2, 1*3=3, 1*4=4
    # 2*1=2, 2*2=4
    # 4*1=4
    # (3*1=3, 3*1.33.. No integers only)

    # Strategy: Reduce larger number first or proportionally?
    # Simple heuristic:
    # If p*s > 4:
    # Try setting strict limit, e.g.
    # 2, 2 is a balanced high risk (4).
    # 2, 3 -> 6 (Too high) -> 2, 2 (4)
    # 3, 2 -> 6 (Too high) -> 2, 2 (4)
    # 3, 3 -> 9 -> 2, 2 (4)
    # 4, 2 -> 8 -> 4, 1 (4) or 2, 2 (4)?
    # Let's favor 2, 2 for general "High but capped" unless one is clearly dominant.
    # But to be safe and simple:
    # If Product > 4, Set P=2, S=2 (Target 4).
    # Unless one was 1? If P=1, S=5 -> P=1, S=4.
    
    if p == 1:
        s = min(s, 4)
    elif s == 1:
        p = min(p, 4)
    else:
        # Both >= 2. And Product > 4.
        # Implies at least one is > 2, or both are > 2.
        # Example 2*3=6. 3*2=6. 2*4=8. 3*3=9.
        # Safe fallback is 2*2 = 4.
        p = 2
        s = 2
    
    return p, s

def process_data(data):
    if isinstance(data, dict):
        for key, value in data.items():
            process_data(value)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and '가능성' in item and '중대성' in item:
                # Adjust 'Current' values
                p = item.get('가능성', 0)
                s = item.get('중대성', 0)
                
                # Check directly conversion
                new_p, new_s = adjust_grade(p, s, max_grade=4)
                
                if new_p != p or new_s != s:
                    print(f"Adjusting {item.get('위험발생및결과', 'Unknown')}: {p}*{s}={int(p)*int(s)} -> {new_p}*{new_s}={new_p*new_s}")
                    item['가능성'] = str(new_p)
                    item['중대성'] = str(new_s)
                    item['등급'] = str(new_p * new_s)
            
            # Recurse if item has children (though usually list items are leaves)
            # But in this structure, list items are leaves.
            pass

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("Processing Risk Data to enforce Grade <= 4...")
        process_data(data)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
