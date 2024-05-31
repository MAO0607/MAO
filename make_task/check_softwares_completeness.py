"""
By 钱忱
脚本功能：检查一个warehouse_root目录下的所有软件目录是否覆盖测试集
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
    if category not in cate2tasks.keys():
        cate2names[category] = []
        cate2tasks[category] = []
    cate2names[category].append(name)
    cate2tasks[category].append(task)

warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm"
chatdev_directories = [chardev_directory for chardev_directory in os.listdir(warehouse_root) if os.path.isdir(os.path.join(warehouse_root, chardev_directory))]
chatdev_tasks = [open(os.path.join(warehouse_root, chatdev_directory, filename)).read() for chatdev_directory in chatdev_directories for filename in os.listdir(os.path.join(warehouse_root, chatdev_directory)) if filename.endswith(".prompt")]

for category in cate2tasks.keys():
    names = cate2names[category]
    tasks = cate2tasks[category]
    assert len(tasks) == 30
    # print(category, len(cate2tasks[category]))

    for (name, task) in zip(names[25:], tasks[25:]):
        matched_directory = sorted([chatdev_directories[i] for i, chatdev_task in enumerate(chatdev_tasks) if chatdev_task == task])
        if len(matched_directory) == 0:
            print("!!!", name, task)
