# functions to interface with the db indirectly rather than 
# doing so directly within the flask app

import sqlite3
#con = sqlite3.connect('the.db', check_same_thread=False, timeout=10)
#cur = con.cursor()

import s3_utils

def db_wrapper(func):
    def inner_func(*args, **kwargs):
        con = sqlite3.connect('the.db', check_same_thread=False, timeout=10)
        cur = con.cursor()
        return_value = func(cur, con, *args, **kwargs)
        con.close()
        return return_value
    return inner_func

def head(table, n=5):
    sample(True, table, n)

def tail(table, n=5):
    sample(False, table, n)

def sample(head, table, n):
    direction = 'ASC' if head else 'DESC'
    column = 'id' if table in ['files', 'tags'] else 'file_id'
    rows = cur.execute('''
        SELECT * 
        FROM {}
        ORDER BY {} {}
        LIMIT {}
    '''.format(table, column, direction, n)).fetchall()
    if head:
        print('\n'.join([str(row) for row in rows]))
    else:
        print('\n'.join([str(row) for row in rows][::-1]))

@db_wrapper
def reset_all(cur, con):
    tables_to_drop = [
        'files', 'tags_id_files_id', 'tags', 'captchas'
    ]
    for table_to_drop in tables_to_drop:
        try:
            cur.execute('DROP TABLE {}'.format(table_to_drop))
        except Exception as e:
            print('Unable to drop table {}, continuing.'.format(table_to_drop))
    cur.execute("""CREATE TABLE files(
        title text, 
        author text, 
        pubdate text,
        uploaddate timestamp, 
        sourcelink text, 
        coverpath text, 
        filepath text, 
        numpages int, 
        filesize int, 
        filetype text,
        md5 text, 
        sha1 text, 
        sha256 text, 
        id int PRIMARY KEY
    )""")
    cur.execute("""CREATE TABLE tags_id_files_id(
        tag_id int, 
        file_id int
    )""")
    cur.execute("""CREATE TABLE tags(
        tag_name text, 
        number_tagged int, 
        id int PRIMARY KEY
    )""")
    cur.execute("""CREATE TABLE captchas(
        timestamp_hash text,
        answer int
    )""")
    con.commit()
    print('Database reset.')

'''
Parameters: None
'''
@db_wrapper
def get_num_files(cur, con):
    return cur.execute('SELECT COUNT(*) FROM files').fetchone()[0]

'''
Parameters: None.

Returns the maximum ID found in the files table.
'''
@db_wrapper
def get_max_id(cur, con):
    try:
        max_id = cur.execute('''
            SELECT id 
            FROM files 
            ORDER BY id DESC
        ''').fetchone()[0]
    except Exception as e:
        print('No files found, creating new max ID starting from 0:', e)
        max_id = 0
    return max_id

