# DEPENDENCIES =================================================================
packages = c("readr", "stringr", "dplyr", "purrr", "tidyr",
             "ggplot2")
## Now load or install&load all
package.check <- lapply(
  packages,
  FUN = function(x) {
    if (!require(x, character.only = TRUE)) {
      install.packages(x, dependencies = TRUE)
      library(x, character.only = TRUE)
    }
  }
)


# ENVIROMENT ===================================================================
SHARED_DATA_PATH <- file.path(Sys.getenv("USERPROFILE"),
                              "Merck Sharp & Dohme, Corp",
                              "IT Global Data Science - 2020-DigitalPathologyDS-MRL",
                              "data")

ANNOTAION_PATH <- file.path(SHARED_DATA_PATH, 
                            "annotations_to_parse")

BRAINS_CUT_PATH <- file.path(SHARED_DATA_PATH,
                             "brains_cut")


image_size = data.frame(X = 1400, 
                        Y = 900)


# PROCESS ALL CSV FILES ========================================================
files_to_parse = list.files(ANNOTAION_PATH)


for (file in files_to_parse) {
  
  pairing_csv_df = data.frame(idx = numeric(),
                              img = character(),
                              anno = character())
  
  pairing_index = 1
  
  loaded_csv = read_csv(file.path(ANNOTAION_PATH, file), 
                        col_names = FALSE)
 
  study_folder_name = str_replace(str_split(file, "\\.")[[1]][1], 
                            pattern = "_", 
                            replacement = "")
  
  # create directory for given study
  dir.create(file.path(BRAINS_CUT_PATH, 
                       study_folder_name, 
                       "annotations"), recursive = T, showWarnings = F)


  # split by folders
  process_csv =
    loaded_csv %>%
    group_by(X5) %>%
    nest() %>%
    mutate(X5_parse = str_split(X5, "_")) %>%
    mutate(layer_folder_name = paste(X5_parse[[1]][3:5], collapse = "_")) %>%
    ungroup() %>%
    select(-X5,
           -X5_parse) %>%
    arrange(layer_folder_name)


  # PAIRING CSV CREATION ===========
  
  images_list = list.files(file.path(BRAINS_CUT_PATH,
                                     study_folder_name,
                                     "images"))
  
  
  images_coords = 
    map(images_list, 
        ~str_split(str_split(str_split(.x, 
                                       "\\.")[[1]][1], 
                             "xx")[[1]][2], 
                   "_")[[1]] %>% 
          t() %>% 
          as.data.frame()) %>% 
    reduce(bind_rows) %>% 
    mutate(Y = as.numeric(V1), 
           X = as.numeric(V2)) %>% 
    select(-V1, 
           -V2) %>% 
    bind_cols(data.frame(image_file_name = images_list)) %>% 
    select(X, Y, image_file_name)
  
  
  annot_folders = 
    process_csv %>% 
    distinct(layer_folder_name) %>% 
    arrange(layer_folder_name)

  
  for (folder_index in 1:nrow(annot_folders)) {

    annot_singl_folder = pull(annot_folders[folder_index, 1])


    dir.create(file.path(BRAINS_CUT_PATH,
                         study_folder_name,
                         "annotations",
                         annot_singl_folder),
               recursive = T, 
               showWarnings = F)

    # annotations' coordinates
    data_per_folder =
      process_csv %>%
      filter(layer_folder_name == annot_singl_folder) %>%
      select(data) %>%
      unnest()

    
    # min and max of annotation
    annot_max_min_df = 
      data.frame(x_min = data_per_folder %>% select(X1) %>% map( ~min(.x)) %>% unlist(),
                 x_max = data_per_folder %>% select(X1) %>% map( ~max(.x)) %>% unlist(),
                 y_min = data_per_folder %>% select(X2) %>% map( ~min(.x)) %>% unlist(),
                 y_max = data_per_folder %>% select(X2) %>% map( ~max(.x)) %>% unlist())
             
     
    # find brain corresponding to this folder's annotation   
    correct_img_coords = 
      images_coords %>% 
      mutate(x_min_flag = ifelse(X <= annot_max_min_df$x_min, 1, 0),
             x_max_flag = ifelse(X + image_size$X >= annot_max_min_df$x_max, 1, 0),
             y_min_flag = ifelse(Y <= annot_max_min_df$y_min, 1, 0),
             y_max_flag = ifelse(Y + image_size$Y >= annot_max_min_df$y_max, 1, 0)) %>% 
      mutate(final_flag = x_min_flag * x_max_flag * y_min_flag * y_max_flag) %>% 
      filter(final_flag == 1) %>% 
      select(X, Y, image_file_name) %>% 
      mutate(image_file_name = as.character(image_file_name))
          
    # Check if there are at least and at max 1 brain for annotation       
    if (nrow(correct_img_coords) > 1) {
      stop("There are more then 1 brain with the same annotation")
    } else if (nrow(correct_img_coords) == 0) {
      stop("No brain for annotation found")
    }        
    
    
    pairing_csv_df = 
      pairing_csv_df %>% 
      bind_rows(data.frame(idx = pairing_index,
                           img = as.character(correct_img_coords$image_file_name[1]),
                           anno = as.character(annot_singl_folder)))
    
    pairing_index = pairing_index + 1
         
    # Writting the file_X_[pos/neg].csv into correct folder
    X3_index =
      data_per_folder %>%
      distinct(X3)

    for (indx in 1:nrow(X3_index)) {
      file_anot_name = pull(X3_index[indx, 1])

      file_name = file.path(BRAINS_CUT_PATH,
                            study_folder_name,
                            "annotations",
                            annot_singl_folder,
                            paste0("file_",
                                   file_anot_name,
                                   "_",
                                   ifelse(data_per_folder %>% 
                                            filter(X3 == file_anot_name) %>% 
                                            head(1) %>% 
                                            pull(X4)  == 1,
                                          "pos",
                                          "neg"),
                                   ".csv"))

      data_per_folder %>%
        filter(X3 == file_anot_name) %>% 
        select(X1, X2) %>%
        write_csv(file_name,
                  col_names = F)

    }

  }
 
  pairing_csv_df = 
    pairing_csv_df %>% 
    bind_rows(
      data.frame(idx = seq(from = max(pairing_csv_df$idx) + 1, 
                           length.out = length(setdiff(images_list, pairing_csv_df$img))), 
                 img = setdiff(images_list, pairing_csv_df$img), 
                 anno = character(length(setdiff(images_list, pairing_csv_df$img)))))
  
  # Write down the pairing.csv file into study_folder
  write_csv(pairing_csv_df,
            file.path(BRAINS_CUT_PATH, 
                      study_folder_name, 
                      "pairing.csv"), 
            col_names = T)
}


# TAKE CARE OF FOLDERS WITHOUT ANNOTAION FILE ==================================


images_folder_list = list.files(file.path(BRAINS_CUT_PATH))


parsed_annotations = 
  files_to_parse %>% 
  map(~str_replace(str_split(.x, "\\.")[[1]][1], 
            pattern = "_", 
            replacement = "")) %>% 
  unlist()


missing_folders = setdiff(images_folder_list, parsed_annotations)

for (miss_folder_idx in 1:length(missing_folders)) {
  
  miss_folder = missing_folders[miss_folder_idx]
  
  # create directory for given study
  dir.create(file.path(BRAINS_CUT_PATH, 
                       miss_folder, 
                       "annotations"), recursive = T, showWarnings = F)
  
  images_list = list.files(file.path(BRAINS_CUT_PATH,
                                     miss_folder,
                                     "images"))
  
  pairing_csv_df = 
    data.frame(idx = seq(from = 1, 
                         length.out = length(images_list)), 
               img = images_list, 
               anno = character(length(images_list)))
  
  write_csv(pairing_csv_df,
            file.path(BRAINS_CUT_PATH, 
                      miss_folder, 
                      "pairing.csv"), 
            col_names = T)
  
}
