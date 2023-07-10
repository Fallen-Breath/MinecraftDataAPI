import os
import unittest

from minecraft_data_api.json_parser import MinecraftJsonParser


class MyTestCase(unittest.TestCase):
	def test_0_preprocess(self):
		cases = [
			'"',
			'"\\',
			'"\\"',
			'"\\a',
			"'",
			"'\\",
			"'\\'",
			"'\\a",
		]
		for s in cases:
			with self.assertRaisesRegex(ValueError, 'Cannot find a string ending quote', msg='s = {}'.format(repr(s))):
				MinecraftJsonParser.preprocess_minecraft_json(s)

	def test_1_correctness(self):
		cases = {
			# docstring of MinecraftJsonParser.convert_minecraft_json
			r''' {a: 0b, big: 2.99E7, c: "minecraft:white_wool", d: '{"text":"rua"}'} ''': {'a': 0, 'big': 2.99E7, 'c': "minecraft:white_wool", 'd': '{"text":"rua"}'},
			r''' [0.0d, 10, 1.7E9] ''': [0.0, 10, 1.7E9],
			r''' [I; -3213, 11345744, -707456, 56785135] ''': [-3213, 11345744, -707456, 56785135],
			r''' {Air: 300s, Text: "\\o/..\""} ''': {'Air': 300, 'Text': "\\o/..\""},
			r''' "hello" ''': 'hello',
			r''' 0b ''': 0,
			r'1s': 1,
			# extra cases
			r''' {XpP: 1.0331472E-7f} ''': {'XpP': 1.0331472E-7},
			r''' {XpP: 1.0331472E+7f} ''': {'XpP': 1.0331472E+7},
			r''' {XpP: 1.0331472E7f} ''': {'XpP': 1.0331472E7},
			r''' {XpP: -1.0331472E-7f} ''': {'XpP': -1.0331472E-7},
			r''' {XpP: -1.0331472E+7f} ''': {'XpP': -1.0331472E+7},
			r''' {XpP: -1.0331472E7f} ''': {'XpP': -1.0331472E7},
			# hjson does not leading "+", e.g. "{a: +1}"
			r''' {XpP: 1.0331472E-7} ''': {'XpP': 1.0331472E-7},
			r''' {XpP: 1.0331472E+7} ''': {'XpP': 1.0331472E+7},
			r''' {XpP: 1.0331472E7} ''': {'XpP': 1.0331472E7},
		}
		for s, expected in cases.items():
			msg = 'conversion: {} -> {}'.format(s, MinecraftJsonParser.preprocess_minecraft_json(s))
			try:
				data = MinecraftJsonParser.convert_minecraft_json(s)
				self.assertEqual(expected, data, msg=msg)
			except Exception as e:
				self.fail('convert failed: {}, {}'.format(e, msg))

	def test_2_long_data(self):
		here = os.path.abspath(os.path.dirname(__file__))
		for file_name in os.listdir(here):
			if file_name.endswith('.txt'):
				print('Testing {}'.format(file_name))
				with open(os.path.join(here, file_name), encoding='utf8') as file:
					text = file.read()
				for line in text.splitlines():
					if len(line) == 0 or line.startswith('#'):
						continue
					print('Parsing long minecraft data with length {}'.format(len(line)))
					try:
						MinecraftJsonParser.convert_minecraft_json(line)
					except Exception as e:
						self.fail('convert failed: {}, line: {}'.format(e, line))


if __name__ == '__main__':
	unittest.main()
