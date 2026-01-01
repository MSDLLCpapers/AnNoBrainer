import functools
import os
import shutil
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from fastai.core import parallel
from imantics import Mask
from PIL import Image
from skimage.color import label2rgb
from skimage.measure import label
from skimage.morphology import closing, disk, remove_small_objects

path = "/data/other/brainStructureMappingTable.csv"
df = pd.read_csv(path, index_col=0)
structure_names = df.to_dict("index")

path = "/data/other/parentChildStructure.csv"
df = pd.read_csv(path)

lst = list(map(tuple, np.array(df).astype(int).astype(str)))
lst = [tuple(reversed(x)) for x in lst]
lst = lst[1:]
# Build a directed graph and a list of all names that have no parent
graph = {name: set() for tup in lst for name in tup}
has_parent = {name: False for tup in lst for name in tup}
for parent, child in lst:
    graph[parent].add(child)
    has_parent[child] = True

# All names that have absolutely no parent:
roots = [name for name, parents in has_parent.items() if not parents]


# traversal of the graph (doesn't care about duplicates and cycles)
def traverse(hierarchy, graph, names):
    for name in names:
        hierarchy[name] = traverse({}, graph, graph[name])
    return hierarchy


tree = traverse({}, graph, roots)


def paths(tree, cur=()):
    if not tree:
        yield cur
    else:
        for n, s in tree.items():
            for path in paths(s, cur + (n,)):
                yield path


leaf_paths = list(paths(tree))


def recursive_pop_start(tpl, cur=()):
    if len(tpl) == 1:
        return cur + (tpl,)
    else:
        cur = cur + (tpl,)
        tpl = tpl[1:]
        return recursive_pop_start(tpl, cur)


def recursive_pop_end(tpl, cur=()):
    if len(tpl) == 1:
        return cur + (tpl,)
    else:
        cur = cur + (tpl,)
        tpl = tpl[:-1]
        return recursive_pop_end(tpl, cur)


children_looking_for_parents = []
[children_looking_for_parents.extend(recursive_pop_end(a)) for a in leaf_paths]
children_looking_for_parents

d = defaultdict(lambda: set())
for x in children_looking_for_parents:
    if len(x) == 1:
        d[x[-1]].update({x[-1]})
    else:
        d[x[-1]].update(set(x))
# who_are_my_parents['children']
who_are_my_parents = dict(d)


parents_looking_for_children = []
[
    parents_looking_for_children.extend(recursive_pop_start(a))
    for a in leaf_paths
]
parents_looking_for_children

dd = defaultdict(lambda: set())
for x in parents_looking_for_children:
    if len(x) == 1:
        dd[x[0]].update({x[0]})
    else:
        dd[x[0]].update(set(x))
# who_are_my_children['parents']
who_are_my_children = dict(dd)


def load_img(path):
    return np.array(Image.open(path).convert("L"))


ann_folder = Path(
    "/ml_data//data/atlas_allen_complete/annotations_png"
)

ann_dest_folder = Path(
    "/ml_data//data/atlas_allen_complete/"
)
ann_dest_folder_csv = ann_dest_folder / "annotations_named_complete_csv"
ann_dest_folder_png = ann_dest_folder / "annotations_named_complete_png"

# if exits clean dataset folders first
for folder in [ann_dest_folder_csv, ann_dest_folder_png]:
    if os.path.exists(folder):
        shutil.rmtree(folder)


def create_and_rename(value, index):
    ann = folder_lookup[index]
    ann_list = os.listdir(ann_folder / ann)
    ann_list_id = [x.split("_")[0] for x in ann_list]
    parents = set()
    [parents.update(who_are_my_parents[ch]) for ch in ann_list_id]
    for p in parents:
        pass
        selection = list(who_are_my_children[p].intersection(set(ann_list_id)))
        selection
        indices = [i for i, x in enumerate(ann_list_id) if x in selection]
        ann_to_merge = [ann_list[i] for i in indices]
        # png part
        ann_img_stack = [load_img(ann_folder / ann / a) for a in ann_to_merge]
        ann_merged = functools.reduce(
            lambda x, y: np.maximum(x, y), ann_img_stack
        )
        ann_merged[ann_merged > 0] = 255
        ann_merged = closing(ann_merged, disk(2))
        ann_merged = label(ann_merged).astype(np.uint8)
        ann_merged = remove_small_objects(ann_merged)
        ann_merged = label(ann_merged).astype(np.uint8)
        # save png, colors represent individual annotations
        dest = (
            ann_dest_folder_png
            / ann
            / "{}.png".format(structure_names[int(p)]["acronym"])
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        ann_img = label2rgb(ann_merged, image=ann_merged, bg_label=0, alpha=1)
        ann_img = ann_img * 255
        Image.fromarray(ann_img.astype(np.uint8)).save(dest)
        # csv part
        ind_ann_list = [
            ann_merged == x for x in range(1, len(np.unique(ann_merged)))
        ]
        for idx, ind_ann in enumerate(ind_ann_list):
            pass
            polygons = Mask(ind_ann).polygons()
            coords = polygons.points
            pos_idx = np.argmax([np.sum(x) for x in coords])
            for idxx, coord in enumerate(coords):
                coord = coord.tolist()
                if idxx == pos_idx:
                    coord.append(coord[0])
                    dest = (
                        ann_dest_folder_csv
                        / ann
                        / "{}_{}_{}_pos.csv".format(
                            structure_names[int(p)]["acronym"], idx, idxx
                        )
                    )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(coord).to_csv(
                        str(dest), header=False, index=False
                    )
                else:
                    coord.append(coord[0])
                    dest = (
                        ann_dest_folder_csv
                        / ann
                        / "{}_{}_{}_neg.csv".format(
                            structure_names[int(p)]["acronym"], idx, idxx
                        )
                    )
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    pd.DataFrame(coord).to_csv(
                        str(dest), header=False, index=False
                    )


folder_lookup = os.listdir(ann_folder)
my_array = list(range(len(os.listdir(ann_folder))))
warnings.filterwarnings("ignore")
parallel(create_and_rename, my_array, max_workers=40)
