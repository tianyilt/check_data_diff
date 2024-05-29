#!/usr/bin/env python
# coding=utf-8
# Copyright 2024 The PJLab OpenLM. team. All rights reserved.
import os
import json
from tqdm import tqdm
import difflib
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from itertools import islice


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


def read_jsonl(file_path, progress_bar, sample_num=None):
	"""
	Read jsonl file and update the progress bar.
	:param file_path: Path to the jsonl file.
	:param progress_bar: tqdm progress bar instance.
	:param sample_num: Number of samples to read from each file. if None read all.
	:return: List of data from the jsonl file.
	"""
	data = []
	with open(file_path, 'r', encoding='utf-8') as file:
		if sample_num:
			lines = list(islice(file, sample_num))
		else:
			lines = file.readlines()
		for line in lines:
			# if 'null\n' not in line:
			data.append(json.loads(line))
			progress_bar.update(1)
	return data


def read_all_jsonl(dir, workers=10, sample_num=None):
	"""
	Read all jsonl files in a directory using multiple threads.
	:param dir: Directory containing jsonl files.
	:param workers: Number of worker threads.
	:param sample_num: Number of samples to read from each file. if None read all.
	:return: List of data from all jsonl files.
	"""
	files = [os.path.join(dir, f) for f in os.listdir(dir) if f.endswith("jsonl")]
	# total_lines = sum(sum(1 for _ in open(file, 'r', encoding='utf-8')) for file in files)
	total_lines = 999999999
	data = []

	with tqdm(total=total_lines, desc="Reading JSONL files", unit="line") as progress_bar:
		with ThreadPoolExecutor(max_workers=workers) as executor:
			future_to_file = {executor.submit(read_jsonl, file, progress_bar, sample_num): file for file in files}
			for future in as_completed(future_to_file):
				data.extend(future.result())
	return data


def ensure_output(output_path):
	# Initialize output file
	if output_path:
		if not os.path.exists(output_path):
			os.makedirs(os.path.dirname(output_path))
			# touch output_path
			open(output_path, 'a').close()


def remove_symbols(text):
	# # 移除所有非字母和非数字字符
	# text = re.sub(r'\$\$', '$', text)
	# only keep chinese characters
	pattern = re.compile(r'[\u4e00-\u9fa5]+')
	# return ''.join(pattern.findall(text))
	return text


def get_q_main_for_xes_clean(content):
	question_list = content['ori']['question_list']
	q_main_str = content['ori']['q_main']
	options = content['ori']['options']
	res = q_main_str
	for question in question_list:
		res += question
	for option in options:
		res += option
	return res


def get_q_main(content):
	question_list = content['question_list']
	q_main_str = content['q_main']
	options = content['options']
	res = q_main_str
	for question in question_list:
		res += question
	for option in options:
		res += option
	return res
