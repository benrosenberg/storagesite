import subprocess
import os


JS_FILE = 'node_render_katex.js'

def render_math_html(math_string):
    # print(math_string)
    # os.system('/usr/bin/node --version')
    with open(JS_FILE, 'r') as f:
        original_js_file_contents = f.read()
        # print(original_js_file_contents)
    js_file_contents = original_js_file_contents.replace('EQN', math_string)
    # print(js_file_contents)
    with open(JS_FILE, 'w') as f:
        f.write(js_file_contents)
    p = subprocess.run(['/usr/bin/node', JS_FILE], stdout=subprocess.PIPE)
    out = p.stdout.decode('utf-8')# .read()
    # print(out)
    with open(JS_FILE, 'w') as f:
        f.write(original_js_file_contents)
    return out
