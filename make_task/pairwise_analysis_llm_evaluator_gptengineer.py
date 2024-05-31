"""
By 钱忱
脚本功能：生成GPTEngineer和mmm的GPT-4对比分值（越大越好）
"""
import os
import re
import sys
import difflib
import hashlib
import time
from graphviz import Digraph
import openai
import numpy as np
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from random import shuffle
from analysis_utils import get_code, remove_comments, get_task2cate, get_task2name, get_test_tasks, get_cates


openai.api_key = "sk-oEVOlF1AHtU53am90a5368Ed3b8f4597B77bEcCcF49d1c40"
openai.api_base = "https://sailaoda.cn/v1"

# chatdev_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/full-gptengineer"
chatdev_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/full"
mmm_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm"
model = "gpt-4-32k" # "gpt-3.5-turbo-16k"
retry_limit = 2
print("model:", model)

assert os.path.isdir(chatdev_root)
assert os.path.isdir(mmm_root)
chat_cache, embedding_chche = {}, {}

task2cate = get_task2cate()
task2name = get_task2name()

prompt_template = \
"""
----------
[Software Description]:
{task}
----------

----------
[Version1]:
{code1}
----------

----------
[Version2]:
{code2}
----------

We would like to request your feedback on the preference of two code versions of a software.
Please rate the completeness, detailedness, relevance, accuracy, and so on. Each code version receives an overall score on a scale of 1 to 10, where a higher score indicates better overall performance.
Please first provide a comprehensive explanation of your evaluation, avoiding any potential bias and ensuring that the order in which the codes were presented does not affect your judgment. Then, output two lines indicating the scores for version 1 and 2, respectively.
Output with the following format:
Evaluation evidence: <evaluation explanation here>
The score of Version 1: <score>
The score of Version 2: <score>
"""

def get_response(request: str):
    messages = [{"role": "user", "content": request}]
    response = openai.ChatCompletion.create(
        messages=messages,
        model=model,
        temperature=0.2,
        top_p=1.0,
        n=1,
        stream=False,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        logit_bias={},
    )
    response_text = response['choices'][0]['message']['content']
    return response_text

def write_string(string):
    writer.write(string)
    print(string, end="")

def update_codebook(utterance, codebook):
    def extract_filename_from_line(lines):
        file_name = ""
        for candidate in re.finditer(r"(\w+\.\w+)", lines, re.DOTALL):
            file_name = candidate.group()
            file_name = file_name.lower()
        return file_name

    def extract_filename_from_code(code):
        file_name = ""
        regex_extract = r"class (\S+?):\n"
        matches_extract = re.finditer(regex_extract, code, re.DOTALL)
        for match_extract in matches_extract:
            file_name = match_extract.group(1)
        file_name = file_name.lower().split("(")[0] + ".py"
        return file_name

    def _format_code(code):
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    regex = r"(.+?)\n```.*?\n(.*?)```"
    matches = re.finditer(regex, utterance, re.DOTALL)
    for match in matches:
        code = match.group(2)
        if "CODE" in code:
            continue
        group1 = match.group(1)
        filename = extract_filename_from_line(group1)
        if "__main__" in code:
            filename = "main.py"
        if filename == "":
            filename = extract_filename_from_code(code)
        assert filename != ""
        if filename is not None and code is not None and len(filename) > 0 and len(code) > 0:
            codebook[filename] = _format_code(code)

def post_process(back_instruction: str):
    back_instruction = back_instruction.replace("\"", "")
    words = back_instruction.split(" ")
    if words[1]=="code": words[1] = "software"
    if words[2]=="code": words[2] = "software"
    if words[3]=="code": words[3] = "software"
    if words[1] == "above": words[1] = ""
    if words[2] == "above": words[2] = ""
    back_instruction = " ".join(words).replace("  ", " ")
    return back_instruction

