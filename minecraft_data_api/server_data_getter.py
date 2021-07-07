from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional, Tuple, List

import parse
from mcdreforged.api.all import *


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
