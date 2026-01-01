# DEPENDENCIES =================================================================

import json
import os
import warnings
from datetime import datetime
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file
from pathlib import Path

import annobrainer_pipeline.master_code_errors_and_warnings as mc_ew


# AUXILIARY FUNCTIONS ==========================================================
def test_existence(path):
    if not os.path.exists(path):
        raise Exception("Provided directory or file do not exist: " + path)
    return True


def test_lenth_max_path(path_input):
    path_test = str(path_input)
    if len(path_test) >= 256:
        raise Exception(
            "Path of dir of file is too large (>256) characters "
            "and windows cannot operate with such long paths."
        )


def print_current_config_file(config):
    print(json.dumps(config, indent=2))


def machine_specific_default_path():
    if os.name == "nt":
        return Path(os.environ["USERPROFILE"])
    else:
        return Path("/user/cluster/{}/".format(os.environ["USER"]))


def validate_existing_config(config):
    mc_ew.validate(config, template=mc_ew.ConfigInitInfo)

    mc_ew.validate_animal_id_mapping_table(
        table_path=config["init_info"]["animal_id_mapping_table"],
        slide_number=config["init_info"]["slide_number"],
        template=mc_ew.AnimalID,
    )

    mc_ew.validate(config, template=mc_ew.ConfigBrainsCutting)

    mc_ew.validate_compatibility_detected_brains_and_animal_id(
        config["pairing_file"],
        path_animal_id=Path(config["brains_cutting"]["base_path_output"])
        / "animal_id_grid.csv",
    )

    return None


def load_init_config(
    experiment_folder,
    config_path,
    path_model,
    atlas_path,
    animal_id_path,
    result_output_folder=None,
    gpu_id=0,
):
    """Author: Michael Mateju
    Function for preparation and loading of initial config file which is
    required to be in the experiment_folder. The initial config is created
    by either GUI or by other script. Required input from USER.
    It prints the config file at the end of the function.
    It returns the config with paths.

    Parameters
    ----------
        experiment_folder : str or Path, required
             It is the the root folder where are data from Renee saved.
        config_path : str or Path, required
            Folder where config is saved
        path_model : str or Path, required
            Path to pre-trained parameters for brain-cutting NN
        atlas_path : str or Path, required
            Path to folder with atlas
        animal_id_path : str or Path, required
            Path to mapping table between animal_id and the brains' cut
        result_output_folder : str or Path, optional
            Folder where is saved atlas used for registration and annotation
            default = experiment_folder
                        / "brains_cut"
                        / config["init_info"]["study_id"] +
                          "_" +
                          config["init_info"]["stain"] +
                          "_" +
                          config["init_info"]["slide_number"]

    Returns
    -------
        config : dict
            a dictionary of strings of paths
    """

    # LOADING CONFIGS ==============================================================
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    if len(config.keys()) > 1:
        # assume this config is already prepared
        return config
    else:
        if result_output_folder is None:
            result_output_folder = str(
                Path(experiment_folder)
                / "brains_cut"
                / str(
                    config["init_info"]["study_id"]
                    + "_"
                    + config["init_info"]["stain"]
                    + "_"
                    + config["init_info"]["slide_number"]
                )
            )

            # Do not override the older folders
            version = 2
            result_output_folder_appr = str(result_output_folder)
            while os.path.exists(result_output_folder_appr):
                result_output_folder_appr = (
                    result_output_folder + "_v" + str(version)
                )
                version += 1
            # create folder
            Path(result_output_folder_appr).mkdir(parents=True, exist_ok=False)

        config["init_info"]["animal_id_mapping_table"] = str(animal_id_path)
        config["init_info"]["path_model"] = str(path_model)
        config["init_info"]["atlas_path"] = str(atlas_path)
        config["init_info"]["result_output_folder"] = str(
            result_output_folder_appr
        )
        config["init_info"]["gpu_id"] = gpu_id

        # If side to be annotated is not provided in the code set default to the right side.
        if config["init_info"].get("side_to_annotate") is None:
            warnings.warn(
                "Side to be annotated not provided: Setting default as Right side."
            )
            config["init_info"]["side_to_annotate"] = ["R"]

        # Also, if zeiss_gray_background is not specified set default values to FALSE
        if config["init_info"].get("zeiss_gray_background") is None:
            warnings.warn(
                "Zeiss background not provided: Setting default as False."
            )
            config["init_info"]["zeiss_gray_background"] = False

        # workaround for converting string to boolean
        if config["init_info"]["zeiss_gray_background"] in ("True", "true"):
            config["init_info"]["zeiss_gray_background"] = True
        elif config["init_info"]["zeiss_gray_background"] in (
            "False",
            "false",
        ):
            config["init_info"]["zeiss_gray_background"] = False

        # Also, if landmarks not specified set default values to FALSE
        if config["init_info"].get("landmarks") is None:
            warnings.warn("Landmarks not provided: Setting default as False.")
            config["init_info"]["landmarks"] = False

        # workaround for converting string to boolean
        if config["init_info"]["landmarks"] in ("True", "true"):
            landmarks = True
        elif config["init_info"]["landmarks"] in ("False", "false"):
            landmarks = False
        else:
            landmarks = config["init_info"]["landmarks"]
        config["init_info"]["landmarks"] = landmarks

        if config["init_info"].get("part_of_code_to_run") is None:
            warnings.warn(
                "Part if code to be run not provided: Setting default as [1, 2] (Entire Code)."
            )
            config["init_info"]["part_of_code_to_run"] = [1, 2]

        # if type(config['init_info']['subset_fixed_annotations']) != dict:
        #     if config['init_info'].get('region') != None:
        #         config['init_info']['subset_fixed_annotations'] = {config['init_info']['region']:config['init_info']['subset_fixed_annotations']}

        # IF NOT LIST CONVERT TO LIST
        if type(config["init_info"]["region"]) != list:
            config["init_info"]["region"] = [(config["init_info"]["region"])]
	
        #if type(config["init_info"]["subset_fixed_annotations"][0]) != list:
        #    config["init_info"]["subset_fixed_annotations"] = [
        #        (config["init_info"]["subset_fixed_annotations"])
        #    ]
        #

	
        res = dict(
            zip(
                config["init_info"]["region"],
                [config["init_info"]["region"]],
            )
        )
        config["init_info"]["subset_fixed_annotations"] = res

        print_current_config_file(config)
        return config


