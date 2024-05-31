"""
By 钱忱
脚本功能：Duration统计
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
from analysis_utils import get_code, get_test_tasks, get_task2name


warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_chatdev"

array = []
for root, directories, filenames in os.walk(warehouse_root):
    for filename in filenames:
        if filename.endswith(".log"):
            # print(filename)
            filepath = os.path.join(root, filename)
            lines = open(filepath).read().split("\n")
            lines = [line for line in lines if "**duration**=" in line]
            duration = lines[0].split("=")[-1].split("s")[0]
            duration = float(duration)
            array.append(duration)
print(len(array), array)
print(os.path.basename(warehouse_root), np.average(array))
