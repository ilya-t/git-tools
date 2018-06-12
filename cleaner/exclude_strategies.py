import requests

import git


def by_name(_strategy_config, _root_config):
	results = []
	for branch in _strategy_config:
		results.append([branch, "manual"])
	return results

def bitbucket_pr(_strategy_config, _root_config):
	_response = requests.get(url=_strategy_config["pullrequests_url"],
	                         headers=_strategy_config["request_headers"])
	# print('Headers:')
	# print request_headers
	# print('RCode:')
	# print _response.status_code
	# print('Content:')
	# print _response.content
	# print('Json:')
	# print _response.json()

	_pr_list = _response.json()['values']

	if len(_pr_list) == 0:
		print ("You do not have opened Pull Requests!")
	results = []

	for pr_item in _pr_list:
		results.append([
			pr_item['fromRef']['displayId'], "PR: "+pr_item["title"]
		])

	return results


def active_branch(_strategy_config, _root_config):
	results = []
	repo = git.Repo(_root_config["repository_path"])
	results.append([repo.active_branch.name, "active branch"])
	return results