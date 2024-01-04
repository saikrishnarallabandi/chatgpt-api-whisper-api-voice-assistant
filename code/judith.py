import gradio as gr
import os
import openai
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import random
import string
import datetime
import concurrent.futures

def generate_random_code():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    return code, date, time

random_code, current_date, time = generate_random_code()
exp_name = "judith-gradle-" + current_date + "-" +  time.replace(":", "-") + '-' +  random_code 
exp_dir = '../exp/' + exp_name
os.mkdir(exp_dir)

client = OpenAI()
prompt_audio = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
    Figure out what your user needs and try to help them as much as you can. \
    Remember to respond in 20 words or less.'
prompt_text = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
    Figure out what your user needs and try to help them as much as you can. '
       
f = open(exp_dir + '/' + 'logfile', 'w')
f.write(prompt_text + '\n')
f.close()

        
messages = [{"role": "system", "content": prompt_text}]
messages_audio = [{"role": "system", "content": prompt_audio}]


def get_text_response(messages):
    response = client.chat.completions.create(model="gpt-3.5-turbo-1106", messages=messages)
    system_message = response.choices[0].message.content
    messages.append({"role": "system", "content": system_message})
    f = open(exp_dir + '/' + 'logfile', 'a')
    f.write('Julia: ' +  system_message + '\n')
    f.close()
    
    return system_message, messages

def get_audio_response(messages_audio):
    response_audio = client.chat.completions.create(model="gpt-3.5-turbo-1106", messages=messages_audio)
    system_message_audio = response_audio.choices[0].message.content
    messages_audio.append({"role": "system", "content": system_message_audio})
    return system_message_audio, messages_audio
    

def transcribe(audio=None, input_data=None):

    global messages, messages_audio

    if audio is not None: input_data = None 
    
    if isinstance(input_data, str):
        # Handle text input
        transcript = input_data
    
    else:    

        audio_filename_with_extension = exp_dir + '/input_' + str(len(messages_audio)+1).zfill(3) + '.wav'
        os.rename(audio, audio_filename_with_extension)
    
        r = sr.Recognizer()
        with sr.AudioFile(audio_filename_with_extension) as source:
            audio_data = r.record(source)
            transcript = r.recognize_google(audio_data)

    f = open(exp_dir + '/' + 'logfile', 'a')
    f.write('User: ' +  transcript + '\n')
    f.close()
 
    messages.append({"role": "user", "content": transcript})
    messages_audio.append({"role": "user", "content": transcript})



    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_text = executor.submit(get_text_response, messages)
        future_audio = executor.submit(get_audio_response, messages_audio)

    system_message, messages = future_text.result()
    system_message_audio, messages_audio = future_audio.result()


    #subprocess.call(["say", system_message])

    chat_transcript = ""
    for ctr, message in enumerate(messages):
        if ctr == 0: continue
        if message['role'] == 'system':
            chat_transcript += "<p style='color:green;'>" +  "JULIA: " + message['content'] + "</p>"
        else:
            chat_transcript += "<p style='color:blue; text-align:right;'>" +  "User: " + message['content'] + "</p>"

            
    tts = gTTS(system_message_audio, lang='en')
    audio_fname = exp_dir + '/' + 'output_' + str(len(messages_audio)).zfill(3) + '.mp3'
    tts.save(audio_fname)       

    return chat_transcript, transcript, audio_fname

ui = gr.Interface(
    fn=transcribe, 
    inputs=[gr.Audio(type="filepath"), gr.Textbox(lines=2, placeholder='Enter your text here...')], 
    outputs=[gr.HTML(label="Conversation"), gr.Textbox(label="Current Utterance"), gr.Audio(type="filepath", label="TTS Output", autoplay=True, visible=False)]
)
ui.launch()
