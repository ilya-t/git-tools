from __future__ import print_function
import json

import sys
from pathlib import Path

import exclude_strategies


def create_default_config(_filename):
	print('{    \n'
	      '    "repository_path": "put path to your repository here", \n'
	      '    "exclude_strategies": {\n'
	      '        "by_name": [\n'
	      '            "master"\n'
	      '        ],\n'
	      '        "active_branch": {}\n'
	      '    }\n'
	      '}',
	      file=file(name=_filename, mode='w'))
	pass


def put(_exclusions, _array):
	for _item in _array:
		_exclusions.append(_item)
	pass


class Config:
	repository_path = None,
	exclude_branches = None


def load(_filename):
	config_file = Path(_filename)
	if not config_file.is_file():
		create_default_config(_filename)
		print('Configure cleaner in ' + _filename)
		return None

	config = json.loads(open(_filename).read())
	exclusions = []

	for some_stategy in config['exclude_strategies']:
		if not hasattr(exclude_strategies, some_stategy):
			sys.stderr.writelines('Undefined strategy: ' + some_stategy + '\n')
			sys.exit(1)
		concrete_strategy = getattr(exclude_strategies, some_stategy)
		put(exclusions, concrete_strategy(config['exclude_strategies'][some_stategy], config))

	if config['repository_path'] == None:
		print('Missing "repository_path" in ' + _filename)
		sys.exit(1)

	strategy = Config()
	strategy.exclude_branches = exclusions
	strategy.repository_path = config['repository_path']

	return strategy
