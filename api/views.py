import json
from django.shortcuts import render
import httpx
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
import tarfile
import io
import hashlib
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
import os
import glob
import subprocess
from rest_framework import status, permissions
from .serializer import ChatRequestSerializer
from .train_intent import get_intent_from_question
from .constants import *
import yaml
import logging

# Get an instance of a logger
#logger = logging.getLogger(__name__)
# Create your views here.
@api_view(['GET'])
def get_latest_model(request):
    # Get the directory of the current file (views.py)
    current_file_dir = os.path.dirname(__file__)
    # Get the parent folder of the parent folder of the current file
    parent_of_parent_dir = (os.path.dirname(current_file_dir)) # os.path.dirname
    # Navigate to the 'rasa-source' folder within the parent of parent directory
    folder_path = os.path.join(parent_of_parent_dir, 'rasa-source', 'models')

    print('current_file_dir: ',current_file_dir)
    print('parent_of_parent_dir: ',parent_of_parent_dir)
    print('folder_path: ',folder_path)
    try:

        tar_file_basename, tar_file_path = get_latest_file_in_folder(folder_path)
        #print('tar_file_basename: ',tar_file_basename)
        print('tar_file_path: ',tar_file_path)

        with open(tar_file_path, 'rb') as tar_file:
            tar_buffer = io.BytesIO(tar_file.read())
            tar_file.seek(0)
            file_content = tar_file.read()
            etag = hashlib.md5(file_content).hexdigest()

        response = HttpResponse(tar_buffer, content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename={}'.format(tar_file_basename)
        response['ETag'] = etag
        
        return response
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=400)

def get_latest_file_in_folder(folder_path):
    list_of_files = glob.glob(os.path.join(folder_path, '*'))
    latest_file = max(list_of_files, key=os.path.getctime)
    #print('latest_file: ',latest_file)
    return os.path.basename(latest_file), latest_file

@api_view(['GET'])
def train_model(request):
    #print("Training model here")
    try:
        current_file_dir = os.path.dirname(__file__)
        
        # Get the parent folder of the parent folder of the current file
        parent_of_parent_dir = (os.path.dirname(current_file_dir)) # os.path.dirname
        # Navigate to the 'rasa-source' folder within the parent of parent directory
        folder_path = os.path.join(parent_of_parent_dir, 'rasa-source')

        # logger.debug("current_file_dir: %s", current_file_dir)
        # logger.debug("parent_of_parent_dir: %s", parent_of_parent_dir)
        # logger.debug("path: %s", folder_path)
        
        print("current_file_dir: ",current_file_dir)
        print("parent_of_parent_dir: ",parent_of_parent_dir)
        print("path: ",folder_path)
        # Run the bash command 
        # 'dir', folder_path, '&&', 'rasa', '--version', '&&',
        # result = subprocess.run(['cmd', '/c', 'rasa', 'train', folder_path ], capture_output=True, text=True, check=True)
        
        # For Windows
        # result = subprocess.run(['rasa', 'train'], cwd=folder_path, capture_output=True, text=True, check=True)

        
        result = subprocess.run(['rasa', 'train'], cwd=folder_path, capture_output=True, text=True, check=True)
        #result = subprocess.call(['rasa', 'train'], cwd=folder_path, shell=True)
        print(result.stdout,' - ', result.stderr, ' - ', result.args)
        # Capture the output
        # output = result.stdout
        #print(output, ' - ', result.stderr, ' - ', result.args)
        
        # logger.debug("Output: %s", output)
        # logger.debug("Error: %s", result.stderr)
        # logger.debug("Args: %s", result.args)

        # Check if the training was successful
        if result.returncode == 0:
            # Delete old models
            delete_old_model(os.path.join(folder_path, 'models'))
        return Response({'message': 'train success'}, status=200)
    except subprocess.CalledProcessError as e:
        # Handle errors
        output = f"An error occurred: {e}"
        print(output)
        return Response({'error': 'Error when training models'}, status=500)
    
    except Exception as e:
        print(e)
        return Response({'error': 'Internal Server Error'}, status=500)

def delete_old_model(folder_path):
    try:
        # Get a list of all files in the folder
        list_of_files = glob.glob(os.path.join(folder_path, '*'))
        
        if not list_of_files:
            return True

        # Identify the newest file
        latest_file = max(list_of_files, key=os.path.getctime)
        
        # Delete all files except the newest one
        for file_path in list_of_files:
            if file_path != latest_file:
                os.remove(file_path)
        
        return True
    except Exception as e:
        print(e)
        return False

