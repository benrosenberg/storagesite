import boto3
import io
import base64

s3 = boto3.client('s3', region_name='us-east-2')

BUCKETNAME = 'storagesite-filebucket'
S3_FILE_PATH = 'files/'
S3_COVER_PATH = 'covers/'

def upload_file(local_dirpath, filename):
    s3.upload_file(local_dirpath, BUCKETNAME, S3_FILE_PATH + filename)
    return filename

def delete_file(filename):
    s3.delete_object(Bucket=BUCKETNAME, Key=S3_FILE_PATH + filename)

def retrieve_file_url(filename):
    return s3.generate_presigned_url(
        'get_object', 
        Params={
            'Bucket' : BUCKETNAME,
            'Key' : S3_FILE_PATH + filename
        },
        ExpiresIn=60
    )

def retrieve_file_as_bytes(filename):
    try:
        object = s3.get_object(Bucket=BUCKETNAME, Key=S3_FILE_PATH + filename)
        data = object['Body'].read()
        return True, io.BytesIO(data)
    except:
        return False, 'unable to access file {} due to uncomprehensible reasons'.format(filename)

def upload_file_directly(file_bytes, filename):
    file_bytes.seek(0)
    s3.put_object(Body=file_bytes, Bucket=BUCKETNAME, Key=S3_FILE_PATH + filename)
    return filename

def upload_cover(local_dirpath, filename):
    s3.upload_file(local_dirpath, BUCKETNAME, S3_COVER_PATH + filename)
    return filename

def delete_cover(filename):
    s3.delete_object(Bucket=BUCKETNAME, Key=S3_COVER_PATH + filename)

def retrieve_cover_url(filename):
    return s3.generate_presigned_url(
        'get_object', 
        Params={
            'Bucket' : BUCKETNAME,
            'Key' : S3_COVER_PATH + filename
        },
        ExpiresIn=60
    )

def retrieve_cover_as_base64_jpg_src(filename):
    try:
        object = s3.get_object(Bucket=BUCKETNAME, Key=S3_COVER_PATH + filename)
        data = object['Body'].read()
        return 'data:image/jpeg;base64,{}'.format(str(base64.b64encode(data))[2:-1])
    except:
        return '/static/images/no_cover_image_found.jpg'

def upload_PIL_image_cover(image, filename, format='jpeg'):
    print(image)
    print(filename)
    in_mem_file = io.BytesIO()
    print('created in mem file')
    image.save(in_mem_file, format=format)
    print('saved image inmemfile')
    in_mem_file.seek(0)
    s3.upload_fileobj(
        in_mem_file,
        BUCKETNAME,
        S3_COVER_PATH + filename
    )
    print('uploaded to s3')
    return filename

if __name__ == '__main__':
    # test upload file
    # upload_file('./tag searching/todo.md', 'test.md')

    # test delete file
    # delete_file('test.md')

    # test direct s3 file upload
    # with open('./tag searching/static/files/6.pdf', 'rb') as f:
    #     upload_file_directly(f, 'test_bytes_upload.pdf')

    # test upload cover
    # upload_cover('./tag searching/covers/1.jpg', 'test.jpg')

    # test delete cover
    # delete_cover('test cover.jpg')

    # test retrieve file
    # print(retrieve_file_url('test.md'))

    # test retrieve cover
    # print(retrieve_cover_url('test.jpg'))

    # test upload PIL cover image
    # from PIL import Image
    # with open('./tag searching/static/covers/1.jpg', 'rb') as f:
    #     im = Image.open(f)
    #     print(upload_PIL_image_cover(im, 'test PIL image.jpg'))

    # test retrieve jpg from s3 as base64
    # out = retrieve_cover_as_base64_jpg_src('15.jpg')
    # print(out)

    pass