import time
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech
from chatgpt import ChatGPT
from storage import MemoryStorage


class ChatCLI:
    def __init__(self, config):
        self.config = config
        self.speech_to_text = SpeechToText(config['speech_to_text'])
        self.text_to_speech = TextToSpeech(config['text_to_speech'])
        self.chatgpt = ChatGPT(config['openai_model'])
        self.storage = MemoryStorage(config['storage'])

    def start(self):
        print("Welcome to ChatGPT CLI!")
        print("Press Ctrl+C to exit.")

        while True:
            try:
                prompt = input("> ")

                # Store the prompt in long-term memory
                self.storage.store_prompt(prompt)

                # Convert speech to text if enabled
                if self.config['speech_to_text']['enabled']:
                    print("Listening for speech...")
                    audio = self.speech_to_text.capture_audio()
                    text = self.speech_to_text.convert_to_text(audio)
                    print("You said:", text)

                    # Store the converted text in long-term memory
                    self.storage.store_prompt(text)

                    prompt = text

                # Generate a response using ChatGPT
                response = self.chatgpt.generate_response(prompt)

                # Store the response in long-term memory
                self.storage.store_response(response)

                # Convert response to speech if enabled
                if self.config['text_to_speech']['enabled']:
                    print("Response:", response)
                    print("Converting response to speech...")
                    speech = self.text_to_speech.convert_to_speech(response)
                    self.text_to_speech.play_audio(speech)

            except KeyboardInterrupt:
                print("\nExiting...")
                break


if __name__ == "__main__":
    # Load configuration from settings.json
    with open('settings.json') as f:
        config = json.load(f)

    # Initialize ChatCLI
    chat_cli = ChatCLI(config)

    # Start the chat CLI
    chat_cli.start()
