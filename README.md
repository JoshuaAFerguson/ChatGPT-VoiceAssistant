# ChatGPT-VoiceAssistant

## Overview
ChatGPT-VoiceAssistant is a Python-based voice assistant that leverages the capabilities of ChatGPT, Whisper, ElevenLabs, and PicoVoice. This voice assistant allows users to interact with their devices using voice commands and provides intelligent responses based on the user's input.

## Features
- Voice recognition: Utilizes Whisper for accurate voice recognition and transcription.
- Natural language understanding: Leverages ChatGPT for understanding user queries and generating responses.
- Voice command processing: Integrates with ElevenLabs and PicoVoice for voice command processing and execution.

## Prerequisites
- Python 3.7 or higher

## Installation
1. Clone the repository: 
```bash
git clone https://github.com/JoshuaAFerguson/ChatGPT-VoiceAssistant.git
```

2. Change directory to the cloned repository:
```bash
cd ChatGPT-VoiceAssistant
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Rename example.env to .env and add your API keys


## Usage
To start the voice assistant, run the following command:
```bash
python assistant.py
```

After starting the voice assistant, it will wait for the wake word [porcupine] before it starts recording. After saying the wake word it will record the next 5 seconds of speach. You can interact with it using voice commands. Speak your queries clearly, and the assistant will provide intelligent responses based on your input.

## Contributing
Contributions to the ChatGPT-VoiceAssistant project are welcome! If you would like to contribute, please fork the repository, make your changes, and submit a pull request.