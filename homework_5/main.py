# hw5.py
import click

import os
import zlib
import re
from pathlib import Path

git_objects_path = os.path.join(Path.home(), '.git', 'objects')


def unzip_git_object(filename):
    with open(filename, 'rb') as f:
        data = f.read()
        return zlib.decompress(data)


def get_git_object_type(path):
    object_type = unzip_git_object(path).split()[0].decode("utf-8")
    return object_type


def get_parsed_commit(text, object_name):
    commit = {}
    decoded = text.decode("utf-8")
    match_name = re.search(r'\n(.+)\n*$', decoded)
    match_parent = re.search(r'parent (.+)\n', decoded)
    match_tree = re.search(r'tree (.+)\n', decoded)
    if match_name:
        name = match_name[1]
        if match_parent:
            commit['parent'] = match_parent[1]
        if match_tree:
            commit['tree'] = match_tree[1]
        commit['id'] = object_name
        commit['name'] = name
    return commit


def get_parsed_tree(text, object_name):
    tree = {"type": "tree", "name": object_name}
    byte = text.find(b'\x00')
    text = text[byte + 1:]
    files = []

    while len(text):
        byte = text.find(b'\x00')
        line_name = text[0:byte].decode("utf-8").split()
        text = text[byte + 1:]
        file_path = text[0:20].hex()
        file_path = os.path.join(git_objects_path, file_path[0:2], file_path[2:])
        files.append({
            "type": get_git_object_type(file_path),
            "mode": line_name[0],
            "name": line_name[1],
            "filePath": file_path
        })
        text = text[20:]
        tree["files"] = files
    return tree


def orderCommits(commits):
    orderedCommits = []

    for cm in commits:
        if not cm.get('parent'):
            orderedCommits.append(cm)
            break

    for i in range(len(commits) - 1):
        for cm in commits:
            # print(cm)
            if cm.get('parent') and orderedCommits[-1]['name'] == cm['parent']:
                orderedCommits.append(cm)
                break

    return orderedCommits


def get_nodes(commits, trees):
    nodes = []
    new_commits = []

    for commit in commits:
        new_commit = {}
        if commit.get('parent'):
            new_commit['parent'] = commit['parent']
        new_commit['name'] = commit['name']
        new_commit['nodes'] = []
        for tree in trees:
            if commit['tree'] == tree['name']:
                for node in tree['files']:
                    if node['type'] == 'tree' and node not in nodes:
                        new_commit['nodes'].append({'type': 'dir', 'name': node['name'], 'nodes': []})
                        for tempTree in trees:
                            if node['filePath'] == tempTree['name']:
                                for tempNode in tempTree['files']:
                                    if tempNode['type'] == 'tree' and tempNode not in nodes:
                                        new_commit['nodes'][-1]['nodes'].append(
                                            {'type': 'dir', 'name': tempNode['name'], 'nodes': []})
                                        for tempTree2 in trees:
                                            if tempNode['filePath'] == tempTree2['name']:
                                                for tempNode2 in tempTree2['files']:
                                                    if tempNode2['type'] == 'blob' and tempNode2 not in nodes:
                                                        new_commit['nodes'][-1]['nodes'][-1]['nodes'].append(
                                                            {'type': 'file', 'name': tempNode2['name']})
                                for tempNode in tempTree['files']:
                                    if tempNode['type'] == 'blob' and tempNode not in nodes:
                                        new_commit['nodes'][-1]['nodes'].append(
                                            {'type': 'file', 'name': tempNode['name']})
                for node in tree['files']:
                    if node['type'] == 'blob' and node not in nodes:
                        new_commit['nodes'].append({'type': 'file', 'name': node['name']})
        new_commits.append(new_commit)

    return new_commits


def get_commits(path):
    walk_git_objects = os.walk(git_objects_path)

    commits = []
    trees = []

    for root, dirs, files in walk_git_objects:
        for file in files:
            file_path = os.path.join(root, file)
            object_name = file_path.split('\\')[-2] + file_path.split('\\')[-1]
            if get_git_object_type(file_path) == "commit":
                commits.append(get_parsed_commit(unzip_git_object(file_path), object_name))
            elif get_git_object_type(file_path) == "tree":
                trees.append(get_parsed_tree(unzip_git_object(file_path), object_name))

    for external_commit in commits:
        if external_commit.get('parent'):
            for inner_commit in commits:
                if external_commit['parent'] == inner_commit['id']:
                    external_commit['parent'] = inner_commit['name']
                    break

    for commit in commits:
        commit.pop('id')

    commits = orderCommits(commits)
    nodes = get_nodes(commits, trees)
    return nodes


def form_graph(commits):
    graph = "digraph git_repo {\n"
    color_commit = "red"
    color_directory = "green"
    color_file = "blue"

    commits_counter = 0
    for commit in commits:
        graph += f'\telement_{commits_counter}[label="Commit: {commit["name"]}", color="{color_commit}", shape=cylinder, style="rounded,filled"]\n'
        commits_counter += 1
        for node in commit['nodes']:
            if node['type'] == 'file':
                graph += f'\telement_{commits_counter}[label="File: {node["name"]}", color="{color_file}", shape=component, style="rounded,filled"]\n'
                commits_counter += 1
            elif node['type'] == 'dir':
                graph += f'\telement_{commits_counter}[label="Directory: {node["name"]}", color="{color_directory}", shape=folder, style="rounded,filled"]\n'
                commits_counter += 1

                for n in node['nodes']:
                    if n['type'] == 'file':
                        graph += f'\telement_{commits_counter}[label="File: {n["name"]}", color="{color_file}", shape=component, style="rounded,filled"]\n'
                        commits_counter += 1
                    elif n['type'] == 'dir':
                        graph += f'\telement_{commits_counter}[label="Directory: {n["name"]}", color="{color_directory}", shape=folder, style="rounded,filled"]\n'
                        commits_counter += 1

                        for k in n['nodes']:
                            if k['type'] == 'file':
                                graph += f'\telement_{commits_counter}[label="File: {k["name"]}", color="{color_file}", shape=component, style="rounded,filled"]\n'
                                commits_counter += 1
                            elif k['type'] == 'dir':
                                graph += f'\telement_{commits_counter}[label="Directory: {k["name"]}", color="{color_directory}", shape=folder, style="rounded,filled"]\n'
                                commits_counter += 1
    counter = 0
    commitCounter = 0
    dirCounter = 0
    prevDirCounter = 0
    for commit in commits:
        if commit.get('parent'):
            graph += f'\telement_{commitCounter} -> element_{counter}\n'
        commitCounter = counter
        counter += 1
        for node in commit['nodes']:
            if node['type'] == 'file':
                graph += f'\telement_{commitCounter} -> element_{counter}\n'
                counter += 1
            elif node['type'] == 'dir':
                graph += f'\telement_{commitCounter} -> element_{counter}\n'
                prevDirCounter = counter
                counter += 1
                for n in node['nodes']:
                    if n['type'] == 'file':
                        graph += f'\telement_{prevDirCounter} -> element_{counter}\n'
                        counter += 1
                    elif n['type'] == 'dir':
                        graph += f'\telement_{prevDirCounter} -> element_{counter}\n'
                        dirCounter = counter
                        counter += 1
                        for k in n['nodes']:
                            graph += f'\telement_{dirCounter} -> element_{counter}\n'
                            counter += 1
    graph += "}"

    return graph


@click.command()
@click.argument('path')
def main(path):
    git_objects_path = os.path.join(path, ".git\objects")
    commits = get_commits(path)
    graph = form_graph(commits)
    print(graph)


if __name__ == "__main__":
    main()
