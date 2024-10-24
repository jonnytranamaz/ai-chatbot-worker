from django.shortcuts import render
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
from .constants import intent_files
import yaml
import logging

# Get an instance of a logger
#logger = logging.getLogger(__name__)
# Create your views here.
@api_view(['GET'])
def get_latest_model(request):
    # Get the directory of the current file (views.py)
    current_file_dir = os.path.dirname(__file__)
    # Navigate to the 'models' folder within the 'api' directory
    folder_path = os.path.join(current_file_dir, 'nlu-models')

    try:

        tar_file_basename, tar_file_path = get_latest_file_in_folder(folder_path)
        
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
    return os.path.basename(latest_file), latest_file

@api_view(['GET'])
def train_model(request):
    print("Training model here")
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

        
        #result = subprocess.run(['rasa', 'train'], cwd=folder_path, capture_output=True, text=True, check=True)
        result = subprocess.call(['rasa', 'train'], cwd=folder_path, shell=True)
        print(result,' - ', result.stderr, ' - ', result.args)
        # Capture the output
       # output = result.stdout
        #print(output, ' - ', result.stderr, ' - ', result.args)
        
        # logger.debug("Output: %s", output)
        # logger.debug("Error: %s", result.stderr)
        # logger.debug("Args: %s", result.args)

    except subprocess.CalledProcessError as e:
        # Handle errors
        output = f"An error occurred: {e}"
        print(output)
    
    except Exception as e:
        print(e)
        return Response({'error': str(e)}, status=400)
    return Response({'message': 'train success'}, status=200)

class ConvertData(APIView):
    # Disable authentication and authorization
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if serializer.is_valid():
            question = serializer.validated_data['question']
            answer = serializer.validated_data['answer']

            intents = self.get_intents_from_api()

            self.process_data(intents, question, answer)

            return Response({"message": "Dữ liệu đã được thêm vào file thành công"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
