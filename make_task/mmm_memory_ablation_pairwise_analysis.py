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
from openai import OpenAI

client = OpenAI(
    api_key='sk-R0heaABPw3Fux159D2E60cDd4c3245A596B40201155a6a06',
    base_url="https://sailaoda.cn/v1",
)
import numpy as np
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
from random import shuffle

# TODO: The 'openai.api_base' option isn't read in the client API. You will need to pass it when you instantiate the client, e.g. 'OpenAI(api_base="https://sailaoda.cn/v1")'

chatdev_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_mmm" # 用mmm分支下Memory=False跑出的所有软件
mmm_root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/make_task/test_ablation_HeadToTail" # 用mmm分支下Memory=True跑出的所有软件

assert os.path.isdir(chatdev_root)
assert os.path.isdir(mmm_root)
chat_cache, embedding_chche = {}, {}

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

def get_response(request):
    if request in chat_cache.keys():
        return chat_cache[request]
    else:
        messages = [{"role": "user", "content": request}]
        response = client.chat.completions.create(messages=messages,
        model="gpt-3.5-turbo-16k",
        temperature=0.2,
        top_p=1.0,
        n=1,
        stream=False,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        logit_bias={})
        if "choices" in response.keys():
            response_text = response['choices'][0]['message']['content']
        else:
            print("!!! \"choices\" not in response.keys()")
            print(response)
            assert False
        chat_cache[request] = response_text
    return response_text

def get_text_embedding(text: str):
    if text in embedding_chche.keys():
        return embedding_chche[text]
    else:
        response = openai.Embedding.create(input=[text], model="text-embedding-ada-002")
        if "data" in response:
            ada_embedding = response['data'][0]['embedding']
        else:
            print("!!! \"data\" not in response.keys()")
            print(response)
            assert False
        embedding_chche[text] = ada_embedding
    return ada_embedding

def get_code_embedding(text: str):
    if text in embedding_chche.keys():
        return embedding_chche[text]
    else:
        response = client.embeddings.create(input=[text], model="text-embedding-ada-002")
        if "data" in response:
            ada_embedding = response['data'][0]['embedding']
        else:
            print("!!! \"data\" not in response.keys()")
            print(response)
            assert False
        embedding_chche[text] = ada_embedding
    return ada_embedding

def get_cosine_similarity(embeddingi, embeddingj):
    embeddingi = np.array(embeddingi)
    embeddingj = np.array(embeddingj)
    cos_sim = embeddingi.dot(embeddingj) / (np.linalg.norm(embeddingi) * np.linalg.norm(embeddingj))
    return cos_sim

def post_process(back_instruction: str):
    back_instruction = back_instruction.replace("\"", "")
    words = back_instruction.split(" ")
    if words[1]=="code": words[1] = "software"
    if words[2]=="code": words[2] = "software"
    if words[3]=="code": words[3] = "software"
    if words[1] == "above": words[1] = ""
    if words[2] == "above": words[2] = ""
    back_instruction = " ".join(words).replace("  ", " ")
    return back_instruction

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

