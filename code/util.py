import os
import random
import string
import datetime
import speech_recognition as sr
from openai import OpenAI


class JudithBase:
    def __init__(self, exp_name=None):
        self.client = OpenAI()
        self.prompt_text = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
            Figure out what your user needs and try to help them as much as you can. '
        self.messages = [{"role": "system", "content": self.prompt_text}]
        self.init_exp(exp_name)

    def init_logs(self):
        with open(f'{self.exp_dir}/logfile', 'w') as f:
            f.write(self.prompt_text + '\n')
        
    def add_log(self, message):
        with open(f'{self.exp_dir}/logfile', 'a') as f:
            f.write(message + '\n')
                
    def init_exp(self, name=None):
        self.random_code, self.current_date, self.time = self.generate_random_code()
        name_str = name if name is not None else 'convo'
        self.exp_name = (
            f"judith-gradle-{name_str}-{self.current_date}-"
            + self.time.replace(":", "-")
            + '-'
            + self.random_code
        )
        self.exp_dir = f'../exp/{self.exp_name}'
        os.mkdir(self.exp_dir)
        
            
    def generate_random_code(self):
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        return code, date, time


    def get_text_response(self, messages, search_array = None):
        if search_array is not None:
            search_results = ' \n '.join(k.description for k in search_array)
            
            messages.append(
            {
                "role": 'system',
                'content': f' You can use the following search context: {search_results}',
            }
            )
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106", messages=messages
        )
        system_message = response.choices[0].message.content
        messages.append({"role": "system", "content": system_message})
        with open(f'{self.exp_dir}/logfile', 'a') as f:
            f.write(f'Julia: {system_message}' + '\n')
        return system_message, messages

    
class Judith(JudithBase):
    def __init__(self):
        super().__init__()

        self.prompt_audio = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
            Figure out what your user needs and try to help them as much as you can. \
            Remember to respond in 20 words or less.'
        
        self.messages_audio = [{"role": "system", "content": self.prompt_audio}]

        
    def get_audio_response(self, messages_audio, search_array = None):
        if search_array is not None:
            search_results = '\n'.join(k.description for k in search_array)
    
            messages_audio.append(
                {
                "role": 'system',
                'content': f' You can use the following search context: {search_results}',
                }
            )
        response_audio = self.client.chat.completions.create(
            model="gpt-3.5-turbo-1106", messages=messages_audio)

        system_message_audio = response_audio.choices[0].message.content
        messages_audio.append({"role": "system", "content": system_message_audio})
        return system_message_audio, messages_audio
    
