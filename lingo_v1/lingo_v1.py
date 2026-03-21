import os
import json
import time
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
client = None
if GOOGLE_API_KEY:
    client = genai.Client(api_key=GOOGLE_API_KEY)

SYSTEM_PROMPT = "You are GENIUSDEV, an AI assistant and language tutor. Maintain context across interactions."

conversation_history = []
HISTORY_FILE = "lingo_history.json"

if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            loaded_history = json.load(f)
            for entry in loaded_history:
                if isinstance(entry, dict) and 'user' in entry and 'ai' in entry:
                    conversation_history.append(entry)
    except Exception as e:
        print(f"Warning: could not load history, starting fresh. ({e})")

def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=2)

tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)

def speak_text(text):
    print(f"GENIUSDEV: {text}")
    tts_engine.say(text)
    tts_engine.runAndWait()
    time.sleep(0.2)

recognizer = sr.Recognizer()

def listen_user():
    with sr.Microphone() as source:
        print("🎤 Speak now...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            speak_text("I didn't hear anything. Please speak louder or check your mic.")
            return None
    try:
        text = recognizer.recognize_google(audio, language="ro-RO")
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        speak_text("Sorry, I could not understand. Please repeat.")
        return None
    except sr.RequestError as e:
        speak_text(f"Could not request results; {e}")
        return None

def ask_gemini(prompt_text):
    if client:
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_text
            )
            if hasattr(response, "text") and response.text:
                return response.text
        except Exception as e:
            print(f"(API fallback) Error calling Gemini API: {e}")
    return f"(MOCK) AI would respond to: {prompt_text[:50]}..."

def build_prompt(user_input):
    full_prompt = SYSTEM_PROMPT + "\n"
    for entry in conversation_history:
        user_text = entry.get('user')
        ai_text = entry.get('ai')
        if user_text and ai_text:
            full_prompt += f"User: {user_text}\nAI: {ai_text}\n"
    full_prompt += f"User: {user_input}\nAI:"
    return full_prompt

def main():
    speak_text("Hello! I am GENIUSDEV, your multilingual AI assistant! Type 'mic' to speak or 'exit' to quit.")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("exit", "quit"):
            speak_text("Goodbye! Au revoir! Auf Wiedersehen! Adiós!")
            save_history()
            break

        if user_input.lower() == "mic":
            spoken_text = listen_user()
            if spoken_text:
                prompt = build_prompt(spoken_text)
                assistant_output = ask_gemini(prompt)
                speak_text(assistant_output)
                conversation_history.append({"user": spoken_text, "ai": assistant_output})
                save_history()
            continue

        prompt = build_prompt(user_input)
        assistant_output = ask_gemini(prompt)
        speak_text(assistant_output)
        conversation_history.append({"user": user_input, "ai": assistant_output})
        save_history()

if __name__ == "__main__":
    main()
