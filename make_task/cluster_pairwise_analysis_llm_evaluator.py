"""
By 钱忱
脚本功能：生成ChatDev和mmm的对比图
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
from analysis_utils import get_code, remove_comments, get_response, get_task2cate, get_task2name


filepath = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/pairwise_analysis_llm_evaluator_gpt_3_5_turbo_16k.tsv"
# filepath = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/pairwise_analysis_llm_evaluator_gpt_4_32k.tsv"

lines = open(filepath).read().split("\n")

cates = get_task2cate().values()

down = 0
win1, win2, draw = 0, 0, 0
for line in lines:
    objs = line.split("\t")
    if len(objs) == 4:
        dirname, category, chatdev_point, mmm_point = objs
        chatdev_point = int(chatdev_point)
        mmm_point = int(mmm_point)
        if chatdev_point == mmm_point:
            draw += 1
        if chatdev_point > mmm_point:
            win1 += 1
        if chatdev_point < mmm_point:
            win2 += 1
        down += 1
assert win1 + win2 + draw == down
print("down:", down)
print("win1:", win1, "{:.2%}".format(win1*1.0/down))
print("win2:", win2, "{:.2%}".format(win2*1.0/down))
print("draw:", draw, "{:.2%}".format(draw*1.0/down))
