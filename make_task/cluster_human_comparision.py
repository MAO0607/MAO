import os

name2id, name2human = {}, {}
keys = []

root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/"
lines = open(os.path.join(root, "人工对比实验-Baseline对比实验-ChatDev_ID.csv")).read().split("\n")
for line in lines:
    objs = line.split(",")
    if len(objs) < 2:
        continue
    name2id[objs[0]] = objs[1]
    keys.append(objs[0])
print(len(name2id.keys()))

lines = []
for name in ["党余凡", "刘鸿樟", "李嘉豪", "王一飞", "谢子昊", "钱忱", "陈诺"]:
    lines.extend(open(os.path.join(root, "人工对比实验-{}.csv".format(name))).read().split("\n"))
lines = [line for line in lines if "," in line]
for line in lines:
    objs = line.split(",")
    if len(objs) < 3:
        continue
    name2human[objs[1]] = objs[2]
    # print(objs)
print(len(name2human.keys()))

up, down = 0, 0
for name in keys:
    if not (name in name2human.keys() and name in name2id.keys()):
        continue
    human = name2human[name]
    idd = name2id[name][0] # 取第一位字符
    if human == idd:
        up += 1
    down += 1
    print("{}\t{}\t{}".format(name, idd, human))
print(up, down, "{:.4%}".format(up*1.0/down))
