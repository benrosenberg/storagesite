#
#   RUN ME WITH `flask run` in the command line (from within same directory)!
#

import json

# leetcode solutions auth token
with open('leetcode-credentials.json', 'r') as f:
    leetcode_credentials = json.loads(f.read())

leetcode_json_file_location = 'static/leetcode-solutions.json'

from flask import Flask, request, redirect, url_for, send_file

VISITOR_LOG_FILENAME = './static/files/visitors.txt'

import populate_templates

import subprocess

import datetime
SITE_START_DAY = datetime.datetime.now().date().isoformat()
SITE_START_TIME = datetime.datetime.now().time().isoformat() + ' GMT-5'

import time

import hashlib
BUF_SIZE = 65536

import pdf2image
import PyPDF2

import PIL
from PIL import ImageFont, Image, ImageDraw
fnt = PIL.ImageFont.truetype('fonts/FreeMono.ttf', 16)

import epub_thumbnailer
# import djvu_thumbnailer

import db_interface

import os

import captcha_render

import discord_webhook_interface

import s3_utils

import re
URL_PATTERN = r'^(?:(?:(?:https?|ftp):)?\/\/)(?:\S+(?::\S*)?@)?(?:(?!(?:10|127)(?:\.\d{1,3}){3})(?!(?:169\.254|192\.168)(?:\.\d{1,3}){2})(?!172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2})(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)(?:\.(?:[a-z\u00a1-\uffff0-9]-*)*[a-z\u00a1-\uffff0-9]+)*(?:\.(?:[a-z\u00a1-\uffff]{2,})).?)(?::\d{2,5})?(?:[/?#]\S*)?$'

import custom_string_formatter
custom_formatter = custom_string_formatter.CustomFormatter()


app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
MAX_FILESIZE_STR = '10MB'

@app.errorhandler(404)
def page_not_found(_):
    return populate_templates.populate_error_template(
        '404 (file not found)', 'It looks like the endpoint you tried to reach doesn\'t exist. ' 
        + 'Check the URL you entered for typos and try again.'
    )

@app.errorhandler(413)
def file_too_big(_):
    return populate_templates.populate_error_template(
        '413 (file too big)', 'It looks like you tried to upload a file larger than {}. '.format(
            MAX_FILESIZE_STR
        )
        + 'Unfortunately, this site only accepts files that are {} or smaller. '.format(
            MAX_FILESIZE_STR
        )
        + 'Please try again with a smaller file.'
    )

def log_visitor(request):
    ip = request.access_route[-1]
    with open(VISITOR_LOG_FILENAME, 'a') as f:
        f.write('[ {} ] {}\n'.format(datetime.datetime.now().isoformat(), ip))
    with open(VISITOR_LOG_FILENAME, 'r') as f:
        linecount = sum(1 for _ in f)
    return linecount, ip

@app.route("/", methods=['GET'])
def land():
    if request.args.get('query'):
        print('[get] <landing page> searching for', request.args.get('query'))
        # build up get request to redirect to results page
        query_string = ''
        for arg,val in request.args.items():
            query_string += '{}={}&'.format(arg, val)
        query_string = query_string[:-1]
        return redirect(url_for('results') + '?' + query_string)
    else:
        num_files = db_interface.get_num_files() 
        visitor_number, visitor_ip = log_visitor(request)
        return populate_templates.populate_landing_template(
            num_files, visitor_number, visitor_ip, 
            SITE_START_DAY, SITE_START_TIME
        )

# simply returns page content from a filename
def page_content(filename):
    with open(filename, 'r') as f:
        contents = f.read()
    return contents

# fill results HTML template
def apply_search(query):
    if query == 'all':
        results = db_interface.search_all()
    else:
        results = db_interface.search(query.split())
    # out = 'searched for ' + str(query)
    # out += '\n' + 'results: ' + str(results)
    return populate_templates.populate_results_template(results)

@app.route('/results', methods=['GET', 'POST'])
def results():
    if request.args.get('query'):
        print('[get] <results page> searching for', request.args.get('query'))
        return apply_search(request.args.get('query'))
    else:
        return redirect(url_for('land'))

