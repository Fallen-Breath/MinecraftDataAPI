import collections
import re
from typing import List

import hjson


class MinecraftJsonParser:
	__COMMAND_RESULT_PREFIX_REGEX = re.compile(r'^[^ ]* has the following entity data: ')
	__LETTER_AFTER_NUMBER_REGEX = re.compile(r'(([{\[:,]|^) *[+-]?\d+(\.\d*?)?(E[+-]?\d+)?)([bsLdf])')
	__ARRAY_HEADER_REGEX = re.compile(r'(?<=\[)[IL];')  # "I;" or "L;" after a "["
	__FOLDED_TAG_REGEX = re.compile(r'<\.\.\.>')        # "<...>"

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
		text = cls.remove_command_result_prefix(text)  # yeet prefix

		# {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		# remove letter after number outside string
		# remove int array or long array header outside string
		text = cls.preprocess_minecraft_json(text)

		# {a: 0, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'}
		value = hjson.loads(text)
		if isinstance(value, collections.OrderedDict):
			return dict(value)  # in python 3.6+ dict is already ordered
		return value

	@classmethod
	def remove_command_result_prefix(cls, text: str) -> str:
		return cls.__COMMAND_RESULT_PREFIX_REGEX.sub('', text)

	@classmethod
	def preprocess_minecraft_json(cls, text: str) -> str:
		def cpp_find(idx: int, end: int) -> int:
			if idx != -1:
				return idx
			return end

		result: List[str] = []
		i = 0
		while i < len(text):
			pos = min(cpp_find(text.find('"', i), len(text)), cpp_find(text.find("'", i), len(text)))
			non_quote_str = text[i:pos]
			non_quote_str = cls.__LETTER_AFTER_NUMBER_REGEX.sub(r'\1', non_quote_str)  # remove letter after number outside string: "1.23D" -> "1.23"
			non_quote_str = cls.__ARRAY_HEADER_REGEX.sub('', non_quote_str)  # remove int array or long array header outside string: "[I; 1,2,3]" -> "[ 1,2,3]"
			non_quote_str = cls.__FOLDED_TAG_REGEX.sub('', non_quote_str)  # remove FOLDED tag introduced in mc1.20.5-pre2, see issue #13
			result.append(non_quote_str)

			i = pos
			if i == len(text):
				break
			quote = text[i]
			j = i + 1
			while j < len(text):
				slash_pos = cpp_find(text.find('\\', j), len(text))
				quote_pos = text.find(quote, j, slash_pos)
				if quote_pos == -1:  # cannot find a quote in front of the first slash
					j = slash_pos + 2
					if j > len(text):
						raise ValueError(f'Cannot find a string ending quote, quote start: {i}')
				else:
					j = quote_pos + 1  # found an un-escaped quote
					break
			else:
				raise ValueError(f'Cannot find a string ending quote, quote start: {i}')

			# Expected after finishes the while-loop above:
			#     foo: "abc\tedf\"bar", xxx: 123
			#          i              j
			# i.e. text[i:j] == "abc\tedf\"bar"
			result.append(text[i: j])
			i = j
		return ''.join(result)
