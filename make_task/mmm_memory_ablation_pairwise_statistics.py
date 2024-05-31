"""
By 钱忱
脚本功能：ChatDev和mmm的对比图进行信息分类统计
"""
import os
import re
import sys
import difflib
import hashlib
import time
import numpy as np
from graphviz import Digraph
from analysis_utils import get_cates, get_task2cate, get_task2name, get_test_tasks

class Node:
    def __init__(self, idd, info):
        self.idd = idd
        self.info = info

class Edge:
    def __init__(self, source, target, info):
        self.source = source
        self.target = target
        self.info = info

class Graph:
    def __init__(self, lines):
        self.nodes = {}
        self.edges = []
        self.name = ""

        assert len(lines) > 0

        nodes = [line for line in lines if "->" not in line]
        edges = [line for line in lines if "->" in line]
        for node in nodes:
            idd = node.split("[")[0].strip()
            info = node.split("[")[-1].split("]")[0].strip("\" ")
            self.nodes[idd] = Node(idd, info)
        for edge in edges:
            source = edge.split("->")[0].strip("\" ")
            target = edge.split("->")[-1].split("[")[0].strip("\" ")
            info = edge.split("[")[-1].split("]")[0].strip("\" ")
            self.edges.append(Edge(source, target, info))

    def view(self):
        graph = Digraph(format="png", node_attr={"shape": "circle"}, edge_attr={"arrowhead": "normal"})
        for idd in self.nodes.keys():
            graph.node(idd, self.nodes[idd].info.replace("\t", "\n").replace("label=", "").strip("\""))
        for edge in self.edges:
            graph.edge(edge.source, edge.target, edge.info.replace("\t", "\n").replace("label=", "").strip("\""))
        # graph.render(directory="./pngs", filename=self.name)
        graph.view(directory="./pngs", filename=self.name)

    def statistics(self):
        collect, result = {}, {}
        # for idd in self.nodes.keys():
        #     node = self.nodes[idd]
        #     info = node.info
        #     objs = info.split("\t")
        #     for obj in objs:
        #         u = obj.split("=")[0]
        #         v = obj.split("=")[-1]
        #         if u not in collect:
        #             collect[u] = []
        #         collect[u].append(v)
        # for key in collect.keys():
        #     if key in ["mid"]:
        #         continue
        #     try:
        #         values = [float(v) for v in collect[key]]
        #     except:
        #         continue
        #     result[key] = np.average(values)
        #
        # result["tca*tta"] = result["tca"] * result["tta"]
        #
        # phases = [edge.info.split("\t")[-1].strip() for edge in self.edges]
        # for keyword in ["Coding", "CodeComplete", "CodeReviewModification", "TestModification"]:
        #     result[keyword] = len([phase for phase in phases if phase==keyword])
        # result["Coding"] = 1
        #
        # # other statistics
        # visit, counter = {}, 0
        # for edge in self.edges:
        #     if "CodeReviewModification" in edge.info:
        #         counter += 1
        #     visit[edge.source] = True
        #     if "CodeReviewModification" in edge.info and edge.target in visit.keys():
        #         break
        # result["CodeReviewModification_Loop"] = counter
        #
        # result["FirstNode_Line"] = int(self.nodes[self.edges[0].source].info.split("line=")[-1].split("\t")[0])
        # result["LastNode_Line"] = int(self.nodes[self.edges[-1].target].info.split("line=")[-1].split("\t")[0])
        #
        # result["#SelfLoop"] = len([edge for edge in self.edges if edge.source == edge.target])
        #
        # result["Exist_Test"] = 1 if "TestModification" in phases else 0
        #
        # result["EdgeNum"] = len(self.edges)

        lastnode = self.nodes[self.edges[-1].target]
        lines = lastnode.info.split("\t")
        lines = [line for line in lines if "tca=" in line]
        tca = float(lines[0].split("=")[-1].strip())
        result["lastnode_tca"] = tca

        return result

def print_statistics(png_filepaths):

    # print("len(png_filepaths):", len(png_filepaths))

    chatdev_map, mmm_map = {}, {}
    counter = 0
    for filepath in png_filepaths:
        # print(filepath)
        if not os.path.exists(filepath):
            continue
        # assert os.path.exists(filepath)
        content = open(filepath).read()
        for keyword in ["mid=", "#line=", "tca=", "tta=", "ttb=", "Coding", "CodeComplete", "CodeReviewModification", "TestModification", "TestModification"]:
            content = content.replace(f"\n{keyword}", f"\t{keyword}")
        lines = content.split("\n")
        lines = [line.strip("\t\n ") for line in lines]
        lines = [line for line in lines if "[" in line and "]" in line and "label=" in line]

        name1, name2 = "test_mmm".lower(), "test_ablation_HeadToTail".lower()
        chatdev_graph = Graph([line for line in lines if name1 in line.lower()])
        mmm_graph = Graph([line for line in lines if name2 in line.lower()])

        assert len(chatdev_graph.nodes.keys()) > 0
        assert len(mmm_graph.nodes.keys()) > 0

        chatdev_graph.name = name1
        mmm_graph.name = name2

        # chatdev_graph.view()
        # mmm_graph.view()

        _chatdev = chatdev_graph.statistics()
        _mmm = mmm_graph.statistics()

        for key in _chatdev:
            if key not in chatdev_map:
                chatdev_map[key] = []
            chatdev_map[key].append(_chatdev[key])
        for key in _mmm:
            if key not in mmm_map:
                mmm_map[key] = []
            mmm_map[key].append(_mmm[key])

        counter += 1

    keys = sorted(list(chatdev_map.keys()))
    for key in keys:
        print("{}\t{}".format(key, key), end="\t")
    print()
    for key in keys:
        print("{:.4f}\t{:.4f}".format(np.average([float(v) for v in chatdev_map[key]]),
                                      np.average([float(v) for v in mmm_map[key]])), end="\t")
    print()

warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_ablation_HeadToTail"
png_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/pngs"
assert os.path.isdir(png_root)

all_cates = get_cates()
task2cate = get_task2cate()
task2name = get_task2name()

directories = [os.path.join(warehouse_root, directory) for directory in os.listdir(warehouse_root) if os.path.isdir(os.path.join(warehouse_root, directory))]
directories = sorted(directories)
tasks = [open(os.path.join(directory, filename)).read().strip("\"") for directory in directories for filename in os.listdir(directory) if filename.endswith(".prompt")]

names, cates = [], []
for task in tasks:
    if task not in task2name:
        names.append("Guess That Tune Trivia")
        cates.append("Entertainment")
    else:
        names.append(task2name[task])
        cates.append(task2cate[task])

assert len(directories) == len(tasks) and len(cates) == len(directories) and len(names) == len(directories)

indexs = [i for i in range(0, 200, 20)]
directories = [directories[index] for index in indexs]

# for cate in sorted(list(all_cates)) + [""]:
for cate in [""]:
    sub_directories = [directory for i,directory in enumerate(directories) if cate=="" or cates[i]==cate]
    assert len(sub_directories) > 0
    png_filepaths = [os.path.join(png_root, "pairwise_"+os.path.basename(directory)) for i,directory in enumerate(sub_directories)]
    assert len(sub_directories) == len(png_filepaths)
    print(cate, end="\t")
    print_statistics(png_filepaths)
