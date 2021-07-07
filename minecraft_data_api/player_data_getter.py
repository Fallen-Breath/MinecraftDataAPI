import re
from queue import Queue, Empty
from threading import RLock
from typing import Dict

from mcdreforged.api.all import *

from minecraft_data_api.json_parser import MinecraftJsonParser


class PlayerDataGetter:
	class QueueTask:
		def __init__(self):
			self.queue = Queue()
			self.count = 0

	def __init__(self, server: PluginServerInterface):
		self.queue_lock = RLock()
		self.work_queue = {}  # type: Dict[str, PlayerDataGetter.QueueTask]
		self.server = server  # type: PluginServerInterface
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
			self.server.logger.warning('[{}] Query for player {} at path {} timeout'.format(self.server.get_self_metadata().name, player, path))
			return None
		finally:
			task.count -= 1
		try:
			return self.json_parser.convert_minecraft_json(content)
		except Exception as err:
			self.server.logger.error('[{}] Fail to Convert data "{}": {}'.format(
				self.server.get_self_metadata().name,
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