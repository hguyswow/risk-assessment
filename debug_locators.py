
path = 'd:/dang/위험성평가실행 C7.html'

try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_line = -1
    end_marker_line = -1
    
    for i, line in enumerate(lines):
        if 'let baseRiskData =' in line:
            start_line = i + 1
            print(f"Found baseRiskData start at line {start_line}")
        if 'let riskData =' in line:
            end_marker_line = i + 1
            print(f"Found riskData start at line {end_marker_line}")

    if start_line != -1 and end_marker_line != -1:
        print(f"Content block is between key lines.")
        
except Exception as e:
    print(f"Error: {e}")
