import json
from cli import ChatCLI


def main():
    # Load configuration from settings.json
    with open('settings.json') as f:
        config = json.load(f)

    # Initialize ChatCLI
    chat_cli = ChatCLI(config)

    # Start the chat CLI
    chat_cli.start()


if __name__ == "__main__":
    main()
