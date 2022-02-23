import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """


def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def get_session_attributes(intent_request):
    if intent_request['sessionAttributes'] is not None:
        return intent_request['sessionAttributes']
    else:
        return {}


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

"""--- ---"""

def validate_dining_suggestions(location, cusine, num_of_people, date, time,  email):
    location_list = ["manhattan downtown", "manhattan midtown", "Mmanhattan uptown", "bronx", 
                        "brooklyn", "queens", "harlem"]
    cusine_types = ["italian", "american", "mediterrancean", "chinese", "indian", "spanish", "thai",
                    "japanese", "greek", "french", "turkish"]

    if location is not None and location.lower() not in location_list:
        return build_validation_result(False,
                                       'Location',
                                       'We do not have restaurants in {} area, would you like to dine in another area?'.format(location))
        
    if cusine is not None and cusine.lower() not in cusine_types:
        return build_validation_result(False,
                                       'Cuisine',
                                       'We do not have {} restaurants, would you like to try another cuisine?'.format(cusine))

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand that, what date would you like dine in?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'Date', 'You can choose a date from tomorrow onwards.  What day would you like?')

    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', None)

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'Time', None)
    
    if num_of_people is not None:
        if not num_of_people.isdigit() or int(num_of_people) <= 1:
            return build_validation_result(False, 'NumberOfPeople', None)

    return build_validation_result(True, None, None)

""" --- Functions that control the bot's behavior --- """
def greeting(intent_request):
    session_attributes = get_session_attributes(intent_request)
    text = "Hi there, how can I help you?"
    fulfillment_state = "Fulfilled"  
    message =  {
            'contentType': 'PlainText',
            'content': text
        }  
    return close(intent_request, session_attributes, fulfillment_state, message)

def dining_suggestions(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    location = get_slots(intent_request)["Location"]
    cusine = get_slots(intent_request)["Cuisine"]
    num_of_people = get_slots(intent_request)["NumberOfPeople"]
    date = get_slots(intent_request)["Date"]
    time = get_slots(intent_request)["Time"]
    email = get_slots(intent_request)["Email"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestions(location, cusine, num_of_people, date, time,  email)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                              intent_request['currentIntent']['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'])

        session_attributes = get_session_attributes(intent_request)
        
        return delegate(session_attributes, get_slots(intent_request))
    
    # send info to sqs Q1
    sqs_client = boto3.client('sqs')
    sqs_url = 'https://sqs.us-east-1.amazonaws.com/261903827858/Q1'
    msg_info = {"Cuisine": cusine, "Location":location, "Date": date, "Time": time, "NumberOfPeople":num_of_people,"Email":email}
    print("message to sent is {}".format(msg_info))
   # print(res_info)
    try:
        response = sqs_client.send_message(QueueUrl=sqs_url,
                                      MessageBody=json.dumps(msg_info))
    except ClientError as e:
        print('Error', e.response['Error']['Message'])
    else:
        print(response)
        

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': "Your information is stored. We will send you some suggestions shortly. Thank you!"})


def thank_you(intent_request):
    session_attributes = get_session_attributes(intent_request)
    text = "You are welcome! See you soon!"
    fulfillment_state = "Fulfilled"
    message =  {
            'contentType': 'PlainText',
            'content': text
        }    
    return close(intent_request, session_attributes, fulfillment_state, message)


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you(intent_request)
    elif intent_name == 'GreetingIntent':
        return greeting(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)