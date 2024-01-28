import db_interface
import random
import s3_utils
# import generate_ip_stats

RESULT_ITEM = '''<div class="result"><div class="book">
<a href="{}"><img class="result" src="{}"><p>{}</p></a></div></div>'''

RESULTS_NO_ITEMS = '''<p>No results.</p>'''


def generate_sitename():
    sitename = random.choice([
        'Book', 'File', 'Page', 'Text', 'Item', 'Storage', 
        'Article', 'Thing', 'Stuff', 'Object'
    ])
    sitename += random.choice([
        'Shelf', 'Hub', 'Space', 'Place', 'Site', 'Area',
        'Box', 'House', 'Container', 'Repository',
        'Receptacle'
    ])
    return sitename

def populate_results_template(results : list) -> str:
    print(results)
    with open('results.html', 'r') as f:
        page_contents = f.read()
    if len(results) == 0:
        out = page_contents.format(
            sitename=generate_sitename(),
            numberofitems=RESULTS_NO_ITEMS,
            results=''
        )
    else:
        resultstring = ''
        for result in results:
            file_id, coverpath, title, numpages, author, filesize = result
            if coverpath is None:
                cover_src = '/static/images/no_cover_image_found.jpg'
            else:
                cover_src = s3_utils.retrieve_cover_as_base64_jpg_src('{}.jpg'.format(file_id))
            resultstring += RESULT_ITEM.format(
                '/item?id=' + str(file_id), cover_src, title
            )
        s = '' if len(results) == 1 else 's'
        out = page_contents.format(
            sitename=generate_sitename(),
            numberofitems='<p>{} result{}</p>'.format(
                len(results), s
            ),
            results=resultstring
        )
    return out

def populate_item_specific_template(file_id : int) -> str:
    # get relevant attributes from db
    print(f'{file_id=}')
    attr_dict = db_interface.get_file_info(file_id)
    if attr_dict == False:
        return populate_error_template(
            'unknown file ID', 'It looks like you attempted to access a file with an ID that is not in our database. Please try again.'
        )
    for k,v in attr_dict.items():
        if v == None:
            if k == 'coverpath':
                attr_dict['coverpath'] = '/static/images/no_cover_image_found.jpg'
            else:
                attr_dict[k] = '<span style="color: #777">N/A</span>'
        else:
            if k == 'coverpath':
                attr_dict['coverpath'] = s3_utils.retrieve_cover_as_base64_jpg_src('{}.jpg'.format(file_id))
    # populate template with those attributes
    attr_dict['sitename'] = generate_sitename()
    with open('item.html', 'r') as f:
        page_contents = f.read()
    return page_contents.format(**attr_dict)

def populate_landing_template(
        num_files : int, visitor_number, visitor_ip,
        site_start_day : str, site_start_time : str
    ) -> str:
    with open('landing_page.html') as f:
        page_contents = f.read()
    # insert page number markers
    landing_page_dict = {
        'num_files' : num_files,
        's' : 's' if num_files != 1 else '',
        'sitename' : generate_sitename(),
        'site_start_day' : site_start_day,
        'site_start_time' : site_start_time,
        'visitor_number' : visitor_number,
        'visitor_ip' : visitor_ip
    }
    return page_contents.format(**landing_page_dict)

def populate_error_template(error, details):
    with open('error.html', 'r') as f:
        page_contents = f.read()
    return page_contents.format(
        error=error, details=details, 
        sitename=generate_sitename(),
        buttonlink='/', buttontext="Go home"
    )

def populate_upload_success_template(filename, file_id):
    with open('upload_success.html', 'r') as f:
        page_contents = f.read()
    return page_contents.format(
        filename=filename, file_id=file_id, 
        sitename=generate_sitename(), 
        buttonlink='/', buttontext='Go home'
    )

def populate_about_template(topic):
    try:
        print('attempting to open about page on topic {}'.format(topic))
        with open('about/{}.html'.format(topic)) as f:
            # if topic == 'stats':
            #     generate_ip_stats.generate_all_graphics()
            page_contents = f.read()
        return page_contents.format(
            sitename=generate_sitename()
        )
    except:
        return populate_error_template(
            'about topic <code>{}</code> not found'.format(topic),
            'It looks like you tried finding help on something that doesn\'t yet have a help page here. Have you tried Google?'
        )
