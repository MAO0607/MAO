import os
import re
import sys
import difflib
import hashlib
import time
from random import shuffle
from graphviz import Digraph
from mmm_memory_ablation_pairwise_analysis import post_process, get_response, get_embedding, sentence_bleu, get_cosine_similarity, update_codebook, get_codes

root = "/Users/qianchen/Workspace/PycharmProjects/ChatDev/test_chatdev"

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
            tmp = get_codes(codebook)
            code = get_codes(codebook).replace(task_prompt, "")
            fingerprint = "{}".format(hashlib.md5(code.encode(encoding='UTF-8')).hexdigest())
            fingerprints.append(fingerprint)
            codelines.append(len(code.split("\n")))

            prompt = """{codes}\n\nProvide a sentence that describes the key functionality of the above code. For example: \"An action game where the player must eliminate a wave of incoming enemy forces using their shooting skills\" or \"Monster Mayhem is an action game where players take on the role of a fearless monster hunter tasked with eliminating hordes of terrifying creatures\".""".replace(
                "{codes}", code)
            back_instruction = post_process(get_response(prompt)).replace("\t", " ").replace("\n", " ").replace("  ", " ")

            task_code_alignment = get_cosine_similarity(get_embedding(task_prompt), get_embedding(code))
            task_task_alignment = get_cosine_similarity(get_embedding(task_prompt), get_embedding(back_instruction))
            bleu_score = sentence_bleu([task_prompt.split(" ")], back_instruction.split(" "))
            task_code_alignments.append(task_code_alignment)
            task_task_alignments.append(task_task_alignment)
            bleu_scores.append(bleu_score)

        node_infos = ["mid={}\n#line={}\ntca={:.4f}\ntta={:.4f}\nttb={:.4f}".format(fingerprints[i][:4], codelines[i], task_code_alignments[i], task_task_alignments[i], bleu_scores[i]) for i in range(len(fingerprints))]
        edge_infos = ["{}\n{}".format(i, phases[i]) for i in range(len(fingerprints))]

        return fingerprints, node_infos, edge_infos

    def plot_fingerprints(fingerprints, node_infos, edge_infos, filename):
        graph = Digraph(format="png", node_attr={"shape": "circle"}, edge_attr={"arrowhead": "normal"})

        created = {}
        for i in range(len(fingerprints)):
            idd = f"{fingerprints[i]}"
            if idd in created.keys():
                continue
            graph.node(idd, "{}\n{}".format("", node_infos[i]))
            created[idd] = True

        for i in range(len(edge_infos)-1):
            graph.edge(f"{fingerprints[i]}", f"{fingerprints[i+1]}", f"{edge_infos[i+1]}")

        graph.view(directory="./pngs", filename="pointwise_{}".format(filename))
        # graph.render(directory="./pngs", filename="pointwise_{}".format(filename))

    filename = os.path.basename(directory)
    filepath = os.path.join(root, "..", "make_task", "pngs", f"pointwise_{filename}")
    if os.path.exists(filepath):
        print(f"{filename} cached.")
        return

    fingerprints, node_infos, edge_infos = get_fingerprints(directory)
    plot_fingerprints(fingerprints, node_infos, edge_infos, os.path.basename(directory))

directories = []
for directory in os.listdir(root):
    if "_NewFeature_" not in directory:
        directories.append(os.path.join(root, directory))
directories = sorted(directories)
shuffle(directories)
print("len(directories):", len(directories))
for i,directory in enumerate(directories):
    generate_state_transition_graph(directory)
    print(i)
    # break
    if i>=10:
        break
