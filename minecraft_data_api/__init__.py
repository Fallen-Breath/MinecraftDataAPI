from typing import Optional, Union, NamedTuple

from mcdreforged.api.all import RText, RTextTranslation, ServerInterface, Version

from minecraft_data_api.config import Config
from minecraft_data_api.player_data_getter import PlayerDataGetter
from minecraft_data_api.server_data_getter import ServerDataGetter, PlayerListQueryResult

__all__ = [
	'Coordinate',
	'PlayerListQueryResult',

	'convert_minecraft_json',
	'get_player_info',
	'get_player_coordinate',
	'get_player_dimension',
	'get_dimension_translation_text',
	'get_server_player_list',
]


class Coordinate(NamedTuple):
	x: float
	y: float
	z: float


DEFAULT_TIME_OUT = 5  # seconds
player_data_getter: Optional[PlayerDataGetter] = None
server_data_getter: Optional[ServerDataGetter] = None


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


def get_player_coordinate(player: str, *, timeout: Optional[float] = None) -> Coordinate:
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
	overworld_key = 'flat_world_preset.minecraft.overworld'
	try:
		version = Version(ServerInterface.si().get_server_information().version)
	except ValueError:
		pass
	else:
		if version < Version('1.19'):
			overworld_key = 'createWorld.customize.preset.overworld'
	dimension_translation = {
		0: overworld_key,
		-1: 'advancements.nether.root.title',
		1: 'advancements.end.root.title'
	}
	if dim_id in dimension_translation:
		return RTextTranslation(dimension_translation[dim_id])
	else:
		return RText(dim_id)


def get_server_player_list(*, timeout: Optional[float] = None) -> Optional[PlayerListQueryResult]:
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
