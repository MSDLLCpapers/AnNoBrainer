#########
# Imports
#########

import os
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
from allensdk.api.queries.image_download_api import ImageDownloadApi
from allensdk.api.queries.svg_api import SvgApi
from cairosvg import svg2png
from fastai.core import parallel
from imantics import Mask
from PIL import Image

###############
# Aux functions
###############

image_api = ImageDownloadApi()
svg_api = SvgApi()

############
# Atlas info
############
# our atlas of interest has id 1
atlas_id = 1
# image_api.section_image_query(section_data_set_id) is the analogous method for section data sets
atlas_image_records = image_api.atlas_image_query(atlas_id)
# this returns a list of dictionaries. Let's convert it to a pandas dataframe
atlas_image_dataframe = pd.DataFrame(atlas_image_records)

################
# Set inputs
################
path_atlas = Path(
    "/data/atlas_allen_complete"
)
target_size = (1296, 880)

#########################
# Download images_raw_jpg
#########################
annotation = False
downsample = 3

path_jpg = path_atlas / "images_jpg"

for i, atlas_image_id in enumerate(atlas_image_dataframe.id):
    dest = path_jpg / "{}_{}.jpg".format(
        atlas_image_dataframe.data_set_id[i],
        atlas_image_dataframe.section_number[i],
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    image_api.download_atlas_image(
        atlas_image_id, dest, annotation=annotation, downsample=downsample
    )

################################
# Convert images to png format
################################

path_images = path_atlas / "images_png"
for img in os.listdir(path_jpg):
    img_path = path_jpg / img
    dest = path_images / "{}.png".format(img_path.stem)
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(img_path).convert("RGB").save(dest)

################
# Resize images
###############

# this folder is prepared manually, there are images without artifacts
path_images = path_atlas / "images"

path_images_fixed = path_atlas / "images_fixed"
for img in os.listdir(path_images):
    img = Path(img)
    img_path = path_images / img
    dest_img_name = "{}xx0_0{}".format(img.stem, img.suffix)
    dest = path_images_fixed / dest_img_name
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(img_path).convert("RGB").resize(target_size).save(dest)

####################
# Create pairing.csv
####################

path_pairing = path_atlas / "pairing.csv"

idx = []
img = []
anno = []

for i in atlas_image_dataframe.index:
    img_name = "{}_{}".format(
        atlas_image_dataframe.data_set_id[i],
        atlas_image_dataframe.section_number[i],
    )
    idx.append(i + 1)
    img.append(img_name + "xx0_0.png")
    anno.append(img_name)

pd.DataFrame({"idx": idx, "img": img, "anno": anno}).to_csv(
    str(path_pairing), index=False
)


##############
# Download svg
##############
path_svgs = path_atlas / "svg"

for i, atlas_image_id in enumerate(atlas_image_dataframe.id):
    dest = path_svgs / "{}_{}.svg".format(
        atlas_image_dataframe.data_set_id[i],
        atlas_image_dataframe.section_number[i],
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    svg_api.download_svg(atlas_image_id, file_path=dest)

###########
# Parse svg
###########


def svg_to_csv(value, index):
    el = value
    data = ET.Element(root.tag, root.attrib)
    subgroup = ET.SubElement(
        data, root[0][root_idx].tag, root[0][root_idx].attrib
    )
    ET.SubElement(subgroup, el.tag, el.attrib)
    mydata = ET.tostring(data, encoding="utf8")
    # save individual svg
    dest_svg = (
        path_anno_svg
        / svg_path.stem
        / str(
            "{}_{}".format(el.attrib["structure_id"], el.attrib["id"]) + ".svg"
        )
    )
    dest_svg.parent.mkdir(parents=True, exist_ok=True)
    myfile = open(str(dest_svg), "wb")
    myfile.write(mydata)
    myfile.close()
    # svg to png
    dest_png = (
        path_anno_png
        / svg_path.stem
        / str(
            "{}_{}".format(el.attrib["structure_id"], el.attrib["id"]) + ".png"
        )
    )
    dest_png.parent.mkdir(parents=True, exist_ok=True)
    svg2png(url=str(dest_svg), write_to=str(dest_png))
    Image.open(dest_png).convert("L").resize(target_size).save(dest_png)
    array = np.array(Image.open(dest_png))
    array[array > 0] = 255
    polygons = Mask(array).polygons()
    coord = polygons.points[0].tolist()
    coord.append(coord[0])
    # save to csv
    dest = (
        path_anno
        / svg_path.stem
        / str(
            "{}_{}".format(el.attrib["structure_id"], el.attrib["id"]) + ".csv"
        )
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(coord).to_csv(str(dest), header=False, index=False)


path_svgs = path_atlas / "svg"


path_atlas = Path(
    "/ml_data//data/atlas_allen_complete"
)
target_size = (1296, 880)

path_anno = path_atlas / "annotations"
path_anno_svg = path_atlas / "annotations_svg"
path_anno_png = path_atlas / "annotations_png"

for svg in os.listdir(path_svgs):
    print(svg)
    svg_path = path_svgs / svg
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for root_idx, root_block in enumerate(root[0]):
        elements = []
        for element in root_block:
            elements.append(element)
        warnings.filterwarnings("ignore")
        parallel(svg_to_csv, elements, max_workers=30)
