import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from decimal import Decimal

def insert_data(data_list, db=None, table='yelp-nyc-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    for data in data_list:
        data["insertion_timestamp"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        response = table.put_item(Item=data)
    print('@insert_data: response', response)
    return response


def lookup_data(key, db=None, table='yelp-nyc-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.get_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response['Item'])
        return response['Item']


def update_item(key, feature, db=None, table='yelp-nyc-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    # change student location
    response = table.update_item(
        Key=key,
        UpdateExpression="set #feature=:f",
        ExpressionAttributeValues={
            ':f': feature
        },
        ExpressionAttributeNames={
            "#feature": "from"
        },
        ReturnValues="UPDATED_NEW"
    )
    print(response)
    return response


def delete_item(key, db=None, table='yelp-nyc-restaurants'):
    if not db:
        db = boto3.resource('dynamodb')
    table = db.Table(table)
    try:
        response = table.delete_item(Key=key)
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response)
        return response

def lambda_handler(event, context):

    cuisines = [ "italian-restaurant", "french-restaurant", "chinese-restaurant", "spanish-restaurant",
            "japanese-restaurant", "greek-restaurant", "turkish-restaurant", "american-restaurant"]
    
            
    for cuisine in cuisines:
        file_name = cuisine + '.json'
        with open(file_name) as json_file:
            businesses = json.load(json_file, parse_float=Decimal)
            insert_data(businesses)
            print(file_name + ": " + str(len(businesses)))
    return