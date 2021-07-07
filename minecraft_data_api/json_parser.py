import collections
import re

import hjson


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
