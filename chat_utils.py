import numpy as np
import ast
import base64

import openai
from openai import OpenAI

import os


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
  
def chat_with_gpt4v(chat_history):
    retries = 10    
    while retries > 0:  
        try: 
            response = client.chat.completions.create(
                model='o1', 
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


# def chat_with_gpt4v(chat_history, gpt_type = args.gpt_type):
    
#     headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
#     retries = 10    
#     while retries > 0:  
#         try: 
#             payload = {
#                 "model": 'gpt-4o',
#                 "response_format": { "type": "json_object" },
#                 "temperature": 1.1,
#                 "messages": chat_history,
#                 "max_tokens": 100
#             }
            
#             response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

#             response_message = response.json()["choices"][0]["message"]["content"]
#             # print(response_message)
#             try:
#                 ground_json = ast.literal_eval(response_message)
#                 break
                
#             except (SyntaxError, ValueError) as e:
#                 print(e)
#         except OpenAIError as e:
#             if e:
#                 print(e)
#                 print('Timeout error, retrying...')    
#                 retries -= 1
#                 time.sleep(5)
#             else:
#                 raise e
            
#     print(response_message)
#     return response_message

