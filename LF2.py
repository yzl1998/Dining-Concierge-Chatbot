import json
import boto3
import random
import requests
from requests_aws4auth import AWS4Auth
#from openSearchQuery import get_from_open_search, get_from_DynamoDB

def get_from_open_search(cuisine):
    host = 'https://search-yelp-nyc-restaurants-5kmezcttm7vqzsk2djyxtjorby.us-east-1.es.amazonaws.com/_search/'
    region = 'us-east-1'

    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    
    url = host
    headers = { "Content-Type": "application/json" }
    query = {
        "size": 5,
        "query": {
            "multi_match": {
                "query": cuisine
            }
        }
    }
    
    es_response = requests.get(url, auth=awsauth, headers=headers, data=json.dumps(query))
    es_restaurants =  json.loads(es_response.text)['hits']['hits']
    restaurant_ids = []
    
    for index, restaurant in enumerate(es_restaurants):
        restaurant_id = restaurant['_source']['id']
        print("Restaurant id: " + restaurant_id)
        restaurant_ids.append(restaurant_id)
    
    return restaurant_ids
    

def get_from_DynamoDB(restaurant_ids):
    dynamo = boto3.client('dynamodb')
    restaurants = []
    for restaurant_id in restaurant_ids:
        restaurant = {}
        try:
            response = dynamo.get_item(
            TableName="yelp-nyc-restaurants",
            Key={
                "id": {
                    "S": restaurant_id
                    }
                }
            )   
        except ClientError as e:
            print('Error', e.response['Error']['Message'])
        else:
            restaurant['name'] = response['Item']['name']['S']
            restaurant['address'] = (response['Item']['location']['M']['display_address']['L'][0]['S'] + ", " 
                             +  response['Item']['location']['M']['display_address']['L'][1]['S'])
            restaurant['phone']= response['Item']['display_phone']['S']
            restaurants.append(restaurant)
            
    return restaurants


def recommend(cuisine):
    ids = get_from_open_search(cuisine)
    ids = random.sample(ids,3)
    print(ids)
    results = get_from_DynamoDB(ids)
    print(results)
    return results
    

def send_email(email, content):
    ses_client = boto3.client("ses", region_name="us-east-1")
    CHARSET = "UTF-8"

    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                email,
            ],
        },
        Message={
            "Body": {
                "Text": {
                    "Charset": CHARSET,
                    "Data": content,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Test",
            },
        },
        Source="cyixing961@gmail.com",
    )
        

def lambda_handler(event, context):
    
    print(event['Records'][0]['body'])
    message = json.loads(event['Records'][0]['body'])
    
    cuisine = message["Cuisine"]
    location = message["Location"]
    date = message["Date"]
    time = message["Time"]
    number = message["NumberOfPeople"]
    email_address = message["Email"]
    """
    cuisine ="chinese"
    number = 3
    date = "tomorrow"
    time = "6pm"
    email_address = "zy2496@columbia.edu"
    """
    recommends = recommend(cuisine)
    cuisine = cuisine.capitalize()
    
    email_message = "Hello! Here are my {} restaurant suggestions for {} people, on {} {}. 1. {}, located at {}, 2. {}, located at {}, 3. {}, located at {}. Enjoy your meal!".format(cuisine, number, date, time, recommends[0]["name"],recommends[0]["address"],
        recommends[1]["name"],recommends[1]["address"],recommends[2]["name"],recommends[2]["address"])
        
    print(email_message)
    send_email(email_address, email_message)