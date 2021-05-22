import collections
import re
from contextlib import contextmanager
from queue import Queue, Empty
from threading import RLock
from typing import Dict, Optional, Union, Tuple, List

import hjson
import parse
from mcdreforged.api.all import *

PLUGIN_METADATA = {
	'id': 'minecraft_data_api',
	'version': '1.3.0',
	'name': 'Minecraft Data API',
	'description': 'A MCDReforged api plugin to get player data information and more',
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/MCDReforged/MinecraftDataAPI'
}

DEFAULT_TIME_OUT = 5  # seconds


class PlayerDataGetter:
	class QueueTask:
		def __init__(self):
			self.queue = Queue()
			self.count = 0

	def __init__(self, server: ServerInterface):
		self.queue_lock = RLock()
		self.work_queue = {}  # type: Dict[str, PlayerDataGetter.QueueTask]
		self.server = server  # type: ServerInterface
		self.json_parser = MinecraftJsonParser()

	def get_queue_task(self, player) -> QueueTask:
		with self.queue_lock:
			if player not in self.work_queue:
				self.work_queue[player] = self.QueueTask()
			return self.work_queue[player]

	def get_player_info(self, player: str, path: str, timeout: float):
		if self.server.is_on_executor_thread():
			raise RuntimeError('Cannot invoke get_player_info on the task executor thread')
		if len(path) >= 1 and not path.startswith(' '):
			path = ' ' + path
		command = 'data get entity {}{}'.format(player, path)
		task = self.get_queue_task(player)
		task.count += 1
		try:
			self.server.execute(command)
			content = task.queue.get(timeout=timeout)
		except Empty:
			self.server.logger.warning('[{}] Query for player {} at path {} timeout'.format(PLUGIN_METADATA['name'], player, path))
			return None
		finally:
			task.count -= 1
		try:
			return self.json_parser.convert_minecraft_json(content)
		except Exception as err:
			self.server.logger.error('[{}] Fail to Convert data "{}": {}'.format(
				PLUGIN_METADATA['name'],
				content if len(content) < 64 else '{}...'.format(content[:64]),
				err
			))

	def on_info(self, info: Info):
		if not info.is_user:
			if re.match(r'^\w+ has the following entity data: .*$', info.content):
				player = info.content.split(' ')[0]
				task = self.get_queue_task(player)
				if task.count > 0:
					task.queue.put(info.content)


class MinecraftJsonParser:
	@classmethod
	def convert_minecraft_json(cls, text: str):
		r"""
		Convert Minecraft json string into standard json string and json.loads() it
		Also if the input has a prefix of "xxx has the following entity data: " it will automatically remove it, more ease!
		Example available inputs:
		- Alex has the following entity data: {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		- {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		- [0.0d, 10, 1.7E9]
		- [I; -3213, 11345744, -707456, 56785135]
		- {Air: 300s, Text: "\\o/..\""}
		- "hello"
		- 0b

		:param str text: The Minecraft style json string
		:return: Parsed result
		"""

		# Alex has the following entity data: {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		# yeet the prefix
		text = re.sub(r'^.* has the following entity data: ', '', text)  # yeet prefix

		# {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		# remove letter after number outside string
		text = cls.remove_letter_after_number(text)

		# {a: 0, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		value = hjson.loads(text)
		if isinstance(value, collections.OrderedDict):
			return dict(value)  # in python 3.6+ dict is already ordered
		return value

	@classmethod
	def remove_letter_after_number(cls, text: str) -> str:
		result = ''
		while text:
			pos = min(text.find('"'), text.find("'"))
			quote = None
			if pos == -1:
				pos = len(text)
			non_quote_str, quote_str = text[:pos], text[pos:]
			non_quote_str = re.sub(r'(?<=\d)[a-zA-Z](?=(\D|$))', '', non_quote_str)  # remove letter after number outside string: 1.23D
			non_quote_str = re.sub(r'(?<=\[)[IL];', '', non_quote_str)  # remove int array or long array header outside string: [I: 1,2,3]
			result += non_quote_str
			if quote_str:
				quote = quote_str[0]
				result += quote
				quote_str = quote_str[1:]  # remove the beginning quote
			while quote_str:
				slash_pos = quote_str.find('\\')
				if slash_pos == -1:
					slash_pos = len(quote_str)
				quote_pos = quote_str[:slash_pos].find(quote)
				if quote_pos == -1:  # cannot find a quote in front of the first slash
					if slash_pos == len(quote_str):
						raise ValueError('Cannot find a string ending quote')
					result += quote_str[:slash_pos + 2]
					quote_str = quote_str[slash_pos + 2:]
				else:
					result += quote_str[:quote_pos + 1]
					quote_str = quote_str[quote_pos + 1:]  # found an un-escaped quote
					break
			text = quote_str
		return result