def generate_state_transition_graph(directory):
    def get_fingerprints(directory):
        directory = directory
        logdir = [filename for filename in os.listdir(directory) if filename.endswith(".log")]
        if len(logdir) > 0:
            log_filename = logdir[0]
            print("log_filename:", log_filename)
        else:
            raise Exception("No log file found in {}".format(directory))

        content = open(os.path.join(directory, log_filename), "r", encoding='UTF-8').read()

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

        codebook, fingerprints, codelines = {}, [], []
        task_code_alignments, task_task_alignments, bleu_scores = [], [], []
        for utterance in utterances_code:
            update_codebook(utterance, codebook)
            code = get_codes(codebook)
            code = remove_comments(code)
            fingerprint = "{}".format(hashlib.md5(code.encode(encoding='UTF-8')).hexdigest())
            fingerprints.append(fingerprint)
            codelines.append(len(code.split("\n")))

            # prompt = """{codes}\n\nProvide a sentence that describes the key functionality of the above code. For example: \"An action game where the player must eliminate a wave of incoming enemy forces using their shooting skills\" or \"Monster Mayhem is an action game where players take on the role of a fearless monster hunter tasked with eliminating hordes of terrifying creatures\".""".replace(
            #     "{codes}", code)
            # back_instruction = post_process(get_response(prompt)).replace("\t", " ").replace("\n", " ").replace("  ", " ")

            task_code_alignment = get_cosine_similarity(get_text_embedding(task_prompt), get_code_embedding(code))
            # task_task_alignment = get_cosine_similarity(get_embedding(task_prompt), get_embedding(back_instruction)) TBD
            task_task_alignment = -1.0
            # bleu_score = sentence_bleu([task_prompt.split(" ")], back_instruction.split(" ")) TBD
            bleu_score = -1.0
            task_code_alignments.append(task_code_alignment)
            task_task_alignments.append(task_task_alignment)
            bleu_scores.append(bleu_score)

        node_infos = ["mid={}\n#line={}\ntca={:.4f}\ntta={:.4f}\nttb={:.4f}".format(fingerprints[i][:4], codelines[i], task_code_alignments[i], task_task_alignments[i], bleu_scores[i]) for i in range(len(fingerprints))]
        edge_infos = ["{}\n{}".format(i, phases[i]) for i in range(len(fingerprints))]

        return fingerprints, node_infos, edge_infos

    def plot_fingerprints(chatdev_fingerprints, chatdev_node_infos, chatdev_edge_infos, mmm_fingerprints, mmm_node_infos, mmm_edge_infos, filename):
        graph = Digraph(format="png", node_attr={"shape": "circle"}, edge_attr={"arrowhead": "normal"})

        suffix1 = os.path.basename(chatdev_root)
        suffix2 = os.path.basename(mmm_root)

        created = {}
        for i in range(len(chatdev_fingerprints)):
            idd = f"{suffix1}{chatdev_fingerprints[i]}"
            if idd in created.keys():
                continue
            graph.node(idd, "{}\n{}".format(suffix1, chatdev_node_infos[i]))
            created[idd] = True
        for i in range(len(mmm_fingerprints)):
            idd = f"{suffix2}{mmm_fingerprints[i]}"
            if idd in created.keys():
                continue
            graph.node(idd, "{}\n{}".format(suffix2, mmm_node_infos[i]))
            created[idd] = True

        for i in range(len(chatdev_edge_infos)-1):
            graph.edge(f"{suffix1}{chatdev_fingerprints[i]}", f"{suffix1}{chatdev_fingerprints[i+1]}", f"{chatdev_edge_infos[i+1]}")
        for i in range(len(mmm_edge_infos)-1):
            graph.edge(f"{suffix2}{mmm_fingerprints[i]}", f"{suffix2}{mmm_fingerprints[i+1]}", f"{mmm_edge_infos[i+1]}")

        # graph.view(directory="./pngs", filename="pairwise_{}".format(filename))
        graph.render(directory="./pngs", filename="pairwise_{}".format(filename))

    filename = os.path.basename(directory)
    filepath = os.path.join(chatdev_root, "..", "pngs", f"pairwise_{filename}")
    if os.path.exists(filepath):
        print(f"{filename} cached.")
        return

    mmm_task = [open(os.path.join(directory, filename)).read() for filename in os.listdir(directory) if filename.endswith(".prompt")][0]
    chatdev_directories = [chardev_directory for chardev_directory in os.listdir(chatdev_root) if "_NewFeature_" not in chardev_directory]
    chatdev_tasks = [open(os.path.join(chatdev_root, chatdev_directory, filename)).read() for chatdev_directory in chatdev_directories for filename in os.listdir(os.path.join(chatdev_root, chatdev_directory)) if filename.endswith(".prompt")]
    matched_directory = sorted([chatdev_directories[i] for i,chatdev_task in enumerate(chatdev_tasks) if chatdev_task==mmm_task])[-1]
    assert len(matched_directory) > 0
    matched_directory = os.path.join(chatdev_root, matched_directory)

    chatdev_fingerprints, chatdev_node_infos, chatdev_edge_infos = get_fingerprints(matched_directory)
    mmm_fingerprints, mmm_node_infos, mmm_edge_infos = get_fingerprints(directory)
    plot_fingerprints(chatdev_fingerprints, chatdev_node_infos, chatdev_edge_infos, mmm_fingerprints, mmm_node_infos, mmm_edge_infos, filename)

if __name__ == "__main__":
    directories = []
    for directory in os.listdir(mmm_root):
        if "_NewFeature_" not in directory:
            directories.append(os.path.join(mmm_root, directory))
    directories = sorted(directories)
    print("len(directories):", len(directories))

    indexs = [i for i in range(0, 200, 10)]
    directories = [directories[index] for index in indexs]

    for i,directory in enumerate(directories):
        # try:
        generate_state_transition_graph(directory)
        # except:
        #     print("!!! {}".format(os.path.basename(directory)))
            # assert False
        print(i)

        # break
        # if i >= 10:
        #     break
