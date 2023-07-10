# Minecraft Data API
-------------

[English](https://github.com/MCDReforged/MinecraftDataAPI/blob/master/README.md)

一个提供获取玩家数据信息等的 MCDReforged 插件 API

## 依赖

- `hjson` 模块

## 使用方法

直接 `import` MinecraftDataAPI，就能用了

```python
import minecraft_data_api as api

pos = api.get_player_info('Steve', 'Pos')
```

建议：在插件元数据中声明对 MinecraftDataAPI 的依赖：

```python
PLUGIN_METADATA = {
	'dependencies': {
		'minecraft_data_api': '*',
	}
}
```

## 函数列表

查看 `examples` 文件夹中的样例插件，或者阅读相关代码，以得到更全面的理解

### convert_minecraft_json

```python
def convert_minecraft_json(text: str)
```

将麻将牌 JSON 转换成 Python 可读取的数据类型

麻将牌 JSON 的形式如下：

- `Steve has the following entity data: [-227.5d, 64.0d, 12.3E4d]`
- `[-227.5d, 64.0d, 231.5d]`
- `Alex has the following entity data: {HurtByTimestamp: 0, SleepTimer: 0s, ..., Inventory: [], foodTickTimer: 0}`

会自动检查消息是否包含 `<name> has the following entity data: `前缀，并且会在转换前自动去除

参数：
- text: 从`/data get entity`指令或者其他命令获得的麻将牌 JSON 数据

返回：
- json 解析后的结果。它可以是一个 `dict`, 一个 `list`, 一个 `int`

示例：

- 输入： `Steve has the following entity data: [-227.5d, 64.0d, 231.5d]`, 输出： `[-227.5, 64.0, 123000.0]`

- 输入： `{HurtByTimestamp: 0, SleepTimer: 0s, Inventory: [], foodTickTimer: 0}`, 输出： `{'HurtByTimestamp': 0, 'SleepTimer': 0, 'Inventory': [], 'foodTickTimer': 0}`

### get_player_info

```python
def get_player_info(player: str, data_path: str = '', *, timeout: Optional[float] = None)
```

自动执行 `/data get entity <name> [<path>]` 并解析返回数据

参数：
- name: 要获得 TA 数据的目标玩家名
- path: 在`/data get entity` 指令中的可选参数 `path`
- timeout: 等待结果的最长时间。如果超时了则返回 `None`。默认 5s

返回：
 - 解析后的结果

你可以在Minecraft Wiki参考关于Player.dat的格式信息

[Player.dat格式](https://minecraft-zh.gamepedia.com/Player.dat%E6%A0%BC%E5%BC%8F)

### get_player_coordinate

```python
def get_player_coordinate(player: str, *, timeout: Optional[float] = None) -> Coordinate
```

使用 `get_player_info` 查询玩家的 `Pos` 字段信息，从何得到玩家的坐标。如果查询失败，抛出 `ValueError` 异常

这个函数会将返回的坐标为值包装为一个命名元组 `collections.namedtuple('Coordinate', 'x y z')`，从而让返回值更易于使用

### get_player_dimension

```
def get_player_dimension(player: str, *, timeout: Optional[float] = None) -> Union[int or str]
```

使用 `get_player_info` 查询玩家的 `Dimension` 字段信息，从何得到玩家的维度。如果查询失败，抛出 `ValueError` 异常

这个函数内置了维度数据的转化，会将 MC 1.16 后的维度名称（如 `minecraft:overworld`）转换为对应的数字

维度名称映射表如下

```python
dim_convert = {
    'minecraft:overworld': 0,
    'minecraft:the_nether': -1,
    'minecraft:the_end': 1
}
```

如果得到的维度名称不在其中，比如该维度为自定义维度，那么将直接返回维度的名称

### get_dimension_translation_text

```
def get_dimension_translation_text(dim_id: int) -> RText
```

将维度 id 转换为对应的可被 Minecraft 翻译的一个 RTextTranslation 对象。其中翻译键的映射如下

```python
dimension_translation = {
    0: 'createWorld.customize.preset.overworld',
    -1: 'advancements.nether.root.title',
    1: 'advancements.end.root.title'
}
```

如果输入的维度 id 不在上表中，则直接返回一个包装着输入的维度 id 的 RText 对象

顺便一提，你可以放心地使用 `api.get_dimension_translation_text(api.get_player_dimension('Steve'))` 来获得一个储存着玩家维度的文本容器

### get_server_player_list

```python
def get_server_player_list(*, timeout: Optional[float] = None) -> Optional[Tuple[int, int, List[str]]]
```

使用 `/list` 指令获得玩家列表相关信息

返回值是一个含有 3 个元素的元组：当前玩家的数量、玩家数量上限、在线玩家名的列表。如果查询失败，返回 None

样例用法见 `examples/PlayerList.py`
