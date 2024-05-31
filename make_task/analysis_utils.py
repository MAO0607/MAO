import os
import re

def getFilesFromType(sourceDir, filetype):
    files = []
    for root, directories, filenames in os.walk(sourceDir):
        for filename in filenames:
            if filename.endswith(filetype):
                files.append(os.path.join(root, filename))
    return files

def get_task2cate():
    lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
    lines = [line for line in lines if "," in line]
    assert len(lines) == 1200

    task2cate, task2name = {}, {}
    for line in lines:
        objs = line.split(",")
        category = objs[0]
        name = objs[1].replace(" ", "_").replace(":", "_")
        task = ",".join(objs[2:]).strip("\"")
        task2cate[task] = category
        task2name[task] = name

    return task2cate

def get_task2name():
    lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
    lines = [line for line in lines if "," in line]
    assert len(lines) == 1200

    task2cate, task2name = {}, {}
    for line in lines:
        objs = line.split(",")
        category = objs[0]
        name = objs[1].replace(" ", "_").replace(":", "_")
        task = ",".join(objs[2:]).strip("\"")
        task2cate[task] = category
        task2name[task] = name

    return task2name

def get_name2task():
    lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
    lines = [line for line in lines if "," in line]
    assert len(lines) == 1200

    name2task = {}
    for line in lines:
        objs = line.split(",")
        category = objs[0]
        name = objs[1].replace(" ", "_").replace(":", "_")
        task = ",".join(objs[2:]).strip("\"")
        name2task[name] = task

    return name2task

def get_cates():
    lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
    lines = [line for line in lines if "," in line]
    assert len(lines) == 1200

    cates = set()
    for line in lines:
        objs = line.split(",")
        category = objs[0]
        name = objs[1].replace(" ", "_").replace(":", "_")
        task = ",".join(objs[2:]).strip("\"")
        cates.add(category)
    return cates

def get_test_tasks():
    lines = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/输入层：Task-Task汇总.csv").read().split("\n")[1:]
    lines = [line for line in lines if "," in line]
    assert len(lines) == 1200

    cate2tasks = {}
    for line in lines:
        objs = line.split(",")
        category = objs[0]
        name = objs[1].replace(" ", "_").replace(":", "_")
        task = ",".join(objs[2:]).strip("\"")
        if category not in cate2tasks.keys():
            cate2tasks[category] = []
        cate2tasks[category].append(task)

    test_tasks = [task for key in cate2tasks.keys() for task in cate2tasks[key][-5:]]
    assert len(test_tasks) == 200

    return test_tasks

def remove_comments(string):
    def remove_comments_by_regex(string, regex):
        lines = string.split("\n")
        lines = [line for line in lines if not line.strip().startswith("#")]
        string = "\n".join(lines)
        comments = []
        matches = re.finditer(regex, string, re.DOTALL)
        for match in matches:
            group1 = match.group(1)
            comments.append(group1)
        for comment in comments + ["''''''\n"]:
            string = string.replace(comment, "")
        return string

    string = remove_comments_by_regex(string, r"'''(.*?)'''")
    string = remove_comments_by_regex(string, r"\"\"\"(.*?)\"\"\"")
    return string

def get_code(directory):
    def _format_code(code):
        code = "\n".join([line for line in code.split("\n") if len(line.strip()) > 0])
        return code

    # Read all .py files
    codebooks = {}
    filepaths = getFilesFromType(directory, ".py")
    for filepath in filepaths:
        filename = os.path.basename(filepath)
        codebooks[filename] = _format_code(open(filepath, "r", encoding="utf-8").read())

    # Format Codes
    code = ""
    for filename in codebooks.keys():
        code += "{}\n```Python\n{}\n```\n\n".format(filename, codebooks[filename])

    if len(code) == 0:
        code = "# None"

    return code.strip()