@app.route('/item', methods=['GET', 'POST'])
def item():
    if request.method == 'GET':
        if request.args.get('id'):
            file_id = request.args.get('id')
            return (populate_templates
                .populate_item_specific_template(
                    file_id
                )
            )
        else:
            return populate_templates.populate_error_template(
                'item page not found', 
                'It looks like the item you are looking for is not there. '
                + 'Perhaps you mistyped the URL?'
            )
    else: # request.method == 'POST'
        if request.args.get('id'):
            file_id = request.args.get('id')
            # build up get request to redirect to download page
            return redirect(url_for('download') + '?' + 'id=' + str(file_id))

def generate_filename(title, author, filepath):
    title = '_'.join(title.split())
    author = '_'.join(author.split())
    ext = filepath[filepath.find('.'):]
    return title + '_' + '({})'.format(author) + ext

@app.route('/download', methods=['GET'])
def download():
    if request.args.get('id'):
        file_id = request.args.get('id')
        file_info = db_interface.get_download_attrs(file_id)
        success, file_data_or_error = s3_utils.retrieve_file_as_bytes(file_info['filepath'])
        if success:
            return send_file(
                file_data_or_error,
                download_name=generate_filename(
                    file_info['title'], 
                    file_info['author'],
                    file_info['filepath']
                )
            )
        return populate_templates.populate_error_template(
            'download failed', file_data_or_error
        )
    else:
        return populate_templates.populate_error_template(
            'download failed', 'It seems as though you attempted to download a file in an unexpected way. ' 
            + 'Consider instead downloading the file by way of the item-specific page, '
            + 'accessible via the search bar, or by formulating your GET request correctly.'
        )
    
@app.route('/about', methods=['GET'])
def about():
    if request.args.get('topic'):
        topic = request.args.get('topic')
    else:
        topic = 'general'
    return populate_templates.populate_about_template(topic)

def allowed_file(filename):
    # ALLOWED_EXTENSIONS = {'txt', 'tex', 'pdf', 'epub', 'djvu', 'md'} 
    ALLOWED_EXTENSIONS = {'txt', 'tex', 'pdf', 'epub', 'md'} 
    return '.' in filename and filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS

def check_required_fields(request_form):
    REQUIRED_FIELDS = {'title', 'author', 'pubdate'}
    missing = []
    for field in REQUIRED_FIELDS:
        if not request_form.get(field):
            missing.append(field)
    if len(missing) > 0:
        return False, missing
    return True, missing

