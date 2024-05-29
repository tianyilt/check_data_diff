import json
from utils.utils import ensure_output

def read_output_jsonl(file_path):
	"""
	only select data containing figures
	:param file_path:
	:return:
	"""
	data = []
	with open(file_path, 'r', encoding='utf-8') as file:
		for line in file:
			# not null
			if 'null\n' not in line:
				data.append(json.loads(line))
	return data


class StateManager():
	def __init__(self, cur_output_file):
		ensure_output(cur_output_file)
		self.cur_visited_data = read_output_jsonl(cur_output_file)
		visited_ids = [dd["id"] for dd in self.cur_visited_data]
		self.visited_ids = set(visited_ids)


# sm = StateManager(cur_output_file="output/mllm_vqa_output_all.jsonl")