'''
Parameters:

    attributes (dict) : a dictionary containing the following elements:
        title: the title of the file
        author: the author of the file
        pubdate: the date the file was originally published
        uploaddate: the timestamp at which the file was uploaded
        sourcelink: a link to the original source of the file, or None
        coverpath: the (local) path to the file's cover thumbnail
        filepath: the (local) path to the file itself
        numpages: the number of pages that the file has, or None
        filesize: the size of the file
        filetype: the type of the file
        md5: the md5 hash of the file
        sha1: the sha1 hash of the file
        sha256: the sha256 hash of the file
        id: the unique numeric identifier of the file

    tags (iterable of strings) : an iterable of the file's tags
'''
@db_wrapper
def add_file(cur, con, attributes : dict, tags):
    # add file to files table
    ATTRIBUTE_LIST = [
        'title', 'author', 'pubdate', 'uploaddate', 'sourcelink', 
        'coverpath', 'filepath', 'numpages', 'filesize', 
        'filetype', 'md5', 'sha1', 'sha256', 'id'
    ]
    query = 'INSERT INTO files VALUES('
    query += ', '.join([':' + attr for attr in ATTRIBUTE_LIST])
    query += ')'
    cur.execute(query, attributes)

    # some attributes are added as tags
    TAG_ATTRIBUTES = [
        'title', 'author', 'pubdate',
        'md5', 'sha1', 'sha256'
    ]
    tags = set(tags)
    for attr in TAG_ATTRIBUTES:
        tags |= set(attributes[attr].split())

    tags = {tag.lower() for tag in tags}

    # add tags to tag-file id junction table, and update tags table
    for tag in tags:
        id_data = {'tag_id' : None, 'file_id' : attributes['id']}
        ## first, check if tag is already in db
        print(tag)
        cur.execute('SELECT id FROM tags WHERE tag_name = :tag', [tag])
        rows = cur.fetchone()
        if rows: 
            # tag is in db, rows contains ID of that tag
            id_data['tag_id'] = rows[0]
        else:
            # determine max tag id so far
            try:
                max_id = cur.execute('SELECT MAX(id) FROM tags').fetchone()[0]
                id_data['tag_id'] = max_id + 1
            except:
                max_id = 0
                id_data['tag_id'] = max_id + 1
            # create tags entry in db since it does not yet exist
            tag_info = {
                'tag_name' : tag, 'number_tagged' : 0, 'id' : max_id + 1
            }
            cur.execute('''INSERT INTO tags VALUES(
                :tag_name, :number_tagged, :id
            )''', tag_info)
            
        # create entry in junction table
        cur.execute('''
            INSERT INTO tags_id_files_id VALUES(:tag_id, :file_id)
        ''', id_data)
        # update count in tags table
        cur.execute('''
            UPDATE tags
            SET number_tagged = number_tagged + 1
            WHERE id = :tag_id
        ''', id_data)
        con.commit()

    print('Addition of file {} completed.'.format(attributes['id']))

'''
Parameters:

    file_id (int): the unique id of the file to be removed
'''
@db_wrapper
def remove_file(cur, con, file_id : int):
    # first, retrieve file to get filepath and coverpath for deleting from s3
    file_rows = cur.execute('''
        SELECT filepath, coverpath
        FROM files
        WHERE id = :file_id
    ''', {'file_id' : file_id}).fetchone()

    if file_rows is None:
        paths_found = False
    else:
        paths_found = True
        filepath, coverpath = file_rows

    # delete file from files table
    cur.execute('''
        DELETE FROM files 
        WHERE id = :file_id
    ''', {'file_id' : file_id})
    # determine which tags the file had so they can be updated
    cur.execute('''
        SELECT tag_id 
        FROM tags_id_files_id
        WHERE file_id = :file_id
    ''', {'file_id' : file_id})
    affected_tags = [row[0] for row in cur.fetchall()]
    # delete file tags from tags junction table
    cur.execute('''
        DELETE FROM tags_id_files_id
        WHERE file_id = :file_id
    ''', {'file_id' : file_id})
    # decrement tag counts
    cur.executemany('''
        UPDATE tags
        SET number_tagged = number_tagged - 1
        WHERE id = ?
    ''', [(tag_id,) for tag_id in affected_tags])
    con.commit()

    print('Removal of file {} from database completed. {} tags affected.'.format(
        file_id, len(affected_tags)
    ))

    if paths_found:
        s3_utils.delete_file(filepath)
        s3_utils.delete_cover(coverpath)

        print('Successfully removed file and cover for {} from s3.'.format(filepath))
    else:
        print('Could not remove file and cover from s3 because there were no corresponding rows in the DB')

'''
Parameters:
    
    tag_id (int): the id of the tag to remove
'''
@db_wrapper
def remove_tag(cur, con, tag_id : int):
    # get number of affected records
    num_affected = cur.execute('''
        SELECT number_tagged
        FROM tags
        WHERE tag_id = :tag_id
    ''', {'tag_id' : tag_id}).fetchone()[0]
    # delete tag from tags table
    cur.execute('''
        DELETE FROM tags
        WHERE id = :tag_id
    ''', {'tag_id' : tag_id})
    # delete tags from tags junction table
    cur.execute('''
        DELETE FROM tags_id_files_id
        WHERE tag_id = :tag_id
    ''', {'tag_id' : tag_id})
    con.commit()

    print('Removal of tag {} completed. {} files affected.'.format(
        tag_id, num_affected
    ))

