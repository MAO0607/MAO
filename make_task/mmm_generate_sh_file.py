"""
By 钱忱
脚本功能：生成.sh脚本以批量进行chatdev\mmm实验
"""

import os

lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
lines = [line for line in lines if "," in line]
print(len(lines))
assert len(lines) == 1200

cate2names, cate2tasks = {}, {}
for line in lines:
    objs = line.split(",")
    category = objs[0]
    name = objs[1].replace(" ", "_").replace(":", "_")
    task = ",".join(objs[2:]).strip("\"")
    print(category, name, task)
    if category not in cate2tasks.keys():
        cate2names[category] = []
        cate2tasks[category] = []
    cate2names[category].append(name)
    cate2tasks[category].append(task)

sh_vali = open("./sh_vali1.sh", "w")
sh_test = open("./sh_test1.sh", "w")
for category in cate2tasks.keys():
    names = cate2names[category]
    tasks = cate2tasks[category]
    assert len(tasks) == 30
    print(category, len(cate2tasks[category]))
    for (name, task) in zip(names[20:21], tasks[20:21]):
        sh_vali.write("python run.py --name {} --org auto --task \"{}\"\n".format(name, task))
    for (name, task) in zip(names[25:], tasks[25:]):
        sh_test.write("python run.py --name {} --org auto --task \"{}\"\n".format(name, task))
sh_vali.close()
sh_test.close()
