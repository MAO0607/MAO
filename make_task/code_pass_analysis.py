"""
By 钱忱
脚本功能：代码的pass数量统计
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
from analysis_utils import get_code, get_test_tasks, get_task2name, remove_comments, getFilesFromType


# for full-gptengineer & full-metagpt
# warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/full"
# warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_chatdev"
warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/chatdev_ablation/to_design_coding_complete_review_test"
print("root:", os.path.basename(warehouse_root))

directories = [os.path.join(warehouse_root, directory) for directory in os.listdir(warehouse_root) if os.path.isdir(os.path.join(warehouse_root, directory))]
directories = [directory for directory in directories if "_NewFeature_" not in directory]
directories = sorted(directories)
print("len(directories):", len(directories))

counter, passSet = 0, set()
for i,directory in enumerate(directories):
    if "gptengineer" in warehouse_root:
        name = os.path.basename(directory).split("_")[0].strip().replace(" ", "_")
    elif "metagpt" in warehouse_root:
        name = os.path.basename(directory).split("-")[0].strip().replace(" ", "_")
    else:
        name = "None"

    vn = get_code(directory)
    # vn = remove_comments(vn)
    lines = vn.split("\n")
    linesnum = len(lines)

    filesnum = len(getFilesFromType(directory, ".py"))

    duration = float(open(os.path.join(directory, getFilesFromType(directory, ".log")[0])).read().split("**duration**=")[-1].split("s")[0].split("\n")[0])

    tokens_num = int(open(os.path.join(directory, getFilesFromType(directory, ".log")[0])).read().split("**num_total_tokens**=")[-1].split("\n")[0])

    lines = [line for line in lines if
             "password" not in line.lower() and "passenger" not in line.lower() and "passed" not in line.lower() and "passes" not in line.lower()]
    lines = [line for line in lines if "pass" in line.lower() or "todo" in line.lower()]
    for line in lines:
        passSet.add(line)
    passNum = len(lines)
    passFlag = 1 if passNum > 0 else 0
    counter += 1
    print("{:.4f}\t{:.0f}\t{:.0f}\t{:.0f}".format(duration, tokens_num, filesnum, linesnum))