'''
Parameters: 

    captcha_id (str): the ID (timestamp hash) of a captcha.
    answer (int): the correct/expected answer to the captcha. 
'''
@db_wrapper
def add_captcha_answer(cur, con, captcha_id, answer):
    cur.execute('''
        INSERT INTO captchas VALUES(:captcha_id, :answer)
    ''', {'captcha_id' : captcha_id, 'answer' : answer})
    con.commit()
    print('Addition of captcha [\'{}\' <=> {}] completed.'.format(
        captcha_id[:6] + '...', answer
    ))

'''
Parameters:

    captcha_id (str): the ID (timestamp hash) of a captcha.

Returns the answer associated with captcha_id and, if found,
removes the record from the table.
'''
@db_wrapper
def pop_captcha_answer(cur, con, captcha_id):
    results = cur.execute('''
        SELECT answer
        FROM captchas
        WHERE timestamp_hash = :captcha_id
    ''', {'captcha_id' : captcha_id}).fetchone()
    if results == None:
        return False
    answer = results[0]
    cur.execute('''
        DELETE FROM captchas
        WHERE timestamp_hash = :captcha_id
    ''', {'captcha_id' : captcha_id})
    con.commit()
    print('Popped [\'{}\' <=> {}] from captchas.'.format(
        captcha_id[:6] + '...', answer
    ))
    return answer

'''
Parameters: 

    tags (iterable of strings): an iterable of strings to search for as tags
'''
@db_wrapper
def search(cur, con, tags : list):
    tags = list(set(filter(lambda x:x is not None, tags)))
    # only return those attributes needed for displaying results
    cur.execute('''
        SELECT files.id, files.coverpath, files.title,
        files.numpages, files.author, files.filesize 
        FROM files
        WHERE files.id IN (SELECT junction.file_id
            FROM tags_id_files_id AS junction
            JOIN tags ON tags.id = junction.tag_id
            WHERE tags.tag_name IN ({})
            GROUP BY junction.file_id
            HAVING COUNT(DISTINCT tags.tag_name) = ?);
    '''.format(','.join(['?'] * len(tags))),
    tags + [len(tags)])
    return cur.fetchall()

@db_wrapper
def search_all(cur, con):
    # only return those attributes needed for displaying results
    cur.execute('''
        SELECT files.id, files.coverpath, files.title,
        files.numpages, files.author, files.filesize 
        FROM files
    ''')
    return cur.fetchall()

'''
Parameters:

    file_id (int): the ID of the file that was requested
'''
@db_wrapper
def get_file_info(cur, con, file_id : int) -> dict:
    result = cur.execute('''
        SELECT *
        FROM files
        WHERE files.id = ?;
    ''', (file_id,)).fetchone()
    if result == None:
        return False
    (title, author, pubdate, uploaddate, sourcelink, 
     coverpath, filepath, numpages, filesize, 
     filetype, md5, sha1, sha256, _) = result
    return {
        'title' : title,
        'author' : author,
        'pubdate' : pubdate,
        'uploaddate' : uploaddate,
        'sourcelink' : sourcelink,
        'coverpath' : coverpath,
        'filepath' : filepath,
        'numpages' : numpages,
        'filesize' : filesize,
        'filetype' : filetype,
        'md5' : md5,
        'sha1' : sha1,
        'sha256' : sha256,
        'id' : file_id
    }

@db_wrapper
def get_download_attrs(cur, con, file_id : int) -> dict:
    result = cur.execute('''
        SELECT title, author, filepath
        FROM files
        WHERE files.id = ?;
    ''', (file_id,)).fetchone()
    if result == None:
        return False
    (title, author, filepath) = result
    return {
        'title' : title,
        'author' : author,
        'filepath' : filepath,
        'id' : file_id
    }

if __name__ == '__main__':
    # test that decorator works
    print(head('tags', 3))
