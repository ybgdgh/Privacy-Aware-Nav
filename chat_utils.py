import numpy as np
import ast
import jsonschema
from jsonschema import validate
import time
import requests
import json
import base64
import openai
from openai import OpenAI
from io import BytesIO
from PIL import Image

import system_prompt

client = OpenAI()

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

def generate_message_prepare(sys_prompt, map, obs, navigation_instruct):

    message = []
    message.append({
        "role": "system", 
        "content": sys_prompt,
    })
    
    image_path = "/home/ybg/Project/Privacy-Aware-Nav/img/3_example.PNG"
    pil_image = Image.open(image_path)
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    base64_image_1 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    example_contents = []
    example_contents.append({
        "type": "text",
        "text": system_prompt.generate_path_examp_1,
    })
    example_contents.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image_1}"
        }
    })
    example_contents.append({
        "type": "text",
        "text": system_prompt.generate_path_examp_2,
    })
    
    
    image_contents = example_contents
    image_contents.append({
        "type": "text",
        "text": navigation_instruct,
    })
    base64_image = base64.b64encode(map.getvalue()).decode("utf-8")
    base64_obs= base64.b64encode(obs.getvalue()).decode("utf-8")
    image_contents.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
        },
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_obs}"
        }
    })
    message.append({"role": "user", "content": image_contents})
    
    return message

def path_message_prepare(sys_prompt, map):
    message = []
    message.append({
        "role": "system", 
        "content": sys_prompt,
    })
    
    base64_image = base64.b64encode(map.getvalue()).decode("utf-8")
    # base64_image_orignal = base64.b64encode(orignal_map.getvalue()).decode("utf-8")
    
    image_contents = []
    image_contents.append({
        "type": "image_url",
        "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
        }
    })
    message.append({"role": "user", "content": image_contents})
    
    return message
    
def critique_message_prepare(prompt, candidate_map_list):
    base64_image_list = []
    for image_candidate in candidate_map_list:
        base64_image_list.append(base64.b64encode(image_candidate.getvalue()).decode("utf-8"))


    message = []
    
    image_contents = []
    image_contents.append({
        "type": "text",
        "text": prompt,
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
    
def chat_with_gpt4v(chat_history):
    retries = 10    
    while retries > 0:  
        try: 
            response = client.chat.completions.create(
                model='gpt-4o', 
                response_format = { "type": "json_object" },
                messages = chat_history,
                # temperature=0.1,
                # max_tokens=300,
            )

            response_message = response.choices[0].message.content
            print('gpt-4o' + " response: ")
            print(response_message)
            try:
                ground_json = ast.literal_eval(response_message)

                return ground_json
                
            except (SyntaxError, ValueError) as e:
                print(response_message)
        except openai.APIError as e:
            #Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            pass
        except openai.APIConnectionError as e:
            #Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            pass
        except openai.RateLimitError as e:
            #Handle rate limit error (we recommend using exponential backoff)
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass
        retries -=1
            
    # print(ground_json)
    ground_json = {
                    "path": "",
                    }
    return ground_json

