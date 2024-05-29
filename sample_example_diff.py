#!/usr/bin/env python
# coding=utf-8
# Copyright 2024 The PJLab OpenLM. team. All rights reserved.
# 从check_data_diff文件的output中按照学科和题型进行采样. 匹配major和q_type的组合，输出每个组合的第一个样本
import os
import json
from collections import Counter, defaultdict
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--output_path', type=str, default="output/diff.jsonl", help='Path to the output file')
parser.add_argument('--example_diff_path', type=str, default="output/example_diff.jsonl", help='Path to the example diff file')
args = parser.parse_args()

output_path = args.output_path
example_diff_path = args.example_diff_path

# example_diff_path = f"example_diff_{os.path.basename(output_path)}.jsonl"
# output_path = "output/diff.jsonl"
result_example_diff = []

if os.path.exists(output_path):
	counter = Counter()
	example_diff_dict = defaultdict(list)

	with open(output_path, 'r', encoding='utf-8') as file:
		record_count = 0
		for line in tqdm(file):
			# if record_count >= 10000:  # 检查是否已达到最大记录数
			# 	break
			record_count += 1
			res_dict = json.loads(line)
			dd = res_dict['data2']
			subject = dd['major']
			q_type = dd['q_type']
			counter[(subject, q_type)] += 1
			example_diff_dict[(subject, q_type)].append(res_dict)

	# Collect the first example of each (subject, q_type) combination
	for key, value in example_diff_dict.items():
		result_example_diff.append(value[0])  # Assuming you want the first occurrence
		print(key)
	# Optionally, save the result to a file
	with open(example_diff_path, 'w', encoding='utf-8') as outfile:
		for item in result_example_diff:
			outfile.write(json.dumps(item, ensure_ascii=False) + '\n')

	print("Processing completed and results saved to", example_diff_path)
	print("Counter results:", counter)