class ConvertData(APIView):
    # Disable authentication and authorization
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        print('request.data 1: ',request.data)#.get('data')
        data = request.data#.get('data')
        if isinstance(data, list):
            for item in data:
                question = item.get('question')
                answer = item.get('answer')
                if question and answer:
                    intents = self.get_intents_from_api()
                    self.process_data(intents, question, answer)
                else:
                    return Response({"message": "Dữ liệu bị thiếu"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Dữ liệu đã được thêm vào file thành công"}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Dữ liệu không hợp lệ, phải là mảng"}, status=status.HTTP_400_BAD_REQUEST)
        # serializer = ChatRequestSerializer(data=request.data)
        # if serializer.is_valid():
        #     question = serializer.validated_data['question']
        #     answer = serializer.validated_data['answer']

        #     intents = self.get_intents_from_api()

        #     self.process_data(intents, question, answer)

        #     return Response({"message": "Dữ liệu đã được thêm vào file thành công"}, status=status.HTTP_201_CREATED)

        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_intents_from_api(self):
        return []

    def process_data(self, intents, user_example, bot_response):

        current_file_dir = os.path.dirname(__file__)
        
        # Get the parent folder of the parent folder of the current file
        parent_of_parent_dir = (os.path.dirname(current_file_dir)) # os.path.dirname
        # Navigate to the 'rasa-source' folder within the parent of parent directory
        folder_path = os.path.join(parent_of_parent_dir, 'rasa-source')
        
        print('folder_path: ',folder_path)
        # read example of intent
        def read_examples_from_file(file_path):
            examples = set()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = yaml.safe_load(file)
                    if data and 'nlu' in data:
                        for item in data['nlu']:
                            examples.update(item['examples'].splitlines())
            return examples

        # save into nlu - intent file
        question = user_example
        bot_response = bot_response
        intent = get_intent_from_question(question).strip()
        print('intent',intent)
        if intent in intent_files:
            file_path = os.path.join(folder_path, intent_files[intent])
            existing_examples = read_examples_from_file(file_path)
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write("nlu:\n- intent: {}\n  examples: |\n".format(intent))

            if question.strip() not in {example.lstrip('- ').strip() for example in existing_examples}:
                with open(file_path, 'a', encoding='utf-8') as file:
                    file.write(f"    - {question.strip()}\n")

        responses = {f'utter_{intent}': [{'text': bot_response}]}

        domain_data = {
            'intents': [],
            'responses': {}
        }

        # save into domain
        if os.path.exists(os.path.join(folder_path, intent_files['domain'])):
            with open(os.path.join(folder_path, intent_files['domain']), 'r', encoding='utf-8') as domain_file:
                domain_data = yaml.safe_load(domain_file) or {}

        existing_intents = set(domain_data.get('intents', []))
        existing_intents.add(intent)
        domain_data['intents'] = list(existing_intents)

        for intent, response_list in responses.items():
            if intent not in domain_data.get('responses', {}):
                domain_data.setdefault('responses', {})[intent] = []
            for response in response_list:
                if response not in domain_data['responses'][intent]:
                    domain_data['responses'][intent].append(response)
                
        if 'entities' not in domain_data:
            domain_data['entities'] = []

        # Thêm intent vào entities
        if intent not in domain_data['entities']:
            domain_data['entities'].append(intent)
        
        if 'slots' not in domain_data:
            domain_data['slots'] = {}
        if intent not in domain_data['slots']:
            domain_data['slots'][intent] = {
                'type': 'text',
                'mappings': [{'type': 'from_entity', 'entity': intent}]
            }
        action_name = f'action_{intent}'
        if 'actions' not in domain_data:
            domain_data['actions'] = []
        if action_name not in domain_data['actions']:
            domain_data['actions'].append(action_name)

        with open(os.path.join(folder_path, intent_files['domain']), 'w', encoding='utf-8') as domain_file:
            domain_file.write("version: \"3.1\"\n\n")
            domain_file.write("intents:\n")
            for intent in domain_data['intents']:
                domain_file.write(f"  - {intent}\n")
            domain_file.write("\nresponses:\n")
            for intent, response_list in domain_data['responses'].items():
                domain_file.write(f"  {intent}:\n")
                for response in response_list:
                    domain_file.write(f"  - text: \"{response['text']}\"\n")

            domain_file.write("\nactions:\n")
            for action in domain_data.get('actions', []):
                domain_file.write(f"  - {action}\n")
            domain_file.write("\nentities:\n")
            for entity in domain_data.get('entities', []):
                domain_file.write(f"  - {entity}\n")
            domain_file.write("\nslots:\n")
            for slot_name, slot_info in domain_data.get('slots', {}).items():
                domain_file.write(f"  {slot_name}:\n")
                domain_file.write(f"    type: {slot_info['type']}\n")
                domain_file.write(f"    mappings:\n")
                for mapping in slot_info['mappings']:
                    domain_file.write(f"      - type: {mapping['type']}\n")
                    domain_file.write(f"        entity: {mapping['entity']}\n") 

        # save into stories
        stories_data = []
        existing_intents = set()  
        added_intents = set() 
        existing_stories = []
        if os.path.exists(os.path.join(folder_path, intent_files['stories'])):
            with open(os.path.join(folder_path, intent_files['stories']), 'r', encoding='utf-8') as stories_file:
                existing_data = yaml.safe_load(stories_file)
                if existing_data and 'stories' in existing_data:
                    existing_stories = existing_data['stories']
                    for story in existing_stories:
                        for step in story['steps']:
                            intent = step.get('intent')
                            if intent:
                                existing_intents.add(intent)
        intent = get_intent_from_question(question).strip()
        action = f'utter_{intent}'
        if intent not in existing_intents and intent not in added_intents:
            stories_data.append({
                'story': f'story_{intent}', 
                'steps': [
                    {'intent': intent},
                    {'action': action}
                ]
            })
            added_intents.add(intent)  
        with open(os.path.join(folder_path, intent_files['stories']), 'a', encoding='utf-8') as stories_file:
            for story in stories_data:
                stories_file.write(f"- story: {story['story']}\n")
                stories_file.write("  steps:\n")
                for step in story['steps']:
                    if 'intent' in step:
                        stories_file.write(f"  - intent: {step['intent']}\n")
                    if 'action' in step:
                        stories_file.write(f"  - action: {step['action']}\n")

