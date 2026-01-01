import pandas as pd
import numpy as np
import glob
import os
from skimage import io
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from imantics import Mask
from skimage.color import label2rgb
from skimage.morphology import label
from fastai.core import parallel

# Main Folder of Pictures to be flipped (png files)
Atlas_path_png = '/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/annotations_named_complete_png'

# Main Folder of Pictures to be flipped (Csv files)
Atlas_path_csv = '/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/annotations_named_complete_csv'

# Function body
Atlas_path_png = Atlas_path_png + str('/*')
Atlas_path_csv = Atlas_path_csv + str('/*')

# Set 
glob_paths = glob.glob(Atlas_path_png)
glob_paths_csv = glob.glob(Atlas_path_csv)

# Destination for proccesed Images:
ann_dest_folder = Path(
"/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/"
)
ann_dest_folder_csv = ann_dest_folder / "annotations_named_complete_csv_mirrored"
ann_dest_folder_png = ann_dest_folder / "annotations_named_complete_png_mirrored"

ann_folder = Path(
"/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/annotations_png"
)
ann_dest_folder = Path(
"/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/"
)

ann_dest_folder_csv = ann_dest_folder / "annotations_named_complete_csv"

ann_dest_folder_png = ann_dest_folder / "annotations_named_complete_png"

fixed_images_path = ann_dest_folder / 'images_fixed'

Destination_fixed_mirrored = ann_dest_folder / 'images_fixed_mirrored'

##############################################
# First part of the script - mirrors png files
##############################################

# Iterate over all folder inside the Path

def mirror_annotation_png(value, index):
    i = value
    glob_paths_i = glob.glob(f"{i}/*")
    # Iterate over all images inside all the folders
    for image in glob_paths_i:
        image_i = io.imread(image)
    # Transpose the image over y-axis
        image_i_mirrored = image_i[:, ::-1]
    # Set Final Destination and name for each image
    # Split string with image path - last 2 elements are name and file type
        splited_i = image.rsplit('/')
    # Find Folder name of each image
        folder_main_i = splited_i[-2]
    # Find Image Original Name
        fullname_i = splited_i[-1]
    # Split the name (ending of 'png' so each mirrored Image can have '_mirrored' ending)
        name_i_splited = fullname_i.rsplit('.')[0]
    # File Ending type (e.g. 'png')
        name_i_end = fullname_i.rsplit('.')[1]

        folder_i = str(ann_dest_folder_png) + '_mirrored' + '/' + str(folder_main_i)

        dest_i = str(ann_dest_folder_png) + '_mirrored' + '/' + str(folder_main_i) + '/' + str(name_i_splited) + '.' + str(name_i_end)

        # CHeck if folder alredy exists, if not let's create it.
        if os.path.exists(folder_i): 
            Image.fromarray(image_i_mirrored).save(dest_i)
        else:
            os.mkdir(folder_i)
            Image.fromarray(image_i_mirrored).save(dest_i)

# ##############################################
# # Second part of the script - mirrors csv files
# ##############################################

path_mirrored_csv = '/ml_data/debug/2020-digitalpathologyds/data/atlas_allen_complete/annotations_named_complete_csv_mirrored'

def mirror_annotation_csv(value, index):

    value = str(value)
    
    folder = value
    
    for filename in os.listdir(folder):
        
    #Load perticullar CSVcoordinates file
        file_i_path = ann_dest_folder_csv / folder / filename
        file_i = pd.read_csv(file_i_path, header = None, names = ['X', 'Y'])

        #Load The same png file to calculate the shape of image, for the mirroring
        image_i_path = Path(ann_dest_folder_png / str(folder).rsplit('/')[-1] / filename.rsplit('_')[0])
        
        image_i_path = Path(str(image_i_path) + '.png')

        # image_i_path = str(ann_dest_folder_png / folder / 
        image_i = io.imread(image_i_path)
        
        # Save the Image sizes
        Ysize = image_i.shape[0]
        Xsize = image_i.shape[1]

        # Flip The coordinates
        file_i.loc[:, 'X'] = Xsize - file_i.loc[:, 'X']

        #Get he file name - csv names
        file_i_name = str(file_i_path).rsplit('/')[-1]

        csv_final_path_i = Path(path_mirrored_csv +'/' + str(folder).rsplit('/')[-1])

        # Create the path if id does not exist
        Path(csv_final_path_i).mkdir(parents=True, exist_ok=True)

        # Save flipped csv file to same sub-folders
        file_i.to_csv(
            str(Path(csv_final_path_i / Path(file_i_name))),
             header = 0,
             index = 0)

def mirror_images_fixed():
    for image in glob.glob(f"{fixed_images_path}/*"):

        # Load one perticullar image
        image_i = io.imread(image)
        
        # Save Image name
        name = image
        name = str(name).rsplit('/')[-1]

        # Mirror it and save it
        image_i_mirorred = image_i[:, ::-1]
        
        #Save it to the new mirrored folder

        #If destination folder doesn't exist - Create it
        Path(Destination_fixed_mirrored).mkdir(parents=True, exist_ok=True)

        dest_i = Path(Destination_fixed_mirrored/name)
        Image.fromarray(image_i_mirorred).save(dest_i)

#########################################################
                # Running Both Scripts
########################################################

from fastai.core import parallel

parallel(mirror_annotation_png, glob_paths, max_workers=40)
parallel(mirror_annotation_csv, glob_paths_csv, max_workers=40)

# mirror_images_fixed()