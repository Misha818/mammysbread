import re

def replace_spaces_in_text_nodes(html_content):
    # This regex will match text between HTML tags while ignoring attributes and tags themselves
    def replace_spaces(match):
        # Replace spaces in the text node with &nbsp;
        return match.group(1).replace(' ', '&nbsp;')
    
    # Regex explanation:
    # 1. `>(.*?)<` matches text content between any tags.
    # 2. `re.DOTALL` allows the `.` to match newlines as well.
    return re.sub(r'>([^<]+)<', lambda m: f">{replace_spaces(m)}<", html_content, flags=re.DOTALL)

# Example usage
html_content = '''
<div style="color: red; background-color: blue;">This  is   an example.</div>
<p>This is another    example.</p>
'''

converted_html = replace_spaces_in_text_nodes(html_content)
print(converted_html)
