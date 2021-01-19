from mcdreforged.api.all import *


PLUGIN_METADATA = {
	'id': 'playerlist_getter',
	'version': '1.0.0',
	'description': 'MinecraftDataAPI Showcase for player list',
	'author': 'Fallen_Breath',
	'link': 'https://github.com/MCDReforged/MinecraftDataAPI',
	'dependencies': {
		'minecraft_data_api': '>=1.1.0',
	}
}


@new_thread(PLUGIN_METADATA['id'])
def get_list(source: CommandSource):
	if source.get_server().is_server_startup():
		api = source.get_server().get_plugin_instance('minecraft_data_api')
		amount, limit, players = api.get_server_player_list()
		source.reply('玩家列表：{}/{} {}'.format(amount, limit, players))


def on_load(server: ServerInterface, prev):
	server.register_help_message('!!list', '获取玩家列表')
	server.register_command(Literal('!!list').runs(get_list))
