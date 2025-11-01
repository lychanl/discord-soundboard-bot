import argparse
import json
import pathlib
from traceback import print_exception

import discord

from typing import List, Optional


class SoundboardClient(discord.Client):
    def __init__(self, path: str, prefix: str, users: Optional[List[int]]) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self._path = pathlib.Path(path).resolve()
        assert self._path.is_dir(), "Not a directory"
        self._prefix = prefix
        self._commands = [
            ('help', self.help, '', 'Shows help message'),
            ('join', self.join, 'CHANNEL', 'Joins a voice channel. Use #! to reference a voice channel.'),
            ('leave', self.leave, '', 'Leaves current voice channel'),
            ('list', self.list_, '', 'Lists avaliable files'),
            ('play', self.play, 'FILE', 'Plays file (must be connected to a voice channel). FILE may be:'
             '\n- name of the file (with or without extension) in the directory provided in config'
             '\n- absoulte path of a file'
             '\n- number of the file in alphabetical order (as seen using list command)'),
            ('stop', self.stop, '', 'Stops playing audio file')
        ]
        self._users = users

    async def on_ready(self) -> None:
        print('Connected!')

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user:
            return
        if not message.content.startswith(self._prefix):
            return
        if self._users and message.author.id not in self._users:
            return

        command = message.content[len(self._prefix):].strip()
        print('Processing command from', message.author, 'content:\n', command)
        try:
            response = 'Sorry, it is not a valid command'

            for comm, func, _, _ in self._commands:
                if command.startswith(comm):
                    params = command[len(comm):].strip()
                    response = await func(params, message)
                    break

            if response:
                await message.channel.send(response)
        except Exception as e:
            print('An error occured.')
            print_exception(type(e), e, e.__traceback__)
            await message.channel.send('An error occured')

    async def help(self, params: str, message: discord.Message) -> str:
        return '\n'.join([
            'Use one of the following commands, preceded by a prefix ' + self._prefix
        ] + [
            f'{comm} {param_spec}: {info}' for comm, _, param_spec, info in self._commands
        ])

    async def _get_guild_voice_client(self, guild: discord.Guild) -> Optional[discord.VoiceClient]:
        for channel in guild.voice_channels:
            if self.user in channel.members:
                clients = [c for c in self.voice_clients if c.channel == channel]
                if clients:
                    client = clients[0]
                else:
                    print('Reconnecting to voice chanel...')
                    client = await channel.connect()
                return client
        return None

    async def join(self, params: str, message: discord.Message) -> Optional[str]:
        if not params:
            return 'Missing channel'
        channel_param = params.split()[0]
        if not channel_param.startswith('<#') or not channel_param.endswith('>') or not channel_param[2:-1].isnumeric():
            return 'Not a channel reference - use #! to reference a voice channel'
        channel_num = int(channel_param[2:-1])
        channel = self.get_channel(channel_num)
        if channel is None or not isinstance(channel, discord.channel.VoiceChannel):
            return 'Not a proper voice channel - use #! to reference a voice channel'
        if await self._get_guild_voice_client(message.guild):
            return 'Already connected to a voice channel on this server!'
        await channel.connect()
        return None

    async def leave(self, params: str, message: discord.Message) -> Optional[str]:
        client = await self._get_guild_voice_client(message.guild)
        if client is None:
            return 'Not connected!'
        await client.disconnect()
        return None

    async def list_(self, params: str, message: discord.Message) -> str:
        return '\n'.join([f'{i}: {path.name}' for i, path in enumerate(self._path.iterdir(), 1)])

    async def play(self, params: str, message: discord.Message) -> Optional[str]:
        if params.isnumeric():
            i = int(params) - 1
            files = list(self._path.iterdir())
            if i >= len(files) or i < 0:
                return 'Invalid file number'
            else:
                path = files[i]
        elif pathlib.Path(params).is_absolute():
            path = pathlib.Path(params)
        else:
            matches = [path for path in self._path.iterdir() if path.name == params or path.name.startswith(params + '.')]
            if not matches:
                return 'No such file'
            path = matches[0]
        if not path.is_file():
            return 'Not a file'

        client = await self._get_guild_voice_channel(message.guild)

        if client is None:
            return 'Not connected!'

        client.play(discord.FFmpegPCMAudio(str(path)))

    async def stop(self, params: str, message: discord.Message) -> Optional[str]:
        client = await self._get_guild_voice_channel(message.guild)

        if client is None:
            return 'Not connected!'

        client.stop()


def get_config(path: str) -> dict:
    with open(path, 'r') as f:
        config = json.load(f)
    assert 'token' in config, 'Missing token in config'
    assert 'path' in config, 'Missing sounds path in config'
    assert 'prefix' in config, 'Missing message prefix in config'
    return config


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('config', type=str, help='Path to .json config with "path", "token" and "prefix".'
                        'Optionally, it may specify "users" ids as the list of users that will be allowed to use the bot.')
    args = parser.parse_args()

    config = get_config(args.config)

    client = SoundboardClient(config['path'], config['prefix'], config.get('users', None))
    client.run(config['token'])
