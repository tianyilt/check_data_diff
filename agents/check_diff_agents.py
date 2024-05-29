import httpx
import json
import asyncio
from tqdm.asyncio import tqdm
from utils.utils import ensure_output,truncate_str
from agents.check_diff_data_loader import DiffData
from agents.state_manager import StateManager
import argparse

API_KEY = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI0MDA0ODI2NyIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTcxNjQyODU5MywiY2xpZW50SWQiOiJtcXprcGxtbnc5N29wa28zNmpxaiIsInBob25lIjoiMTg5NjQ5MDc4OTAiLCJ1dWlkIjoiOWU2ZjQ2NjgtNWUwOS00MDJiLThhNzUtZDgwYzMyMDU1M2ExIiwiZW1haWwiOiJsaWFuZ3RpYW55aUBwamxhYi5vcmcuY24iLCJleHAiOjE3MzE5ODA1OTN9.efJL1BzGBG_VaTUIw8sdz22f3Bth648cAqQRzOibubcRS8xUVQiT_t5orwjA34voroWRB15PX_-zVzvfMasLiw"
API_BASE_URL = "https://puyu.openxlab.org.cn/puyu/api/v1/chat/completions"


class CheckDiffClient:
	def __init__(self, data: DiffData, sm: StateManager, output_file: str = None):
		self.api_key = API_KEY
		self.base_url = API_BASE_URL
		# self.model_name = "InternLM-100B-0331"
		self.model_name = "internlm2-latest"
		# self.model_name = "qwen-max"
		self.data: DiffData = data
		self.state_manager = sm
		self.prompt = None
		self.output_file = output_file
		ensure_output(self.output_file)

	def build_prompt(self, diff_data, q_main1, q_main2):
		main_question = f"""你是个数据分析师, 需要分析改进后的数据q_main2和原始数据q_main1的差异, 字符的差异显示在了diff_data. 你需要分析并评价一下内容
change_summary: 概括修改了什么
score: 评价修改后的数据的得分 范围-5到5  -5表示q_main2的数据比q_main1的数据更差, 5表示q_main2的数据比q_main1的数据更好

数据: diff_data:{diff_data}, q_main1:{q_main1}, q_main2:{q_main2}
"""
		example_output = """请按照以下格式输出
```
{
"change_summary": "修改了什么",
"score": int
}
```
"""
		prompt = main_question + example_output
		return prompt

	async def check_diff_one(self, index):
		try:
			cur_diff_data = self.data.diff_data[index]
			cur_data = self.data.data[index]
			q_main1, q_main2 = self.data.q_main_pair[index]
			# if q_main1 longer than 4000, take top 4000 tokens
			cur_diff_data = "\n".join(cur_diff_data)
			q_main1 = truncate_str(q_main1, 4000)
			q_main2 = truncate_str(q_main2, 4000)
			cur_diff_data = truncate_str(cur_diff_data, 4000)
			PROMPT = self.build_prompt(cur_diff_data, q_main1, q_main2)
			# if not self.filter(subject, q_type, answer_detail):
			# 	return None
			# random select one api in the list
			import random
			cur_api_key = API_KEY

			headers = {
				"Content-Type": "application/json",
				"Authorization": f"Bearer {cur_api_key}"
			}

			data = {
				"model": self.model_name,
				"messages": [
					# {
					# 	"role": "system",
					# 	"text": "You are a helpful assistant"
					# },
					{
						"role": "user",
						"text": f"{PROMPT}"
					},
				],
				# "temperature": 0.7,
				# "top_p": 40,
				# "repetition_penalty": 1.02,
				# "n": 1,
				# "stop": '<|im_end|>'
			}

			url = self.base_url

			async with httpx.AsyncClient(timeout=5 * 60.0) as client:
				response = await client.post(self.base_url, headers=headers, json=data)
				response.raise_for_status()  # Ensure the response is successful

				# Decode the response
				response_json = response.json()
				print(json.dumps(response_json, ensure_ascii=False, indent=4))  # Debugging: print the response

				# target_length = len(answer_detail) + len(std_ans)
				# best_index = self.choose_best_answer(res_content_list,target_length)
				res_dict = {}
				res_dict["output"] = response_json["choices"][0]["message"]["content"]
				res_dict["diff_prompt"] = PROMPT
				res_dict["id"] = cur_data["id"]
				res_dict["other_info"] = cur_data
				# res_dict = deepcopy(question)
				# res_dict["rephrase_choice"] = response_json["choices"][int(best_index)]["message"]["content"]
				with open(self.output_file, "a", encoding="utf-8") as f:
					f.write(json.dumps(res_dict, ensure_ascii=False) + "\n")
				return res_dict
		except Exception as e:
			print(f"Failed to process {index}: {e}")
			return None

	async def check_diff_batch(self, workers):
		queue = asyncio.Queue()
		results = []

		async def producer():
			for i in range(0, len(self.data.data)):
				if self.data.data[i]["id"] not in self.state_manager.visited_ids:
					await queue.put(i)
			for _ in range(workers):  # Signal the consumers to stop
				await queue.put(None)

		async def consumer(pbar):
			while True:
				i = await queue.get()
				if i is None:  # End signal
					break
				result = await self.check_diff_one(i)
				if result is not None:
					self.state_manager.visited_ids.add(result["id"])
					results.append(result)
				# with open(self.output_file, "a", encoding="utf-8") as f:
				# 	f.write(json.dumps(result, ensure_ascii=False) + "\n")
				queue.task_done()
				pbar.update(1)

		producers = [asyncio.create_task(producer())]
		total_tasks = len(self.data.data) - len(self.state_manager.visited_ids)
		print(f"Already {len(self.state_manager.visited_ids)} Total {len(self.data.data)}")
		pbar = tqdm(total=total_tasks)

		consumers = [asyncio.create_task(consumer(pbar)) for _ in range(workers)]

		await asyncio.gather(*producers)
		await queue.join()  # Ensure all tasks are processed

		for c in consumers:
			c.cancel()

		await asyncio.gather(*consumers, return_exceptions=True)
		pbar.close()

		return results

	def parse_reuslt(self, result):
		pass


argparser = argparse.ArgumentParser()
argparser.add_argument("--input_file", type=str, default="output/example_diff.jsonl", help="Path to the input file")
argparser.add_argument("--output_file", type=str, default="output/check_agent.jsonl",
					   help="Path to the output file")
argparser.add_argument("--workers", type=int, default=3, help="Number of workers")
args = argparser.parse_args()

input_file = args.input_file
output_file = args.output_file

diff_data = DiffData(input_file)
sm = StateManager(output_file)
check_diff_client = CheckDiffClient(diff_data, sm, output_file)
res = asyncio.run(check_diff_client.check_diff_batch(workers=args.workers))
