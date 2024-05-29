# Check Data Diff
LLM预训练重在数据，而每批次数据调整都会在百万到千万行规模中进行数据操作φ，我们很关心φ是否如预期起作用，就需要进行check_data_diff(φ,φ(x))。当前我们传统方法需要manual check with task-specific script,这是个trial and error的过程，是否能用agents实现这个目标成为大家关心的问题.本项目希望能够成为数据构建toolkit中的一个环节,有助于加速内部数据检查工作流

## 参数说明
dir1和dir2是包含jsonl的文件夹,后续将会值读取jsonl
IS_SAMPLE 用于测试 开启后每个文件只会读取前1000行,交集只考虑100行

## 调用方法

调用方法,打开heck_data_diff.sh文件,修改其中的参数,然后执行以下命令
```bash
./scripts/check_data_diff.sh
```

不调用agents的输出结果:
![alt text](doc/image.png)



## 文件结构
```bash
╰─$ tree -L 1
./
├── README.md
├── agents/
├── check_data_diff.ipynb    ipynb版本的脚本
├── check_data_diff.py       主要执行文件,输入dir1,dir2,输出所有diff的output文件
├── output/
├── sample_example_diff.py   从diff的output文件中每个类别抽取一个样本,用户快速可视化
├── scripts/                 shell脚本,调用check_data_diff.py
└── utils/

```

## 修改指南

### 共同的id
不同批次数据id逻辑可能会有变化,修改check_data_diff.py中下面关于key部分
```python
for d in tqdm(data1):
	key = f"{d['id']}"
	exam_problem_id1.append(key)
	exam_problem2data1[key] = d

for d in tqdm(data2):
	key = f"{d['exam_id']}_{d['problem_id']}"
	exam_problem_id2.append(key)
	exam_problem2data2[key] = d
```

### 过滤数据
修改check_data_diff.py中下面关于remove_symbols部分. 比如只保留中文字符对于查看考题的差异是有帮助的
```python
def remove_symbols(text):
	# # 移除所有非字母和非数字字符
	# text = re.sub(r'\$\$', '$', text)
	# only keep chinese characters
	pattern = re.compile(r'[\u4e00-\u9fa5]+')
	# return ''.join(pattern.findall(text))
	return text
```

### 比较数据的field
修改utils/utils.py中下面关于get_q_main部分. 比如只比较考题的内容. 此外两个dir的数据可能字段不一样,需要对应修改
```python
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
```


## License
懂的都懂
