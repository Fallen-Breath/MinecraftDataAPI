# Minecraft Data API
-------------

[中文](https://github.com/MCDReforged/MinecraftDataAPI/blob/master/README_cn.md)

A MCDReforged api plugin to get player data information and more

## Dependency

- `hjson` module

```bash
pip install hjson
```

## Configuration

The config file is at `./config/minecraft_data_api/config.json`. It's configured to for with vanilla Minecraft by default

All regexps in the config use python's named matching group style, like `(?P<name>...)`

See `https://docs.python.org/3/library/re.html`

```json5
{
    "server_data_getter": {
        // The command for listing player. Used by API get_server_player_list
        "list_command": "list",  
        // The regex matching the output of the above command
        // Requires fields: `amount`, `limit`, `players`
        // The `players` field should be a `,` separated string whose items might have surrounding space chars
        "list_output_regex": "^There are (?P<amount>\\d+) of a max( of)? (?P<limit>\\d+) players online:(?P<players>.*)$"
    },
    "player_data_getter": {
        // The commands for query player entity data. Used by API get_player_info etc.
        "data_get_all_command": "data get entity {player}",
        "data_get_path_command": "data get entity {player} {path}",
        // The regex matching the output of the above command
        // Requires fields: `player`
        "data_get_output_regex": "^(?P<player>^\\w+) has the following entity data: .*$"
    }
}
```

## Usage

Directly `import` MinecraftDataAPI and just use it:

```python
import minecraft_data_api as api

pos = api.get_player_info('Steve', 'Pos')
```

Suggestion: declare the dependency of MinecraftDataAPI in your plugin metadata:

```python
PLUGIN_METADATA = {
	'dependencies': {
		'minecraft_data_api': '*',
	}
}
```

## Function list

Check the example plugin in the `examples` folder or read the code to get a more comprehensive understanding

### convert_minecraft_json

```python
def convert_minecraft_json(text: str)
```

Convert Minecraft style json format into a python object

Minecraft style json format is something like these:

- `Steve has the following entity data: [-227.5d, 64.0d, 12.3E4d]`
- `[-227.5d, 64.0d, 231.5d]`
- `Alex has the following entity data: {HurtByTimestamp: 0, SleepTimer: 0s, ..., Inventory: [], foodTickTimer: 0}`

It will automatically detect if there is a `<name> has the following entity data: `. If there is, it will erase it before converting

Args:
- text: A data get entity or other command result that use Minecraft style json format

Return:
- A parsed json result. It can be a `dict` / `list` / `int` / `float`

Examples:

- Input `Steve has the following entity data: [-227.5d, 64.0d, 231.5d]`, output `[-227.5, 64.0, 123000.0]`

- Input `{HurtByTimestamp: 0, SleepTimer: 0s, Inventory: [], foodTickTimer: 0}`, output `{'HurtByTimestamp': 0, 'SleepTimer': 0, 'Inventory': [], 'foodTickTimer': 0}`

### get_player_info

```python
def get_player_info(player: str, data_path: str = '', *, timeout: Optional[float] = None)
```

Execute `data get entity <name> [<path>]` and parse the result

Args:
- name: Name of the player who you want to get his/her info
- path: An optional `path` parameter in `data get entity` command
- timeout: The maximum time to wait the data result. Return `None` if time out. Default value `5`

Return:
- A parsed json result. It can be a `dict`, a `list`, a `int` or a `None`

Please refer to the Player.dat page on minecraft wiki

[player.dat format](https://minecraft.wiki/w/Player.dat_format)

### get_player_coordinate

```python
def get_player_coordinate(player: str, *, timeout: Optional[float] = None) -> Union[int or str]
```

Use `get_player_info` to query the `Pos` data of the player to get the player's coordinate. A `ValueError` will be risen if query failed

It will convert the return value into a named tuple `collections.namedtuple('Coordinate', 'x y z')` for easier use of the return value

### get_player_dimension

```
def get_player_dimension(player: str, *, timeout: Optional[float] = None) -> Coordinate
```

Use `get_player_info` to query the `Dimension` data of the player to get the player's dimension. A `ValueError` will be risen if query failed

It contains a dimension data convert. It will convert the dimension name in MC 1.16+ (e.g. `minecraft:overworld`) into the related integer

Dimension name mapping:

```python
dim_convert = {
    'minecraft:overworld': 0,
    'minecraft:the_nether': -1,
    'minecraft:the_end': 1
}
```

If the dimension it gets is not in the mapping, for example it's a custom dimension, then it will return the name of the dimension directly

### get_dimension_translation_text

```
def get_dimension_translation_text(dim_id: int) -> RText
```

Convert the dimension id into a RTextTranslation object that can be translated by Minecraft. The mapping of the translation key is as follows

```python
dimension_translation = {
    0: 'createWorld.customize.preset.overworld',
    -1: 'advancements.nether.root.title',
    1: 'advancements.end.root.title'
}
```

If the dimension id is not in the mapping, it will return a RText object contains the input id directly

You can safely use `api.get_dimension_translation_text(api.get_player_dimension('Steve'))` to get text component storing the dimension the player is in

### get_server_player_list

```python
def get_server_player_list(*, timeout: Optional[float] = None) -> Optional[Tuple[int, int, List[str]]]
```

Return the player list information by executing /list command

The return value is a tuple with 3 element: the amount of current player, the player limit, and a list of names of online players. Return None if querying failed

See `examples/PlayerList.py` for example usage
