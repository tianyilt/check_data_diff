#!/bin/bash

# 设置环境变量
export DIR1="/fs-computility/llm/shared/leizhikai/kaoshi/xueersi/XES_V0524_Clean"
export DIR2="/fs-computility/llm/shared/huhanglei/math_equation/data_filter/replace_data_3"
export OUTPUT_PATH="output/diff_xes_clean_0524.jsonl"
export WORKERS=30
export IS_SAMPLE=false

# 运行 Python 脚本
python3 check_data_diff.py \
  --dir1="$DIR1" \
  --dir2="$DIR2" \
  --output_path="$OUTPUT_PATH" \
  --workers="$WORKERS" \
  --is_sample="$IS_SAMPLE"
