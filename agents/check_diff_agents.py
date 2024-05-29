import os
import argparse
import httpx
from typing import Dict, Any
import requests
import httpx
from typing import Any, Dict, List
from pathlib import Path
import json
import asyncio
import tiktoken
from datetime import datetime
from copy import deepcopy
from tqdm.asyncio import tqdm
from utils.utils import ensure_output
from check_diff_data_loader import DiffData
from state_manager import StateManager
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

	def build_prompt(self, data: Dict[str, Any]):
		# prompt = f"{' '.join(data['q_main'])}"
		prompt = f"{' '.join(data['question_list'])}"
		return prompt

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
				result = await self.rephrase_one(i)
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


argparser = argparse.ArgumentParser()
argparser.add_argument("--input_file", type=str, default="data/check_data.jsonl", help="Path to the input file")
argparser.add_argument("--output_file", type=str, default="data/check_agent_report.md",
					   help="Path to the output file")
argparser.add_argument("--workers", type=int, default=5, help="Number of workers")
args = argparser.parse_args()

input_file = args.input_file
output_file = args.output_file

diff_data = DiffData(input_file)
sm = StateManager(output_file)
check_diff_client = CheckDiffClient(diff_data, sm, output_file)
