import numpy as np
import ast
import jsonschema
from jsonschema import validate
from utils.json_validate import schema
import time
import requests
import json
from arguments import get_args


gpt_name = [
            'text-davinci-003',
            'gpt-3.5-turbo-0125',
            'gpt-4o',
            'gpt-4o-mini'
        ]           

args = get_args()

import openai
from openai.error import OpenAIError
api_key = "xx-xxx"



def chat_with_gpt4v(chat_history, gpt_type = args.gpt_type):
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    retries = 10    
    while retries > 0:  
        try: 
            payload = {
                "model": 'gpt-4o',
                "response_format": { "type": "json_object" },
                "temperature": 1.1,
                "messages": chat_history,
                "max_tokens": 100
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            response_message = response.json()["choices"][0]["message"]["content"]
            # print(response_message)
            try:
                ground_json = ast.literal_eval(response_message)
                break
                
            except (SyntaxError, ValueError) as e:
                print(e)
        except OpenAIError as e:
            if e:
                print(e)
                print('Timeout error, retrying...')    
                retries -= 1
                time.sleep(5)
            else:
                raise e
            
    print(response_message)
    return response_message

