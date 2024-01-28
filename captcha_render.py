import os
import random
import time
import hashlib
import math
import base64
import render_katex

# boilerplate_header = r'''\documentclass[preview]{standalone} 
# \usepackage{amsmath} \begin{document} \['''
# boilerplate_footer = r'''\] \end{document}'''

def generate_user_id():
    # return sha384-hashed unix timestamp
    timestamp = str(time.time()).replace('.', '')
    return hashlib.sha384(bytes(timestamp, 'utf-8')).hexdigest()

def render_src(eqn):
    # eqn -> user id
    # with open(f'tmp.tex', 'w') as f:
    #     f.write(boilerplate_header + eqn + boilerplate_footer)
    user_id = generate_user_id()
    # os.system('pdflatex --interaction=batchmode tmp.tex 2>&1 > /dev/null')
    # os.system('pdfcrop tmp.pdf > /dev/null')
    # os.system('pdftoppm tmp-crop.pdf > tmp.ppm')
    # os.system('pnmtopng -quiet tmp.ppm > {}.png'.format(user_id))
    # os.system('rm tmp.tex tmp.aux tmp.log tmp.ppm tmp.pdf tmp-crop.pdf')
    # convert image to base64 string
    # with open(user_id + '.png', 'rb') as f:
    #     image_content = f.read()
    # encoded = base64.b64encode(image_content)
    # src = str(encoded, 'utf-8')
    # os.remove(user_id + '.png')

    # return HTML for src instead of an image or base64/png
    src = render_katex.render_math_html(eqn)
    return user_id, src

def process_line(line):
    eqn, ans = line.split('=>')
    eqn = eqn.strip()
    ans = ans.strip()
    return eqn, ans

def random_line(filename):
    with open(filename, 'r') as f:
        # remove whitespace and comments
        lines = [process_line(l) for l in f.readlines() 
                 if l[0] != '#' and len(l.strip()) > 0]
    return random.choice(lines)

def render_random_captcha(filename):
    eqn, ans = random_line(filename)
    r = random.randint(2, 98)
    eqn = eqn % str(r)
    ans = eval(ans)(r)
    user_id, src = render_src(eqn)
    return user_id, src, ans

def render_each():
    with open('eqns.txt', 'r') as f:
        lines = [process_line(l) for l in f.readlines() 
                 if l[0] != '#' and len(l.strip()) > 0]
    for line in lines[20:]:
        eqn, ans = line
        r = random.randint(2, 98)
        eqn = eqn % str(r)
        ans = eval(ans)(r)
        user_id = render_src(eqn)
        print(user_id, ans)
        input() # wait for enter key
        os.remove(user_id + '.png')

if __name__ == '__main__':
    render_each()
