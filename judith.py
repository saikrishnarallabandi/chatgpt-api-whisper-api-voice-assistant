import gradio as gr
import os
import openai, config, subprocess
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import concurrent.futures

client = OpenAI()
prompt_audio = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
    Figure out what your user needs and try to help them as much as you can. \
    Remember to respond in 20 words or less.'
prompt_text = 'You are Judith, a personal AI assistant. Your job is to help the user to the best of your abilities \
    Figure out what your user needs and try to help them as much as you can. '
        
messages = [{"role": "system", "content": prompt_text}]
messages_audio = [{"role": "system", "content": prompt_audio}]


def get_text_response(messages):
    response = client.chat.completions.create(model="gpt-3.5-turbo-1106", messages=messages)
    system_message = response.choices[0].message.content
    messages.append({"role": "system", "content": system_message})
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

        audio_filename_with_extension = audio + '.wav'
        os.rename(audio, audio_filename_with_extension)
    
        r = sr.Recognizer()
        with sr.AudioFile(audio_filename_with_extension) as source:
            audio_data = r.record(source)
            transcript = r.recognize_google(audio_data)

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
    tts.save('output.mp3')       

    return chat_transcript, transcript, 'output.mp3'

ui = gr.Interface(
    fn=transcribe, 
    inputs=[gr.Audio(type="filepath"), gr.Textbox(lines=2, placeholder='Enter your text here...')], 
    outputs=[gr.HTML(label="Conversation"), gr.Textbox(label="Current Utterance"), gr.Audio(type="filepath", label="TTS Output", autoplay=True, visible=False)]
)
ui.launch()