class ServerDataGetter:
	class QueryTask:
		def __init__(self):
			self.querying_amount = 0
			self.result_queue = Queue()

		def is_querying(self):
			return self.querying_amount > 0

		@contextmanager
		def with_querying(self):
			self.querying_amount += 1
			try:
				yield
			finally:
				self.querying_amount -= 1

	def __init__(self, server: ServerInterface):
		self.server = server
		self.player_list = self.QueryTask()

	def get_player_list(self, timeout: float) -> Optional[Tuple[int, int, List[str]]]:
		if self.server.is_on_executor_thread():
			raise RuntimeError('Cannot invoke get_player_list on the task executor thread')
		with self.player_list.with_querying():
			self.server.execute('list')
			try:
				amount, limit, players = self.player_list.result_queue.get(timeout=timeout)
			except Empty:
				return None
			else:
				if len(players) > 0:
					players = players.split(', ')
				else:
					players = []
				return amount, limit, players

	def on_info(self, info: Info):
		if not info.is_user:
			if self.player_list.is_querying():
				formatters = (
					# <1.16
					# There are 6 of a max 100 players online: 122, abc, xxx, www, QwQ, bot_tob
					r'There are {amount:d} of a max {limit:d} players online:{players}',
					# >=1.16
					# There are 1 of a max of 20 players online: Fallen_Breath
					r'There are {amount:d} of a max of {limit:d} players online:{players}',
				)
				for formatter in formatters:
					parsed = parse.parse(formatter, info.content)
					if parsed is not None and parsed['players'].startswith(' '):
						self.player_list.result_queue.put((parsed['amount'], parsed['limit'], parsed['players'][1:]))
						break


player_data_getter = None  # type: Optional[PlayerDataGetter]
server_data_getter = None  # type: Optional[ServerDataGetter]


def on_load(server, prev):
	global player_data_getter, server_data_getter
	player_data_getter = PlayerDataGetter(server)
	server_data_getter = ServerDataGetter(server)

	if hasattr(prev, 'player_data_getter'):
		player_data_getter.queue_lock = prev.player_data_getter.queue_lock
		player_data_getter.work_queue = prev.player_data_getter.work_queue
	if hasattr(prev, 'server_data_getter'):
		server_data_getter.player_list = prev.server_data_getter.player_list


def on_info(server: ServerInterface, info):
	player_data_getter.on_info(info)
	server_data_getter.on_info(info)


# ------------------
#   API Interfaces
# ------------------


def convert_minecraft_json(text: str):
	"""
	Convert a mojang style "json" str to a json like object
	:param text: The name of the player
	"""
	return player_data_getter.json_parser.convert_minecraft_json(text)


def get_player_info(player: str, data_path: str = '', *, timeout: Optional[float] = None):
	"""
	Get information from a player
	It's required to be executed in a separated thread. It can not be invoked on the task executor thread of MCDR
	:param player: The name of the player
	:param data_path: Optional, the data nbt path you want to query
	:param timeout: The timeout limit for querying
	:return: A parsed json like object contains the information. e.g. a dict
	"""
	if timeout is None:
		timeout = DEFAULT_TIME_OUT
	return player_data_getter.get_player_info(player, data_path, timeout)


Coordinate = collections.namedtuple('Coordinate', 'x y z')


def get_player_coordinate(player: str, *, timeout: Optional[float] = None) -> Union[int or str]:
	"""
	Return the coordinate of a player
	The return value is a tuple with 3 elements (x, y, z). Each element is a float
	The return value is also a namedtuple, you can use coord.x, coord.y, coord.z to access the value
	"""
	pos = get_player_info(player, 'Pos', timeout=timeout)
	if pos is None:
		raise ValueError('Fail to query the coordinate of player {}'.format(player))
	return Coordinate(x=float(pos[0]), y=float(pos[1]), z=float(pos[2]))


def get_player_dimension(player: str, *, timeout: Optional[float] = None) -> Union[int or str]:
	"""
	Return the dimension of a player and return an int representing the dimension. Compatible with MC 1.16
	If the dim result is a str, the server should be in 1.16, and it will convert the dimension name into the old integer
	format if the dimension is overworld, nether or the end. Otherwise the origin dimension name str is returned
	"""
	dim_convert = {
		'minecraft:overworld': 0,
		'minecraft:the_nether': -1,
		'minecraft:the_end': 1
	}
	dim = get_player_info(player, 'Dimension', timeout=timeout)
	if dim is None:
		raise ValueError('Fail to query the dimension of player {}'.format(player))
	if type(dim) is str:  # 1.16+
		dim = dim_convert.get(dim, dim)
	return dim


def get_dimension_translation_text(dim_id: int) -> RText:
	"""
	Return a RTextTranslation object indicating the dimension name which can be recognized by Minecraft
	If the dimension id is not supported, it will just return a RText object wrapping the dimension id
	:param dim_id: a int representing the dimension. Should be 0, -1 or 1
	"""
	dimension_translation = {
		0: 'createWorld.customize.preset.overworld',
		-1: 'advancements.nether.root.title',
		1: 'advancements.end.root.title'
	}
	if dim_id in dimension_translation:
		return RTextTranslation(dimension_translation[dim_id])
	else:
		return RText(dim_id)


def get_server_player_list(*, timeout: Optional[float] = None) -> Optional[Tuple[int, int, List[str]]]:
	"""
	Return the player list information by executing /list command
	It's required to be executed in a separated thread. It can not be invoked on the task executor thread of MCDR
	:param timeout: The timeout limit for querying
	:return: A tuple with 3 element: the amount of current player, the player limit, and a list of names of online players
	Return None if querying failed
	"""
	if timeout is None:
		timeout = DEFAULT_TIME_OUT
	return server_data_getter.get_player_list(timeout)

# -----------------------
#   API Interfaces ends
# -----------------------
