#!/usr/bin/env python
# coding=utf-8
# Copyright 2024 The PJLab OpenLM. team. All rights reserved.

from utils.utils import read_all_jsonl, get_q_main, get_q_main_for_xes_clean, remove_symbols, ensure_output
import argparse
import difflib
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from copy import deepcopy

def compare_fields(data1_content, data2_content):
	differences = {}
	if data1_content['question_list'] != data2_content['question_list']:
		differences['question_list'] = {
			'dir1': data1_content['question_list'],
			'dir2': data2_content['question_list'],
			'diff': list(difflib.unified_diff(
				data1_content['question_list'],
				data2_content['question_list'],
				lineterm=''
			))
		}
	if data1_content['q_main'] != data2_content['q_main']:
		differences['q_main'] = {
			'dir1': data1_content['q_main'],
			'dir2': data2_content['q_main'],
			'diff': list(difflib.unified_diff(
				data1_content['q_main'],
				data2_content['q_main'],
				lineterm=''
			))
		}
	return differences


def calculate_similarity_and_diff(content1, content2):
	# Extract q_main fields
	q_main_list1 = get_q_main_for_xes_clean(content1)
	q_main_list2 = get_q_main(content2)

	# Join q_main fields to form a single string for comparison
	text1 = deepcopy(q_main_list1)
	text2 = deepcopy(q_main_list2)
	# print(text1, text2)
	# Remove symbols from text
	text1 = remove_symbols(text1)
	text2 = remove_symbols(text2)
	# print(text1, text2)
	# Calculate similarity
	similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

	# Calculate differences
	diff = list(difflib.unified_diff(text1.splitlines(), text2.splitlines(), lineterm=''))

	return similarity, diff, q_main_list1, q_main_list2, text1, text2


def process_intersection(intersection_id, visited, output_path):
	if intersection_id in visited:
		return None

	data1_content = exam_problem2data1[intersection_id]
	data2_content = exam_problem2data2[intersection_id]

	similarity, diff, q_main1, q_main2, text1, text2 = calculate_similarity_and_diff(data1_content, data2_content)
	if similarity < 0.9 and len(text1)<len(text2):
		res_dict = {
			'exam_id': data2_content['exam_id'],
			'problem_id': data2_content['problem_id'],
			'similarity': similarity,
			'diff': diff,
			'q_main1': q_main1,
			'q_main2': q_main2,
			'text1': text1,
			'text2': text2,
			"data1": data1_content,
			"data2": data2_content
		}

		with open(output_path, 'a', encoding='utf-8') as file:
			file.write(json.dumps(res_dict, ensure_ascii=False) + '\n')

		return res_dict

	return None


parser = argparse.ArgumentParser(
	description='check the different of selected fields from jsonl files of two dirs with the same id.')
parser.add_argument('--dir1', type=str, default="/fs-computility/llm/shared/leizhikai/kaoshi/xueersi/XES_V0524_Clean",
					help='Path to the first directory')
parser.add_argument('--dir2', type=str,
					default="/fs-computility/llm/shared/huhanglei/math_equation/data_filter/replace_data_3",
					help='Path to the second directory')
parser.add_argument('--output_path', type=str, default="output/diff_xes_clean_0524.jsonl",
					help='Path to the output file')
parser.add_argument('--workers', type=int, default=5, help='Number of workers')
parser.add_argument('--is_sample', type=bool, default=False, help='Whether to sample the result')
args = parser.parse_args()

IS_SAMPLE = args.is_sample
WORKERS = args.workers
dir1 = args.dir1
dir2 = args.dir2
output_path = args.output_path

if IS_SAMPLE:
	sample_num = 1000
else:
	sample_num = None

data1 = read_all_jsonl(dir1, workers=WORKERS, sample_num=sample_num)
data2 = read_all_jsonl(dir2, workers=WORKERS, sample_num=sample_num)

# 初始化变量
exam_problem_id1 = []
exam_problem_id2 = []
exam_problem2data1 = {}
exam_problem2data2 = {}
# 单次遍历完成所有初始化操作
for d in tqdm(data1):
	key = f"{d['id']}"
	exam_problem_id1.append(key)
	exam_problem2data1[key] = d

for d in tqdm(data2):
	key = f"{d['exam_id']}_{d['problem_id']}"
	exam_problem_id2.append(key)
	exam_problem2data2[key] = d

# 交集
intersection = set(exam_problem_id1) & set(exam_problem_id2)

intersection_list = list(intersection)
if IS_SAMPLE:
	intersection_list = intersection_list[:100]


visited = set()
all_differences = []
ensure_output(output_path)
# Load already visited IDs from output file if exists
if os.path.exists(output_path):
	with open(output_path, 'r', encoding='utf-8') as file:
		for line in tqdm(file):
			res_dict = json.loads(line)
			exam_id = res_dict["data2"]['exam_id']
			problem_id = res_dict["data2"]['problem_id']
			visited.add(f"{exam_id}_{problem_id}")

# Use ThreadPoolExecutor for multithreading
with ThreadPoolExecutor(max_workers=10) as executor:
	futures = {executor.submit(process_intersection, intersection_id, visited, output_path): intersection_id for
			   intersection_id in intersection_list}

	for future in tqdm(as_completed(futures), total=len(futures)):
		result = future.result()
		if result is not None:
			all_differences.append(result)