def apply_add(formdata):
    # check whether uploaded file is valid
    if 'uploadedfile' not in request.files:
        return False, 'no file uploaded', 'It appears as though you haven\'t uploaded any files.'
    if request.files['uploadedfile'].filename == '':
        return False, 'no file uploaded', 'It appears as though you haven\'t uploaded any files.'
    uploaded_file = request.files['uploadedfile']
    if not allowed_file(uploaded_file.filename):
        return False, 'disallowed file extension', 'It appears as though you attempted to upload a file with a disallowed file extension.'
    
    # check whether all required fields are filled
    check_result, check_fields_missing = check_required_fields(formdata)
    if not check_result:
        return False, 'missing required field(s): ' + ', '.join(check_fields_missing), 'It appears as though you attempted to upload a file without filling in all the required fields. Please fill them in and try again.'
    
    # initialize data dict
    all_fields = '''
        title author pubdate uploaddate sourcelink coverpath filepath numpages 
        filesize filetype md5 sha1 sha256 id
    '''.split()
    data = {field : None for field in all_fields}
    
    # get current timestamp
    uploaddate = datetime.datetime.now()

    # determine max current ID so no overwriting occurs
    max_id = db_interface.get_max_id()
    file_id = max_id + 1

    # determine file extension and save file
    ext = uploaded_file.filename.split('.')[-1]
    filename = '{}.{}'.format(file_id, ext)
    filepath = os.path.join('tmp', filename)
    uploaded_file.save(filepath)

    # get file hashes
    sha1, sha256, md5 = hashlib.sha1(), hashlib.sha256(), hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(BUF_SIZE)
            if not chunk:
                break
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)

    # user-provided data: title, author, date of publication, source link
    user_fields = ['title', 'author', 'pubdate', 'sourcelink']
    for field in user_fields:
        supplied = request.form.get(field)
        if supplied:
            if field == 'sourcelink':
                if not re.match(URL_PATTERN, supplied):
                    return False, 'ill-formatted source link', 'It appears as though you managed to submit a source link with an invalid format. Please try again.'
            data[field] = supplied

    # generated data: document ID, date added to db, number of pages, filesize, filetype, 
    # sha1/sha256, cover_filepath, document filepath (this is just /items/<doc ID> or something similar)
    data['id'] = file_id
    data['filepath'] = filename
    data['filesize'] = os.path.getsize(filepath)
    data['sha1'] = sha1.hexdigest()
    data['md5'] = md5.hexdigest()
    data['sha256'] = sha256.hexdigest()
    data['uploaddate'] = uploaddate

    ext_to_filetype = {
        'txt' : 'Plaintext',
        'tex' : 'TeX',
        'pdf' : 'PDF',
        'md' : 'Markdown',
        # 'djvu' : 'DJVU',
        'epub' : 'EPUB'
    }
    data['filetype'] = ext_to_filetype[ext.lower()]

    # get cover of image (or don't)
    if data['filetype'] == 'PDF':
        # coverpath = os.path.join('static', 'covers', '{}.jpg'.format(file_id))
        coverpath = '{}.jpg'.format(file_id)
        try:
            pages = pdf2image.convert_from_path(filepath, dpi=100, first_page=1, last_page=1, fmt='jpeg')
        except Exception as e:
            return False, 'unable to get pdf cover image', 'It looks like you managed to upload a PDF file that either isn\'t actually a PDF or has some other issue with it that makes it impossible to read the first page. Please try again.'
        for page in pages:
            # page.save(coverpath, 'JPEG')
            s3_utils.upload_PIL_image_cover(page, coverpath, format='jpeg')
        data['coverpath'] = coverpath
        with open(filepath, 'rb') as f:
            pdfReader = PyPDF2.PdfReader(f)
            data['numpages'] = len(pdfReader.pages)
    elif data['filetype'] == 'EPUB':
        # coverpath = os.path.join('static', 'covers', '{}.jpg'.format(file_id))
        coverpath = '{}.jpg'.format(file_id)
        result = epub_thumbnailer.extract_cover(filepath, coverpath)
        if result: 
            data['coverpath'] = coverpath
        else:
            print('failed to extract cover from epub')
    elif data['filetype'] in ['Plaintext', 'TeX', 'Markdown']:
        # coverpath = os.path.join('static', 'covers', '{}.jpg'.format(file_id))
        coverpath = '{}.jpg'.format(file_id)
        first_100_lines = []
        with open(filepath, 'r') as f:
            line = 0
            while line < 100:
                this_line = f.readline()
                if not this_line:
                    break
                else:
                    first_100_lines.append(this_line)
        blurb = '\n'.join(first_100_lines)
        print('generated blurb')
        image_size = (500, 700)
        cover = PIL.Image.new('RGB', image_size, color=(255, 255, 255))
        d = PIL.ImageDraw.Draw(cover)
        d.text((10, 10), blurb, font=fnt, fill=(0,0,0))
        print('generated PIL cover image')
        # cover.save(coverpath)
        s3_utils.upload_PIL_image_cover(cover, coverpath, format='jpeg')
        print('uploaded PIL cover image to s3')
        data['coverpath'] = coverpath
    # elif data['filetype'] == 'DJVU':
    #     coverpath = os.path.join('static', 'covers', '{}.jpg'.format(file_id))
    #     result = djvu_thumbnailer.extract_cover(filepath, coverpath)
    #     if result: 
    #         data['coverpath'] = coverpath
    #     else:
    #         print('failed to extract cover from djvu')
    #     data['numpages'] = djvu_thumbnailer.get_num_pages(filepath)
    
    # upload to s3
    s3_utils.upload_file_directly(uploaded_file, filename)

    # remove tmp file, as file has been already uploaded to s3
    os.remove(filepath)

    # get file tags
    tags = []
    if formdata.get('tags'):
        tags = formdata.get('tags').split()

    # make db entry
    db_interface.add_file(data, tags)

    return True, uploaded_file.filename, file_id

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        print('[post] <add page> adding', request.form)
        user_id, answer = request.form.get('user-id'), request.form.get('captcha-answer')
        expected_answer = db_interface.pop_captcha_answer(user_id)
        if expected_answer == False:
            return populate_templates.populate_error_template(
                'missing user ID', 'It looks like we don\'t have a record of you accessing the captcha page correctly. Please try again.'
            )
        try:
            answer_int = int(answer)
            if expected_answer != answer_int:
                return populate_templates.populate_error_template(
                    'wrong answer to captcha', 'It looks like you didn\'t provide the answer we were looking for. Please try again - some captchas are easier than others!'
                )
        except:
            return populate_templates.populate_error_template(
                'non-integer answer provided', 'It looks like you provided an answer that was not an integer. All captchas have integer answers, please try again.'
            )
        add_success, x, y = apply_add(request.form)
        if add_success:
            ip = request.access_route[-1]
            discord_webhook_interface.send_message(f'FILE UPLOADED\n{x}\n{y}\nIP: {ip}')
            return populate_templates.populate_upload_success_template(
                x, y
            )
        else:
            return populate_templates.populate_error_template(
                x, y
            )
    else:
        start = time.time()
        user_id, src, answer = captcha_render.render_random_captcha('eqns.txt')
        ip = request.access_route[-1]
        discord_webhook_interface.send_message('CAPTCHA GENERATED\nUser ID: {}\nUser IP: {}\nAnswer: {}'.format(user_id, ip, answer))
        db_interface.add_captcha_answer(user_id, answer)
        page_load_time = str(round(time.time() - start, 2)) + ' seconds'
        return custom_formatter.format(page_content('add.html'), {
            'CAPTCHA_HTML' : src, 
            'USER_ID' : user_id,
            'MAX_FILE_SIZE' : MAX_FILESIZE_STR,
            'PAGE_LOAD_TIME' : page_load_time,
            'SITENAME' : populate_templates.generate_sitename()
        })

