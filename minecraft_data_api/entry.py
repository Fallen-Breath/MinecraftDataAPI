from mcdreforged.api.all import *

import minecraft_data_api as root
from minecraft_data_api.config import Config
from minecraft_data_api.player_data_getter import PlayerDataGetter
from minecraft_data_api.server_data_getter import ServerDataGetter


def on_load(server: PluginServerInterface, prev):
	cfg = server.load_config_simple(target_class=Config)

	root.player_data_getter = PlayerDataGetter(server, cfg.player_data_getter)
	root.server_data_getter = ServerDataGetter(server, cfg.server_data_getter)

	if hasattr(prev, 'player_data_getter'):
		root.player_data_getter.queue_lock = prev.player_data_getter.queue_lock
		root.player_data_getter.work_queue = prev.player_data_getter.work_queue
	if hasattr(prev, 'server_data_getter'):
		root.server_data_getter.player_list = prev.server_data_getter.player_list


def on_info(server: PluginServerInterface, info):
	root.player_data_getter.on_info(info)
	root.server_data_getter.on_info(info)


# Backwards compatibility for those who use `server.get_plugin_instance('minecraft_data_api')` to access APIs
for __name in root.__all__:
	globals()[__name] = getattr(root, __name)
