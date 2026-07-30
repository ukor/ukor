import sys

def convert_to_light_selectors(css_content):
    lines = []
    for line in css_content.splitlines():
        if not line.strip():
            lines.append(line)
        else:
            if " .bg {" in line or ".bg {" in line:
                line = line.replace(".bg {", ':root[data-theme="light"] .bg {')
            if ".chroma {" in line:
                line = line.replace(".chroma {", ':root[data-theme="light"] .chroma {')
            if ".chroma ." in line:
                line = line.replace(".chroma .", ':root[data-theme="light"] .chroma .')
            lines.append(line)
    return "\n".join(lines)

with open("scratch/macchiato.css", "r") as f:
    dark_css = f.read()

with open("scratch/latte.css", "r") as f:
    light_css = convert_to_light_selectors(f.read())

with open("themes/lunar/assets/css/theme.css", "r") as f:
    theme_css = f.read()

# Replace everything from /* --- Syntax Highlighting (Dark Mode Default) --- */ to the end of the file
start_idx = theme_css.find('/* --- Syntax Highlighting (Dark Mode Default) --- */')
if start_idx != -1:
    # Keep the top part of the file
    theme_css_new = theme_css[:start_idx]
    
    # Append the new css
    new_content = theme_css_new + "/* --- Syntax Highlighting (Dark Mode Default) --- */\n"
    new_content += dark_css + "\n"
    new_content += "/* --- Syntax Highlighting (Light Mode) --- */\n"
    new_content += light_css + "\n"
    
    with open("themes/lunar/assets/css/theme.css", "w") as f:
        f.write(new_content)
    print("Successfully replaced theme.css syntax highlighting.")
else:
    print("Could not find the start index in theme.css")

