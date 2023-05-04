import pvporcupine
import pvcobra
import pyaudio
import time
import openai
import struct
import wave
import os
from dotenv import load_dotenv
from elevenlabslib import *
from pymilvus import Milvus, DataType
from sentence_transformers import SentenceTransformer


# Load environment variables from the .env file
load_dotenv()

WAKE_WORD = 'porcupine'
WAVE_OUTPUT_FILENAME = 'output.wav'
MAX_RECORD_SECONDS = 5  # Maximum recording duration in seconds
PICOVOICE_API_KEY = os.environ.get('PICOVOICE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
MILVUS_HOST = os.environ.get('MILVUS_HOST')
MILVUS_PORT = os.environ.get('MILVUS_PORT')

# Prepare Milvus for long-term storage
milvus = Milvus(host=MILVUS_HOST, port=MILVUS_PORT)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Define schema of the collection
schema = {
    "fields": [
        {"name": "prompt", "type": DataType.STRING},
        {"name": "response", "type": DataType.STRING},
        {"name": "response_vector", "type": DataType.FLOAT_VECTOR,
            "params": {"dim": 768}},
        {"name": "prompt_vector", "type": DataType.FLOAT_VECTOR, "params": {"dim": 768}},
    ],
    "segment_row_limit": 10000,
    "auto_id": True
}

collection_name = 'chat_history'

if not milvus.has_collection(collection_name):
    milvus.create_collection(collection_name, schema)

# Create Porcupine instance
porcupine = pvporcupine.create(
    access_key=PICOVOICE_API_KEY, keywords=[WAKE_WORD])

# create Cobra instance
cobra = pvcobra.create(access_key=PICOVOICE_API_KEY)

# Initialize OpenAI API
openai.api_key = OPENAI_API_KEY
CHATGPT_MODEL = "gpt-3.5-turbo"

# Initialize PyAudio
pa = pyaudio.PyAudio()
stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length,
)

# Initialize recording
frames = []


def record_audio():
    print('Recording audio...')
    is_speaking = False
    start_time = time.time()
    while True:
        # Read audio data from the microphone
        pcm = stream.read(porcupine.frame_length)
        cobra_pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        # Process the audio data using Cobra
        voice_activity = cobra.process(cobra_pcm)

        # Check if voice activity is detected
        if voice_activity > 0.5:
            is_speaking = True
            frames.append(pcm)
        else:
            frames.append(pcm)
            is_speaking = False

        # Check for recording timeout
        elapsed_time = time.time() - start_time
        if elapsed_time >= MAX_RECORD_SECONDS:
            frames.append(pcm)
            print('Recording timeout reached.')
            break

        if elapsed_time >= 2 and not is_speaking:
            print('Silence detected.')
            break

    # Save recorded audio to file

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    wf.setframerate(porcupine.sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()

    print('Recording complete.')


def transcribe_audio():
    # Transcribe audio file using Whisper API
    print('Transcribing audio...')

    with open(WAVE_OUTPUT_FILENAME, 'rb') as audio_file:
        response = openai.Audio.transcribe("whisper-1", audio_file)

    # Extract transcription result
    text = response['text']
    print('Transcription:', text)

    return text.strip()


def send_to_chatgpt(text):
    response = openai.ChatCompletion.create(
        model=CHATGPT_MODEL,
        n=1,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": text},
        ])

    # Extract the response text
    response_text = response['choices'][0]['message']['content']
    print('Response from ChatGPT:', response_text)
    # Return the response text
    return response_text.strip()


def synthesize_and_play_audio(text):
    # Define the Eleven Labs Voice Synthesis API endpoint and headers
    user = ElevenLabsUser(ELEVENLABS_API_KEY)
    # This is a list because multiple voices can have the same na
    voice = user.get_voices_by_name("Bella")[0]
    voice.generate_and_play_audio(text, playInBackground=False)

    for historyItem in user.get_history_items():
        if historyItem.text == text:
            # The first items are the newest, so we can stop as soon as we find one.
            historyItem.delete()
            break

# Parse Commands


def parseCommand(text):
    commands = ["Persona", "Help", "Quit", "Start"]
    match text:
        case "Help.":
            synthesize_and_play_audio(
                "Available commands are: Persona, Help, Quit, Start")
        case "Persona.":
            return
        case "Quit.":
            return
        case "Start.":
            synthesize_and_play_audio(
                "Please give a name for the project you want to create.")
            record_audio()
            text = transcribe_audio()
            text.replace(" ", "_")
            text.replace(".", "")
            text.replace("?", "")
            collection_name = text
            if not milvus.has_collection(collection_name):
                milvus.create_collection(collection_name, schema)


try:
    print("Listening for wake word '{}'...".format(WAKE_WORD))
    while True:
        # Read audio data from the microphone
        pcm = stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        # Process the audio data using Porcupine
        result = porcupine.process(pcm)

        # Check if the wake word was detected
        if result == 0:
            print("Wake word detected!")
            record_audio()
            text = transcribe_audio()

            if text == 'Quit.':
                break

            parseCommand(text)
            # Send transcribed text to ChatGPT API
            response_text = send_to_chatgpt(text)

            # Synthesize and play audio response
            synthesize_and_play_audio(response_text)

            # Re-initialize PyAudio
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )
            # Clear recording buffer
            frames = []

            # Start listening for wake word again
            print("Listening for wake word '{}'...".format(WAKE_WORD))


except KeyboardInterrupt:
    print("Stopping...")

finally:
    # Clean up resources
    stream.stop_stream()
    stream.close()
    pa.terminate()
    porcupine.delete()
    cobra.delete()
    milvus.close()
