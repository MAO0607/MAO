import os
import shutil

# shells = open("/Users/qianchen/Workspace/PycharmProjects/ChatDev/sh_test.sh").read().split("\n")
#
# warehouse_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm"
# directories = [directory for directory in os.listdir(warehouse_root) if os.path.isdir(os.path.join(warehouse_root, directory))]
#
# cntMap = {}
# for category in directories:
#     filename = [filename for filename in os.listdir(os.path.join(warehouse_root, category)) if filename.endswith(".log")]
#     if len(filename) != 1:
#         continue
#     filename = filename[0]
#     content = open(os.path.join(warehouse_root, category, filename), "r").read()
#     num = len(content.split("CodeReviewModification")) - 1
#     if num not in cntMap.keys():
#         cntMap[num] = []
#     cntMap[num].append(filename)
# for key in sorted(list(cntMap.keys()))[::-1]:
#     print(key)
#     for filename in cntMap[key]:
#         name = "python3 run.py --name {}".format(filename.split("_CodeCompleteAll")[0])
#         targets = [shell for shell in shells if name in shell]
#         if len(targets) == 1:
#             print(targets[0])
#         else:
#             print("......")
#     print()


# # retry对比并新建better目录
# retry_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm_retry"
# retry_directories = [os.path.join(retry_root, directory) for directory in os.listdir(retry_root) if os.path.isdir(os.path.join(retry_root, directory))]
#
# ori_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm"
# ori_directories = [os.path.join(ori_root, directory) for directory in os.listdir(ori_root)]
# ori_tasks = [open(os.path.join(ori_directory, filename)).read() for ori_directory in ori_directories for filename in os.listdir(ori_directory) if filename.endswith(".prompt")]
#
# better_root = os.path.join(retry_root+"_better")
# assert not os.path.exists(better_root)
# os.mkdir(better_root)
#
# counter = 0
# for i,retry_directory in enumerate(retry_directories):
#
#     retry_task = [open(os.path.join(retry_directory, filename)).read() for filename in os.listdir(retry_directory) if filename.endswith(".prompt")][0]
#
#     ori_directory = sorted([ori_directories[i] for i, ori_task in enumerate(ori_tasks) if ori_task == retry_task])[-1]
#
#     retry_filepath = [os.path.join(retry_directory, filename) for filename in os.listdir(retry_directory) if filename.endswith(".log")][0]
#     ori_filepath = [os.path.join(ori_directory, filename) for filename in os.listdir(ori_directory) if filename.endswith(".log")][0]
#
#     retry_num = len(open(retry_filepath, "r").read().split("CodeReviewModification")) - 1
#     ori_num = len(open(ori_filepath, "r").read().split("CodeReviewModification")) - 1
#
#     if retry_num < ori_num:
#         print(os.path.basename(retry_directory), "Retry", retry_num, ori_num)
#         shutil.copytree(retry_directory, os.path.join(better_root, os.path.basename(retry_directory)))
#         counter += 1
#     # else:
#     #     print(os.path.basename(os.path.dirname(ori_filepath)), "Ori", retry_num, ori_num)
#
#     # if i >= 2:
#     #     break
#
# print("Better Counter: {}/{}".format(counter, i))

def get_duration(filepath):
    lines = open(filepath, "r").read().split("\n")
    duration = [float(line.split("=")[-1].replace("s", "")) for line in lines if "**duration**=" in line]
    return duration[0]

retry_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm"
retry_directories = [os.path.join(retry_root, directory) for directory in os.listdir(retry_root) if os.path.isdir(os.path.join(retry_root, directory))]

ori_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_chatdev"
ori_directories = [os.path.join(ori_root, directory) for directory in os.listdir(ori_root)]
ori_tasks = [open(os.path.join(ori_directory, filename)).read() for ori_directory in ori_directories for filename in os.listdir(ori_directory) if filename.endswith(".prompt")]

counter = 0
retry_info_avg, ori_info_avg = 0.0, 0.0
for i,retry_directory in enumerate(retry_directories):

    retry_task = [open(os.path.join(retry_directory, filename)).read() for filename in os.listdir(retry_directory) if filename.endswith(".prompt")][0]
    ori_directory = sorted([ori_directories[i] for i, ori_task in enumerate(ori_tasks) if ori_task == retry_task])[-1]

    retry_filepath = [os.path.join(retry_directory, filename) for filename in os.listdir(retry_directory) if filename.endswith(".log")][0]
    ori_filepath = [os.path.join(ori_directory, filename) for filename in os.listdir(ori_directory) if filename.endswith(".log")][0]


    retry_info = get_duration(retry_filepath)
    ori_info = get_duration(ori_filepath)

    retry_info_avg += retry_info
    ori_info_avg += ori_info

    if retry_info < ori_info:
        print(os.path.basename(retry_directory), "Retry", retry_info, ori_info)
        counter += 1
    else:
        print(os.path.basename(ori_directory), "Ori", retry_info, ori_info)

    # if i >= 99:
    #     break

print("Better Counter: {}/{}".format(counter, i))
print("retry_info_avg", retry_info_avg * 1.0 / i)
print("ori_info_avg", ori_info_avg * 1.0 / i)
