import os
import re
import unittest

from minecraft_data_api.json_parser import MinecraftJsonParser


class MyTestCase(unittest.TestCase):
	def test_doc_string_data(self):
		parser = MinecraftJsonParser()
		for line in parser.convert_minecraft_json.__doc__.splitlines():
			if re.match(r'^\s*- .*$', line):
				s = line.split('- ')[-1]
				print('Testing {}'.format(s))
				print('-> {}'.format(parser.convert_minecraft_json(s)))

	def test_long_data(self):
		here = os.path.abspath(os.path.dirname(__file__))
		for file_name in os.listdir(here):
			if file_name.endswith('.txt'):
				print('Testing {}'.format(file_name))
				with open(os.path.join(here, file_name), encoding='utf8') as file:
					text = file.read()
				print('Parsing long minecraft data with length {}'.format(len(text)))
				MinecraftJsonParser().convert_minecraft_json(text)


if __name__ == '__main__':
	unittest.main()
