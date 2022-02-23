import boto3
import json

# Define the client to interact with Lex
client = boto3.client('lex-runtime')
def lambda_handler(event, context):
    print(event['messages'])
    msg_from_user = event['messages'][0]['unstructured']['text']
    last_user_message = msg_from_user
    
    
    print(f"Message from frontend: {last_user_message}")
    response = client.post_text(botName='DiningSuggestionsChatbot',
                                botAlias='LexBot',
                                userId='testuser',
                                inputText=last_user_message)
    
    msg_from_lex = response['message']
    if msg_from_lex:
        print(f"Message from Chatbot: {msg_from_lex}")
        print(response)
        
        unstructured_message = {
            'text': msg_from_lex
        }
        
        message = {
            'type': 'unstructured',
            'unstructured': unstructured_message
        }
        
        lexBotResponse =  [message]
        

        resp = {
            'statusCode': 200,
            'messages':  lexBotResponse
        }
        # modify resp to send back the next question Lex would ask from the user
        
        # format resp in a way that is understood by the frontend
        # HINT: refer to function insertMessage() in chat.js that you uploaded
        # to the S3 bucket
        return  resp
