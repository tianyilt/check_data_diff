#!/bin/bash

# 设置环境变量
export DIR1="/fs-computility/llm/shared/leizhikai/kaoshi/xueersi/XES_V0524_Clean"
export DIR2="/fs-computility/llm/shared/huhanglei/math_equation/data_filter/replace_data_3"
export OUTPUT_PATH="output/diff_all.jsonl"
export EXAMPLE_DIFF_PATH="output/example_diff.jsonl"
export AGENT_OUTPUT_PATH="output/agent_diff.jsonl"
export AGENT_REPORT_PATH="output/agent_report.jsonl"
export WORKERS=30
export AGENT_WORKERS=2 # 太大会超过LLM单位时间内请求限制
export IS_SAMPLE=false

# 运行 Python 脚本
python3 check_data_diff.py \
  --dir1="$DIR1" \
  --dir2="$DIR2" \
  --output_path="$OUTPUT_PATH" \
  --workers="$WORKERS" \
  --is_sample="$IS_SAMPLE"

python3 sample_example_diff.py \
  --output_path="$OUTPUT_PATH" \
  --example_diff_path="$EXAMPLE_DIFF_PATH" \

python3 agents/check_diff_agents.py \
	--input_path="$EXAMPLE_DIFF_PATH" \
	--output_path="$AGENT_OUTPUT_PATH" \
	--report_file="$AGENT_REPORT_PATH" \
	--workers="$AGENT_WORKERS" \
