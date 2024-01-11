import gradio as gr
import os
import speech_recognition as sr
from gtts import gTTS
import concurrent.futures
from util import JudithBase, Judith
from googlesearch import Search

num_search_results = 3
search_flag = False
judith_convo = Judith()
judith_convo.init_logs()

judith_intent = JudithBase('intent')
judith_intent.prompt_text = 'Identify the meta intent of the user. Dont answer the individual question. \
    Just identify the higher level intent user might have for asking the series of question(s).' 
judith_intent.messages = [{"role": "system", "content": judith_intent.prompt_text}]
judith_intent.init_logs()


def get_transcript(audio=None, input_data=None):

    if audio is not None: input_data = None 

    if isinstance(input_data, str):
        # Handle text input
        transcript = input_data

    else:
        audio_filename_with_extension = (
            f'{judith_convo.exp_dir}/input_{str(len(judith_convo.messages_audio) + 1).zfill(3)}.wav'
        )
        os.rename(audio, audio_filename_with_extension)

        r = sr.Recognizer()
        with sr.AudioFile(audio_filename_with_extension) as source:
            audio_data = r.record(source)
            transcript = r.recognize_google(audio_data)

    return transcript        

def do_conversation(audio=None, input_data=None):

    # Obtain transcript
    transcript = get_transcript(audio, input_data)

    judith_convo.add_log(f'User: {transcript}')
    judith_intent.add_log(f'User: {transcript}')
    
    if search_flag: 
        search_results = Search(transcript, number_of_results=num_search_results).results
    else:
        search_results = None

    judith_convo.messages.append({"role": "user", "content": transcript})
    judith_convo.messages_audio.append({"role": "user", "content": transcript})
    judith_intent.messages.append({"role": "user", "content": transcript})

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_text = executor.submit(judith_convo.get_text_response, judith_convo.messages, search_results)
        future_audio = executor.submit(judith_convo.get_audio_response, judith_convo.messages_audio, search_results)
        future_intent = executor.submit(judith_intent.get_text_response, judith_intent.messages) 

    _, messages = future_text.result()
    system_message_audio, messages_audio = future_audio.result()
    system_message_intent, messages_intent = future_intent.result()

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
    audio_fname = f'{judith_convo.exp_dir}/output_{str(len(messages_audio)).zfill(3)}.mp3'

    intent_list = "\n\n".join(message['content'] for message in messages_intent[1:] if message['role'] == 'system')
    print(intent_list)

    tts.save(audio_fname)       

    return chat_transcript, intent_list, audio_fname


ui = gr.Interface(
    fn=do_conversation, 
    inputs=[gr.Audio(type="filepath"), 
            gr.Textbox(lines=2, placeholder='Enter your text here...')], 
    outputs=[gr.HTML(label="Conversation"), 
             gr.Textbox(label="Intent"), 
             gr.Audio(type="filepath", label="TTS Output", autoplay=True, visible=False)]
)
ui.launch(share=False)