def get_leetcode_data():
    with open(leetcode_json_file_location, 'r') as f:
        full_dict = json.loads(f.read())
    return full_dict

# overwrite by default
def insert_submission(current_data, new_key, new_item):
    current_data[new_key] = new_item
    with open(leetcode_json_file_location, 'w') as f:
        f.write(json.dumps(current_data))
    return 'Successfully updated submission for key {}.'.format(new_key)

# structure of submission json: { key : { <data> } }
@app.route('/submit-lc', methods=['POST'])
def submit_lc():
    print(request)
    try:
        print('submit attempt detected')
        if request.method == 'POST':
            if request.headers.get('Authentication'):
                if request.headers.get('Authentication') == leetcode_credentials['token']:
                    try:
                        if request.is_json:
                            print('[post] <submit leetcode> submitting', request.json)
                            print(request.json)
                            current_data = get_leetcode_data()
                            print('got by current data retrieval')
                            new_data = request.json
                            new_key = list(new_data.keys())[0]
                            new_item = new_data[new_key]
                            return insert_submission(current_data, new_key, new_item)
                        else:
                            return 'Content type is not supported.', 400
                    except Exception as e:
                        return 'failed to get json - {}, {}, {}'.format(repr(e), request, repr(request)), 400
                else:
                    return 'Authentication failed.', 401
            else:
                return 'Missing authentication header.', 401
        else:
            return 'Request type not supported.', 400
    except Exception as e:
        return 'hit this exception: ' + repr(e) + ' at request ' + str(request)
