import re

html_path = 'd:/dang/위험성평가실행 C7.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add APP_VERSION constant near riskData definition
if 'const APP_VERSION =' not in content:
    content = content.replace('let riskData = JSON.parse(JSON.stringify(baseRiskData));', 
                              'const APP_VERSION = "4.2";\n        let riskData = JSON.parse(JSON.stringify(baseRiskData));')

# 2. Update saveUserData to use APP_VERSION
# Original: version: "4.1"
content = re.sub(r'version:\s*"[\d\.]+"', 'version: APP_VERSION', content)

# 3. Update checkAndShowInitialSetup to check version
# We need to find the function and modify the condition.
# Can't easily use regex for multi-line logic replacement without being careful.
# Instead, I'll use a unique string replacement for the condition I modified earlier.

# In Step 140, I modified:
# if (userData && userDataModified) {
# to
# if (userData && userDataModified) { 
# (Wait, I just replaced the prompt logic, but the IF condition remained)

# Let's find the `if (userData && userDataModified)` and add version check.
# Since I previously modified the surrounding code, I 'll search for the block.

pattern_old = r'if \(userData && userDataModified\) \{'
replacement_new = r'if (userData && userDataModified && userData.version === APP_VERSION) {'

content = re.sub(pattern_old, replacement_new, content)

# 4. Also add a log to explain why it reset if version mismatch
# Find the ELSE block for this IF.
# It's hard to inject correctly with regex.
# However, modifying the IF condition is the most critical part. 
# If mismatch, it goes to ELSE -> load baseRiskData (which I implemented in Step 140).

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated HTML version logic.")
