from mcdreforged.api.all import *

PLUGIN_METADATA = {
	'id': 'simple_here',
	'version': '1.0.0',
	'name': 'Simple Here',
	'author': 'Fallen_Breath',
	'link': 'https://github.com/MCDReforged/MinecraftDataAPI',
	'dependencies': {
		'minecraft_data_api': '*',
	}
}


@new_thread(PLUGIN_METADATA['name'])
def show_me(source: CommandSource):
	if isinstance(source, PlayerCommandSource):
		import minecraft_data_api as api
		coord = api.get_player_coordinate(source.player)
		dim = api.get_player_dimension(source.player)
		dim_text = api.get_dimension_translation_text(dim)
		source.get_server().say(RTextList(
			'{} @ [{}, {}, {}] '.format(source.player, coord.x, coord.y, coord.z),
			dim_text
		))


def on_load(server: PluginServerInterface, prev):
	server.register_help_message('!!s-here', '广播坐标并高亮玩家')
	server.register_command(Literal('!!s-here').runs(show_me))
