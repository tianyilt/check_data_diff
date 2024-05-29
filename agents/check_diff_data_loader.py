from utils.utils import read_jsonl


class DiffData:
	"""
	这个里面重要的field是计算好的diff q_main1和q_main2
	"""

	def __init__(self, data_path):
		self.data_path = data_path
		self.data = read_jsonl(data_path)
		self.diff_data = [d["diff"] for d in self.data]
		self.q_main_pair = [(d["q_main1"], d["q_main2"]) for d in self.data]
