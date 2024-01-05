import gradio as gr
import os
import speech_recognition as sr
from gtts import gTTS
import concurrent.futures
from util import Judith


judith = Judith()


def do_conversation(audio=None, input_data=None):


    if audio is not None: input_data = None 

    if isinstance(input_data, str):
        # Handle text input
        transcript = input_data

    else:
        audio_filename_with_extension = (
            f'{exp_dir}/input_{str(len(messages_audio) + 1).zfill(3)}.wav'
        )
        os.rename(audio, audio_filename_with_extension)

        r = sr.Recognizer()
        with sr.AudioFile(audio_filename_with_extension) as source:
            audio_data = r.record(source)
            transcript = r.recognize_google(audio_data)

    judith.add_log(f'User: {transcript}')

    judith.messages.append({"role": "user", "content": transcript})
    judith.messages_audio.append({"role": "user", "content": transcript})

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_text = executor.submit(judith.get_text_response, judith.messages)
        future_audio = executor.submit(judith.get_audio_response, judith.messages_audio)

    _, messages = future_text.result()
    system_message_audio, messages_audio = future_audio.result()

    chat_transcript = "".join(
        "<p style='color:green;'>" + "JULIA: " + message['content'] + "</p>"
        if message['role'] == 'system'
        else "<p style='color:blue; text-align:right;'>"
        + "User: "
        + message['content']
        + "</p>"
        for ctr, message in enumerate(messages)
        if ctr != 0
    )
    tts = gTTS(system_message_audio, lang='en')
    audio_fname = f'{judith.exp_dir}/output_{str(len(messages_audio)).zfill(3)}.mp3'
    tts.save(audio_fname)       

    return chat_transcript, transcript, audio_fname

ui = gr.Interface(
    fn=do_conversation, 
    inputs=[gr.Audio(type="filepath"), gr.Textbox(lines=2, placeholder='Enter your text here...')], 
    outputs=[gr.HTML(label="Conversation"), gr.Textbox(label="Current Utterance"), gr.Audio(type="filepath", label="TTS Output", autoplay=True, visible=False)]
)
ui.launch()
