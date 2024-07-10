from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional, List, NamedTuple

from mcdreforged.api.all import *

from minecraft_data_api.config import ServerDataGetterConfig


class PlayerListQueryResult(NamedTuple):
	amount: int
	limit: int
	players: List[str]


class ServerDataGetter:
	class QueryTask:
		def __init__(self):
			self.querying_amount = 0
			self.result_queue: 'Queue[PlayerListQueryResult]' = Queue()

		def is_querying(self):
			return self.querying_amount > 0

		@contextmanager
		def with_querying(self):
			self.querying_amount += 1
			try:
				yield
			finally:
				self.querying_amount -= 1

	def __init__(self, server: ServerInterface, config: ServerDataGetterConfig):
		self.server = server
		self.config = config
		self.player_list = self.QueryTask()

	def get_player_list(self, timeout: float) -> Optional[PlayerListQueryResult]:
		if self.server.is_on_executor_thread():
			raise RuntimeError('Cannot invoke get_player_list on the task executor thread')
		with self.player_list.with_querying():
			self.server.execute(self.config.list_command)
			try:
				return self.player_list.result_queue.get(timeout=timeout)
			except Empty:
				return None

	def on_info(self, info: Info):
		if not info.is_user:
			if self.player_list.is_querying():
				if (m := self.config.list_output_regex.match(info.content)) is not None:
					self.server.logger.debug('player list output match found: {}'.format(m.groupdict()))

					amount = int(m.group('amount'))
					limit = int(m.group('limit'))
					players = []
					for part in m.group('players').split(','):
						name = part.strip()
						if len(name) > 0:
							players.append(name)

					self.player_list.result_queue.put(PlayerListQueryResult(amount, limit, players))
