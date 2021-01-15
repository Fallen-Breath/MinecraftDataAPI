import re
import unittest

from MinecraftDataAPI import MinecraftJsonParser


class MyTestCase(unittest.TestCase):
	def test_doc_string_data(self):
		parser = MinecraftJsonParser()
		for line in parser.convert_minecraft_json.__doc__.splitlines():
			if re.match(r'^\s*- .*$', line):
				s = line.split('-')[-1]
				print('{} -> {}'.format(s, parser.convert_minecraft_json(s)))

	def test_long_data(self):
		with open('data.txt', encoding='utf8') as file:
			text = file.read()
		print('Parsing long minecraft data with length {}'.format(len(text)))
		MinecraftJsonParser().convert_minecraft_json(text)


if __name__ == '__main__':
	unittest.main()
