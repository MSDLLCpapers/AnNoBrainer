# DEPENDENCIES =================================================================

import os
from pathlib import Path
import pandas as pd


# ENVIROMENT ===================================================================
SHARED_DATA_PATH = \
    Path(os.environ["USERPROFILE"]) \
        / "Merck Sharp & Dohme, Corp" \
        / "IT Global Data Science - 2020-DigitalPathologyDS-MRL" \
        / "data"

ANNOTAION_PATH = SHARED_DATA_PATH / "annotations_to_parse"

BRAINS_CUT_PATH = SHARED_DATA_PATH / "brains_cut"

IMAGE_SIZE = {"X" : 1400,
              "Y" : 900}

# PROCESS ALL CSV FILES ========================================================
files_to_parse = os.listdir(ANNOTAION_PATH)

for file in files_to_parse:

    pairing_csv_df = []

    # pairing_csv_df = {idx = numeric(),
    #                   img = character(),
    #                   anno = character()}

    pairing_index = 1

    loaded_csv = pd.read_csv(
        ANNOTAION_PATH / file,
        header = None,
        names = ["X", "Y", "X3", "X4", "X5", "X6", "X7"],
        index_col = None,
    )

    study_folder_name = file.split(sep = ".")[0].replace("_", "")

    # create directory for given study
    annotations_folder = Path(BRAINS_CUT_PATH) / study_folder_name / "annotations"
    annotations_folder.mkdir(parents=True, exist_ok=True)

    loaded_csv["layer_folder_name"] = loaded_csv["X5"].apply(lambda g: "_".join(g.split("_")[2:6]))
    loaded_csv.sort_values(by="layer_folder_name")

    images_list = os.listdir(BRAINS_CUT_PATH / study_folder_name / "images")

    images_coords = pd.DataFrame(
        {
            "image_file_name": images_list,
            "coords": [(x, y) for (y, x) in
                     [image_name.split(".")[0].split("xx")[1].split("_")
                      for image_name in
                      images_list]]
         }
    )

    annot_max_min_df = loaded_csv.groupby("layer_folder_name",
                                          group_keys=False).agg(
        x_min = ("X", "min"),
        x_max = ("X", "max"),
        y_min=("Y", "min"),
        y_max=("Y", "max"),
    )

    annot_folders = sorted(loaded_csv["layer_folder_name"].unique())

    unique_x3 = loaded_csv.\
        groupby("layer_folder_name").\
        apply(lambda df: df["X3"].unique())

    for annot in annot_folders:
        layer_folder = annotations_folder / annot
        layer_folder.mkdir(parents = True, exist_ok = True)

        # Check if there are at least and at max 1 brain for annotation
        images_coords["true_flag"] =  images_coords["coords"].apply(
                lambda df: int(df[0]) <= annot_max_min_df.loc[annot]["x_min"] and
                           int(df[0]) + IMAGE_SIZE["X"] >=  annot_max_min_df.loc[annot]["x_max"] and
                           int(df[1]) <= annot_max_min_df.loc[annot]["y_min"] and
                           int(df[1]) + IMAGE_SIZE["Y"] >= annot_max_min_df.loc[annot]["y_max"]
            )

        # Check if there are at least and at max 1 brain for annotation
        if images_coords["true_flag"].sum() > 1:
            raise Exception("More then one brain for this annotation")
        elif images_coords["true_flag"].sum() == 0:
            raise Exception("No brain for this annotation")

        # creating pairing.csv dataframe - from anotations
        pairing_csv_df.append({
            "idx" : pairing_index,
            "img" : images_coords.loc[images_coords["true_flag"] == True].iloc[0]["image_file_name"],
            "anno" : annot
        })

        pairing_index += 1

        # For each unique X3 annotaion index, write separé file
        for x3 in list(unique_x3.loc[unique_x3.index == annot].iloc[0]):
            # create directory for given layer
            layer_folder = Path(BRAINS_CUT_PATH) \
                           / study_folder_name \
                           / "annotations" \
                           / annot


            layer_folder.mkdir(parents=True, exist_ok=True)

            #pos / neg annotation
            pos_affix = loaded_csv[(loaded_csv["layer_folder_name"] == annot) &
                                   (loaded_csv["X3"] == x3)]["X4"]

            if pos_affix.unique().__len__() > 1 :
                raise Exception("There are more then 1 unique positive/negative" \
                                + "indicator of annotation")
            else:
                if int(pos_affix.unique()) == 1:
                    pos_affix_str = "pos"
                else:
                    pos_affix_str = "neg"

            data_2_write = loaded_csv[(loaded_csv["layer_folder_name"] == annot) &
                                      (loaded_csv["X3"] == x3)][["X","Y"]]

           # write csv
            pd.DataFrame(data_2_write).to_csv(layer_folder \
                                                / ("file_" + str(x3) + "_" + pos_affix_str + ".csv"),
                                              index=False,
                                              header = False)

    # Add images to the pairing csv file which does not have annotation
    set_A = images_list
    set_B = list(pd.DataFrame(pairing_csv_df)["img"])
    missing_pairing_images = [i for i in set_A + set_B
                              if i not in set_A or i not in set_B]

    pairing_csv_pd_df = pd.DataFrame(pairing_csv_df)

    missing_pairing_images_df = \
        pd.DataFrame({"idx" : range(pairing_csv_pd_df["idx"].max() + 1,
                                    pairing_csv_pd_df["idx"].max() + 1 +
                                    len(missing_pairing_images)),
                      "img" : missing_pairing_images,
                      "anno" : [""] * len(missing_pairing_images)
     })

    pairing_csv_final_df = pd.concat([pairing_csv_pd_df,
                                      missing_pairing_images_df])

    pairing_csv_pd_df.to_csv(Path(BRAINS_CUT_PATH) \
                             / study_folder_name \
                             / "pairing.csv",
                             index=False)

# TAKE CARE OF FOLDERS WITHOUT ANNOTAION FILE ==================================

images_folder_list = os.listdir(BRAINS_CUT_PATH)

parsed_annotations = list(map(lambda g: g.split(".")[0].replace("_", ""),
                              files_to_parse))


missing_folders = list(set(images_folder_list) - set(parsed_annotations))

for missing_folder in missing_folders:
    # create directory for given study
    missing_annot_folder = Path(BRAINS_CUT_PATH) / missing_folder / "annotations"
    missing_annot_folder.mkdir(parents=True, exist_ok=True)

    miss_folder_images_list = os.listdir(BRAINS_CUT_PATH \
                                         / missing_folder \
                                         / "images")

    missing_folder_pairing_images_df = \
        pd.DataFrame({"idx" : range(1, len(miss_folder_images_list) + 1),
                      "img" : miss_folder_images_list,
                      "anno" : [""] * len(miss_folder_images_list)
     })

    missing_folder_pairing_images_df.to_csv(Path(BRAINS_CUT_PATH) \
                             / missing_folder \
                             / "pairing.csv",
                             index=False)