def copytree(src, dst):
    """Author: Michael Mateju
    Function copy one folder to somewhere else.
    Adjusted to workaround about Windows short \"MAX_PATH\" limit (256
    characters).

    Parameters
    ----------
       src : str or Path, required
            Source path.
       dst : str or Path, required
            Destination path.


    Returns
    -------
       None
    """

    if os.name == "nt":
        destination = "\\\\?\\" + str(dst)
    else:
        destination = str(dst)

    test_existence(src)

    Path(dst).mkdir(parents=True, exist_ok=True)
    copy_tree(str(src), destination)

    return None


def copy_registration_results_into_experiment_folder(
    config_file, experiment_folder
):
    """
    Author: Petr Hrobar
    This function finishes the entire registration process.
    It copies all registration outputs into an experiment folder

    Args:
        config_file (dict): Config file used for the registration process
    """

    # copy registration results to experiment folder, workaround due to MAX_PATH issue
    copytree(
        Path(config_file["registration"]["results_path"])
        / config_file["init_info"]["slide_number"],
        Path(experiment_folder) / config_file["init_info"]["slide_number"],
    )

    # HIGH: PRINT RESUTLS ==========================================================
    output_config_filename = (
        "output_config"
        + "_"
        + config_file["init_info"]["study_id"]
        + "_"
        + config_file["init_info"]["stain"]
        + "_"
        + "-".join(config_file["init_info"]["region"])
        + "_"
        + config_file["init_info"]["slide_number"]
        + "_"
        + str(datetime.now().strftime("%Y_%m-%d_%H_%M"))
        + ".json"
    )

    final_conf = (
        Path(config_file["init_info"]["result_output_folder"])
        / output_config_filename
    )

    with open(final_conf, "w",) as final_config:
        json.dump(config_file, final_config, indent=2)

    print(f"All results have been copied. Output folder is {final_conf}")


def copyfile(src, dst):
    """Author: Michael Mateju
    Function copy one file to somewhere else.
    Adjusted to workaround about Windows short \"MAX_PATH\" limit (256
    characters).

    Parameters
    ----------
       src : str or Path, required
            Source path.
       dst : str or Path, required
            Destination path.


    Returns
    -------
       None
    """

    if os.name == "nt":
        destination = "\\\\?\\" + str(dst)
    else:
        destination = dst

    test_existence(src)

    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    copy_file(str(src), destination)

    return None
