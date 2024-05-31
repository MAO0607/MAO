"""
By 钱忱
脚本功能：ChatDev和mmm的对比图进行信息分类统计（重构图）
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
from analysis_utils import get_cates, get_task2cate, get_task2name, get_test_tasks
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from queue import Queue

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

def get_codes(codebook):
    content = ""
    for filename in codebook.keys():
        content += "{}\n```{}\n{}\n```\n\n".format(filename, "python" if filename.endswith(".py") else
        filename.split(".")[-1], codebook[filename])
    return content

def remove_comments(string):
    lines = string.split("\n")
    lines = [line for line in lines if not line.strip().startswith("#")]
    string = "\n".join(lines)

    comments = []
    regex = r"'''(.*?)'''"
    matches = re.finditer(regex, string, re.DOTALL)
    for match in matches:
        group1 = match.group(1)
        comments.append(group1)
    for comment in comments + ["''''''\n"]:
        string = string.replace(comment, "")
    return string

class Node:
    def __init__(self, idd, code):
        self.idd = idd
        self.code = code

class Edge:
    def __init__(self, source, target):
        self.source = source
        self.target = target

class Graph:
    def __init__(self, directory):
        self.nodes = {}
        self.edges = []
        self.directory = directory

        logdir = [filename for filename in os.listdir(directory) if filename.endswith(".log")]
        if len(logdir) > 0:
            log_filename = logdir[0]
            # print("log_filename:", log_filename)
        else:
            raise Exception("No log file found in {}".format(directory))

        content = open(os.path.join(directory, log_filename), "r", encoding='UTF-8').read()

        # print(os.path.basename(directory), "TestModification" in content)

        task_prompt = [line.split("**task_prompt**: ")[-1].strip() for line in content.split("\n") if "**task_prompt**: " in line]
        assert len(task_prompt) == 1
        task_prompt = task_prompt[0]

        utterances = []
        regex = r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \w+)\] ([.\s\S\n\r\d\D\t]*?)(?=\n\[\d|$)"
        matches = re.finditer(regex, content, re.DOTALL)
        for match in matches:
            group1 = match.group(1)
            group2 = match.group(2)
            utterances.append("[{}] {}".format(group1, group2))
        utterances = [utterance for utterance in utterances if "flask app.py" not in utterance and "OpenAI_Usage_Info" not in utterance]
        index = [i for i, utterance in enumerate(utterances) if "Programmer<->Chief Technology Officer on : EnvironmentDoc" in utterance]
        if len(index) > 0:
            utterances = utterances[:index[0] - 1]

        utterances_code = [utterance for utterance in utterances if "Programmer<->" in utterance and ("Coding" in utterance or "CodeComplete" in utterance or "CodeReviewModification" in utterance or "TestModification" in utterance)]

        phases = [utterance.split(", turn")[0].split(" ")[-1] for utterance in utterances_code]

        codebook, codes, fingerprints = {}, [], []
        for utterance in utterances_code:
            update_codebook(utterance, codebook)
            code = get_codes(codebook)
            code = remove_comments(code)
            codes.append(code)
            fingerprint = "{}".format(hashlib.md5(code.encode(encoding='UTF-8')).hexdigest())
            fingerprints.append(fingerprint)

        for i,code in enumerate(codes):
            if fingerprints[i] not in self.nodes.keys():
                self.nodes[fingerprints[i]] = Node(fingerprints[i], code)
        for i, code in enumerate(codes):
            if i+1 < len(codes):
                source = fingerprints[i]
                target = fingerprints[i+1]
                self.edges.append(Edge(source, target))

    def view(self):
        graph = Digraph(format="png", node_attr={"shape": "circle"}, edge_attr={"arrowhead": "normal"})
        for idd in self.nodes.keys():
            graph.node(idd, self.nodes[idd].idd[:4])
        for i,edge in enumerate(self.edges):
            graph.edge(edge.source, edge.target, "{}".format(i+1))
        # graph.render(directory="./pngs", filename=self.name)
        if not os.path.exists("./pngs"):
            os.mkdir("./pngs")
        graph.view(directory="./pngs", filename="tmp")

    def find_shortest_path(self):
        uID = self.edges[0].source
        vID = self.edges[-1].target

        Q, visit, preID, preEdge = Queue(), {}, {}, {}
        Q.put(uID)
        visit[uID] = True
        while not Q.empty():
            mID = Q.get()
            if mID == vID:
                id, pathNodes, pathEdges = vID, [], []
                while id != uID:
                    pathNodes.append(id)
                    pathEdges.append(preEdge[id])
                    id = preID[id]
                pathNodes.append(uID)
                pathNodes = pathNodes[::-1]
                pathEdges = pathEdges[::-1]
                # print("BFSShortestPath_Nodes:", len(pathNodes), pathNodes)
                # print("BFSShortestPath_Edges", len(pathEdges), pathEdges)
                return pathNodes, pathEdges
            nextIDs = [edge.target for edge in self.edges if edge.source == mID]
            nextEdges = [edge for edge in self.edges if edge.source == mID]
            for i in range(len(nextIDs)):
                nextMID = nextIDs[i]
                nextEdge = nextEdges[i]
                if nextMID not in visit.keys():
                    Q.put(nextMID)
                    visit[nextMID] = True
                    preID[nextMID] = mID
                    preEdge[nextMID] = nextEdge

    def statistics(self):
        result = {}
        result["#nodes"] = len(self.nodes.keys())
        result["#edges"] = len(self.edges)
        pathNodes, pathEdges = self.find_shortest_path()
        result["#ShortestPathNodes"] = len(pathNodes)
        result["#ShortestPathEdges"] = len(pathEdges)
        result["#ZombieNodes"] = len(self.nodes.keys()) - len(pathNodes)
        result["#ZombieEdges"] = len(self.edges) - len(pathEdges)

        # self.view()
        loopNum, visit = 0, {}
        visit[self.edges[0].source] = True
        for edge in self.edges:
            if edge.target in visit.keys():
                loopNum += 1
            visit[edge.target] = True
        result["#Loop"] = loopNum

        result["#SelfLoop"] = len([edge for edge in self.edges if edge.source == edge.target])

        vn = self.nodes[self.edges[-1].target].code.lower()
        lines = vn.split("\n")
        lines = [line for line in lines if "password" not in line.lower() and "passenger" not in line.lower() and "passed" not in line.lower() and "passes" not in line.lower()]
        lines = [line for line in lines if "pass" in line.lower() or "todo" in line.lower()]
        for line in lines:
            passSet.add(line)
        passNum = len(lines)
        result["#pass"] = passNum
        result["passFlag"] = 1 if passNum > 0 else 0

        return result

def print_statistics(directories):

    vmap = {}
    for directory in directories:
        graph = Graph(directory)
        # graph.view()
        _vmap = graph.statistics()
        print("{}\t{}".format( _vmap["#pass"], _vmap["passFlag"]))
        # print("{}\t{}\t{}".format(os.path.basename(directory), _vmap["#pass"], _vmap["passFlag"]))
        for key in _vmap:
            if key not in vmap:
                vmap[key] = []
            vmap[key].append(_vmap[key])

    keys = sorted(list(vmap.keys()))
    for key in keys:
        print("{}".format(key), end="\t")
    print()
    for key in keys:
        print("{:.4f}".format(np.average([float(v) for v in vmap[key]])), end="\t")
    print()

warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_expel_20"
print("root:", os.path.basename(warehouse_root))

task2cate = get_task2cate()

directories = [os.path.join(warehouse_root, directory) for directory in os.listdir(warehouse_root) if os.path.isdir(os.path.join(warehouse_root, directory))]
directories = [directory for directory in directories if "_NewFeature_" not in directory]
directories = sorted(directories)
tasks = [open(os.path.join(directory, filename)).read().strip("\"") for directory in directories for filename in os.listdir(directory) if filename.endswith(".prompt")]

test_tasks = get_test_tasks()
index = [i for i,task in enumerate(tasks) if task in test_tasks]
directories = [directories[i] for i in index]
tasks = [tasks[i] for i in index]

cates = []
for task in tasks:
    if task in task2cate.keys():
        cates.append(task2cate[task])
    else:
        cates.append("Unknown")

assert len(directories) == len(tasks) and len(cates) == len(directories)

passSet = set()

# for cate in sorted(list(get_cates())) + [""]:
for cate in [""]:
    sub_directories = [directory for i,directory in enumerate(directories) if cate=="" or cates[i]==cate]
    # if len(sub_directories) == 0:
    #     continue
    print(cate, end="\t")
    print_statistics(sub_directories)
    # break
print("passSet:")
for line in passSet:
    print(line)
