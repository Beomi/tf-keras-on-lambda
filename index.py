import boto3  # AWS S3 접근용
from tensorflow.python import keras  # Keras!
from tensorflow.python.keras.preprocessing import image
from tensorflow.python.keras.applications.resnet50 import preprocess_input, decode_predictions
import numpy as np
import io  # File 객체를 메모리상에서만 이용하도록
import os  # os.path / os.environ
from PIL import Image  # Image 객체
import urllib.request  # 파일받기
import h5py

# (.h5경로변경추가, 레포의 squeezenet.py를 확인하세요.)
from squeezenet import SqueezeNet

ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')


def downloadFromS3(strBucket, s3_path, local_path):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    s3_client.download_file(strBucket, s3_path, local_path)


def uploadToS3(bucket, s3_path, local_path):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
    )
    s3_client.upload_file(local_path, bucket, s3_path)


def predict(img_local_path):
    model = SqueezeNet(weights='imagenet')
    img = image.load_img(img_local_path, target_size=(227, 227))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)
    preds = model.predict(x)
    res = decode_predictions(preds)
    return res


def handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    file_path = event['Records'][0]['s3']['object']['key']
    file_name = file_path.split('/')[-1]
    downloadFromS3(bucket_name, file_path, '/tmp/' + file_name)
    downloadFromS3(
        'keras-blog',
        'squeezenet/squeezenet_weights_tf_dim_ordering_tf_kernels.h5',
        '/tmp/squeezenet_weights_tf_dim_ordering_tf_kernels.h5'
    )  # weights용 h5를 s3에서 받아오기

    print(os.path.exists('/tmp/squeezenet_weights_tf_dim_ordering_tf_kernels.h5'))

    print('filename: ', '/tmp/' + file_name)
    result = predict('/tmp/' + file_name)
    _tmp_dic = {x[1]: {'N': str(x[2])} for x in result[0]}
    dic_for_dynamodb = {'M': _tmp_dic}
    dynamo_client = boto3.client(
        'dynamodb',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name='ap-northeast-2'
    )
    dynamo_client.put_item(
        TableName='keras-blog-result',  # DynamoDB의 Table이름
        Item={
            'filename': {
                'S': file_name,
            },
            'predicts': dic_for_dynamodb,
        }
    )
    return {
        'filename': {
            'S': file_name,
        },
        'predicts': dic_for_dynamodb,
    }


if __name__ == '__main__':
    print(handler({'Records': [
        {
            's3': {'bucket': {'name': 'keras-blog'},
                   'object': {'key': 'uploads/kitten.png'}
                   },
        }
    ]
    }, ''))
