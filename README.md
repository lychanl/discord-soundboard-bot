# discord-soundboard-bot
A discord bot for playing local sound files

## Setup
1. Create a python bot and write down bot token.
2. Install python requirements in requirements.txt.
3. Prepare a json config file.
4. Run: `python run.py path_to_config.json`

## Config

Config file has the following structure:

```json
{
    "path": "path/to/sound/files",
    "token": "token",
    "prefix": "prefix",
    "users": [000000000000, 000000000001, 000000000002]
}
```

- path: a path to the directory with audio files
- token: a discord bot token
- prefix: bot message prefix - a sequence of characters that need to start a message for the bot to process it
- users: (optional) list of discord user ids of users authorized to use bot commands

## Avaliable commands:

- help: lists commands
- join #!Voice-channel: joins referenced voice channel
- leave: leaves currently connected voice channel
- list: lists files in the audio directory (with numerical ids for easier selection)
- play (file_id|file_name|absolute_path): plays specified file from the audio directory (or any other if absolute path used). Needs to be connected to a voice channel
- stop: stops playing
