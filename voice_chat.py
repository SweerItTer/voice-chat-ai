from audio_handler import audio_handler
from openai_interface import OpenAIInterface
import threading
import io
import os
import sys

def get_openai_api_key():
    # If the user hasn't provided it, check the environment variables
    if sys.platform == "win32":
        import winreg
        try:
            # First check user environment variables
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                return winreg.QueryValueEx(key, "OPENAI_API_KEY")[0]
        except WindowsError:
            try:
                # If not in user environment variables, check system environment variables
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as key:
                    return winreg.QueryValueEx(key, "OPENAI_API_KEY")[0]
            except WindowsError:
                pass
    else:
        # For non-Windows systems, directly use os.environ
        return os.environ.get("OPENAI_API_KEY")
    
    # If not found, raise an exception
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Get OpenAI API key using the new function
OPENAI_API_KEY = get_openai_api_key()

openai_interface = OpenAIInterface(OPENAI_API_KEY)
ai_speaking = False

def process_user_input():
    global ai_speaking
    while True:
        audio_data = audio_handler.get_audio_data()
        if audio_data:
            user_input = openai_interface.speech_to_text(audio_data)
            print(f"You said: {user_input}")
            
            if user_input:
                ai_speaking = True
                gpt_response = openai_interface.chat_with_gpt(user_input)
                print(f"AI: {gpt_response}")
                
                if not ai_speaking:  # If the user hasn't interrupted the AI
                    audio_response = openai_interface.text_to_speech(gpt_response)
                    audio_handler.play_audio(io.BytesIO(audio_response))
                
                ai_speaking = False

def main():
    print("Listening... Speech will be automatically recorded when detected. Press Ctrl+C to exit.")
    
    audio_handler.start_listening()
    
    processing_thread = threading.Thread(target=process_user_input)
    processing_thread.start()
    
    try:
        processing_thread.join()
    except KeyboardInterrupt:
        print("Exiting program...")
        audio_handler.stop_listening()

if __name__ == "__main__":
    main()