@api_view(['GET'])
def replace_model_of_rasa(request):
    try:
        payload = {
            'model_server': {
                "url": latest_model_url,
                "params": { },
                "headers": { },
                "basic_auth": { },
                "token": "secret",
                "token_name": "access-token",
                "wait_time_between_pulls": 100
            }
        }
        headers = {
            "Content-Type":"application/json",
        }
     
        result = requests.put(
            change_model_url,
            data=json.dumps(payload),
            headers=headers
        )

        if (result and 200 <= result.status_code and result.status_code < 300):
            msg = 'replace model success'
        else:
            msg = 'replace model failed'

        return Response({'message': msg}, status=200)
    except Exception as e:
        print(e)
        return Response({'error': 'Internal Server Error'}, status=500)

@staticmethod
async def call_api_change_model(url, data):
        try:
            print('url: ',url)
            async with httpx.AsyncClient() as client:
                response = await client.put(url, json=data)
                if (200 <= response.status_code < 300):
                    return True
                return False
        except Exception as e:
            print(f'Error when calling to rasa: {e}')
            return False
        
@api_view(['POST'])
def convert_data_and_train_and_replace_model(request):
    try:
        headers = {
            "Content-Type":"application/json",
        }

        print('request.data 2: ',request.data)
        data = request.data.get('data')
        print('data: ',data)
        convert_data = requests.post(
            inference_url + '/api/v1/convertdata/', 
            data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
            headers=headers)
        
        if (convert_data and 200 <= convert_data.status_code and convert_data.status_code < 300):

            train = requests.get(inference_url + '/api/v1/models/train-model/')

            if (train and 200 <= train.status_code and train.status_code < 300):

                replace_model = requests.get(inference_url + '/api/v1/models/replace-model-of-rasa/')

                if (replace_model and 200 <= replace_model.status_code and replace_model.status_code < 300):
                    msg = 'convert data, train and replace model success'
                    status = 200

                else:
                    msg = 'replace model failed'
                    status = 500
            else:
                msg = 'train failed'
                status = 500
        else:
            msg = 'convert data failed'
            status = 400
        
        return Response({'message': msg}, status=status)

    except Exception as e:
        print(e)
        return Response({'error': 'Internal Server Error'}, status=500)