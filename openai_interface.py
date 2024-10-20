import openai
import io

class OpenAIInterface:
    def __init__(self, api_key):
        openai.api_key = api_key

    def speech_to_text(self, audio_data):
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "speech.wav"
        
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        return transcript["text"]

    def chat_with_gpt(self, prompt):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def text_to_speech(self, text):
        response = openai.Audio.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
