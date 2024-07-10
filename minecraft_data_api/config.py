import re

from mcdreforged.api.all import Serializable


class ServerDataGetterConfig(Serializable):
	list_command: str = 'list'
	list_output_regex: re.Pattern = re.compile(r'^There are (?P<amount>\d+) of a max( of)? (?P<limit>\d+) players online:(?P<players>.*)$')


class PlayerDataGetterConfig(Serializable):
	data_get_all_command: str = 'data get entity {player}'
	data_get_path_command: str = 'data get entity {player} {path}'
	data_get_output_regex: re.Pattern = re.compile(r'^(?P<player>^\w+) has the following entity data: .*$')


class Config(Serializable):
	server_data_getter: ServerDataGetterConfig = ServerDataGetterConfig()
	player_data_getter: PlayerDataGetterConfig = PlayerDataGetterConfig()