def get_win_times_until_limit(task, code1, code2):
    if code1 == code2:
        return 0, 0
    elif code1 == "" and code2 != "":
        return 0, 1
    elif code1 != "" and code2 == "":
        return 1, 0

    prompt_order = prompt_template.replace("{task}",task).replace("{code1}", code1).replace("{code2}", code2)
    prompt_reverse = prompt_template.replace("{task}",task).replace("{code1}", code2).replace("{code2}", code1)

    point1, point2, retry = 0, 0, 0
    while retry < retry_limit:
        response_order = get_response(prompt_order)
        response_reverse = get_response(prompt_reverse)

        v1_order = [line for line in response_order.split("\n") if "The score of Version 1:".lower() in line.lower()]
        v2_order = [line for line in response_order.split("\n") if "The score of Version 2:".lower() in line.lower()]
        v1_reverse = [line for line in response_reverse.split("\n") if "The score of Version 1:".lower() in line.lower()]
        v2_reverse = [line for line in response_reverse.split("\n") if "The score of Version 2:".lower() in line.lower()]

        if not (len(v1_order) == 1 and len(v2_order) == 1 and len(v1_reverse) == 1 and len(v2_reverse) == 1):
            continue

        v1_order = int(v1_order[0].split(":")[-1].split(".")[0])
        v2_order = int(v2_order[0].split(":")[-1].split(".")[0])
        v1_reverse = int(v1_reverse[0].split(":")[-1].split(".")[0])
        v2_reverse = int(v2_reverse[0].split(":")[-1].split(".")[0])

        point1 += v1_order + v2_reverse
        point2 += v2_order + v1_reverse

        if point1 != point2:
            break
        else:
            retry += 1

    print("retry:", retry)
    return point1, point2

def llm_evaluate_until_limit(directory):
    try:
        mmm_task = [open(os.path.join(directory, filename)).read() for filename in os.listdir(directory) if filename.endswith(".prompt")][0]
        chatdev_directories = [chardev_directory for chardev_directory in os.listdir(chatdev_root) if "_NewFeature_" not in chardev_directory]
        chatdev_tasks = [open(os.path.join(chatdev_root, chatdev_directory, filename)).read() for chatdev_directory in chatdev_directories for filename in os.listdir(os.path.join(chatdev_root, chatdev_directory)) if filename.endswith("prompt")]
        matched_directory = sorted([chatdev_directories[i] for i,chatdev_task in enumerate(chatdev_tasks) if chatdev_task==mmm_task])[-1]
        assert len(matched_directory) > 0
        matched_directory = os.path.join(chatdev_root, matched_directory)
    except:
        return None, None, None, None

    if mmm_task not in task2name.keys():
        return None, None, None, None

    name = task2name[mmm_task]
    cate = task2cate[mmm_task]

    chatdev_code = get_code(matched_directory)
    mmm_code = get_code(directory)

    chatdev_code = remove_comments(chatdev_code)
    mmm_code = remove_comments(mmm_code)

    chatdev_point, mmm_point = get_win_times_until_limit(mmm_task, chatdev_code, mmm_code)

    return os.path.basename(directory), cate, chatdev_point, mmm_point

if __name__ == "__main__":
    directories = []
    for directory in os.listdir(mmm_root):
        if "_NewFeature_" not in directory:
            directories.append(os.path.join(mmm_root, directory))
    directories = sorted(directories)
    shuffle(directories)
    print("len(directories):", len(directories))

    tsv_file = (__file__.replace(".py", "")+"_"+model.replace("-", "_").replace(".", "_"))+"_"+os.path.basename(chatdev_root)+"_"+os.path.basename(mmm_root)+".tsv"
    content = ""
    if os.path.exists(tsv_file):
        content = open(tsv_file).read()

    counter = 0
    with open(tsv_file, "a") as writer:
        for i,directory in enumerate(directories):
            dirname = os.path.basename(directory)
            if dirname in content:
                print(dirname, "cached.")
                continue
            dirname, category, chatdev_point, mmm_point = llm_evaluate_until_limit(directory)
            if dirname is not None:
                write_string("{}\t{}\t{}\t{}\n".format(dirname, category, chatdev_point, mmm_point))
                counter += 1
                print(i, "\n")
            else:
                print("!!!", os.path.basename(directory))
            # if counter >= 3:
            #     break

    # 事后分类统计
    for target_category in sorted(list(get_cates())) + [""]:
        down, draw, win1, win2 = 0, 0, 0, 0
        lines = open(tsv_file).read().split("\n")
        for line in lines:
            objs = line.split("\t")
            if len(objs) != 4:
                continue
            dirname, category, point1, point2 = objs
            if target_category == "" or category == target_category:
                if point1 == point2:
                    draw += 1
                elif point1 > point2:
                    win1 += 1
                elif point1 < point2:
                    win2 += 1
                down += 1

        # 填表
        print("{}".format(target_category), end="\t")
        print("{:.8f}".format(win1 * 1.0 / down), end="\t")
        print("{:.8f}".format(win2 * 1.0 / down), end="\t")
        print()
