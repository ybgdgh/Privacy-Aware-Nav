import numpy as np
import ast
import os
import time
import requests
import json
import base64

import openai
from openai.error import OpenAIError
api_key = "xxx"


def message_prepare(prompt, candidate_map_list, navigation_instruct):
    base64_image_list = []
    for image_candidate in candidate_map_list:
        base64_image_list.append(base64.b64encode(image_candidate.getvalue()).decode("utf-8"))


    message = []
    message.append({"role": "system", "content": prompt})

    image_contents = []
    image_contents.append({
        "type": "text",
        "text": navigation_instruct,
    })
    for base64_image in base64_image_list:
        image_contents.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    message.append({"role": "user", "content": image_contents})
    
    return message

def chat_with_gpt4v(messages):
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    retries = 10    
    while retries > 0:  
        try: 
            payload = {
                "model": 'gpt-4-turbo',
                "response_format": { "type": "json_object" },
                "temperature": 0.5,
                "messages": messages,
                "max_tokens": 300
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

            response_message = response.json()["choices"][0]["message"]["content"]
            # print(response_message)
            print('gpt-4o' + " response: ")
            print(response_message)
            
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
            
    return response_message

