# AnNoBrainer Pipeline
## Prerequisities
## Description   
Annotation of multiple regions of interest across the whole mouse brain is an indispensable process for quantitative 
evaluation of a multitude of study endpoints in neuroscience digital pathology. Prior experience and domain expert 
knowledge are the key aspects for image annotation quality and consistency. At present, image annotation is often 
achieved manually by certified pathologists or trained technicians, limiting the total throughput of studies performed 
at neuroscience digital pathology labs. It may also mean that less rigorous, less time-consuming methods of 
histopathological assessment are employed by non-pathologists, especially for early discovery and preclinical studies. 
To address these limitations and to meet the growing demand for image analysis in a pharmaceutical setting, we 
developed AnNoBrainer, an open-source software tool that leverages deep learning, image registration, and standard 
cortical brain templates to automatically annotate individual brain regions on 2D pathology slides. Application of 
AnNoBrainer to a published set of pathology slides from transgenic mice models of synucleinopathy revealed comparable 
accuracy, increased reproducibility, and a significant reduction (~50%) in time spent on brain annotation, quality 
control and labelling compared to trained scientists in pathology. Taken together, AnNoBrainer offers a rapid, 
accurate, and reproducible automated annotation of mouse brain images that largely meets the experts’ histopathological 
assessment standards (>85% of cases) and enables high-throughput image analysis workflows in digital pathology labs.

## Getting started

### Prerequisities
* Workstation with 8-core CPU, 32GB of RAM, CUDA-ready GPU with at least 16GB VRAM
* Docker
  * Pipeline has been tested only on Ubuntu and Debian servers, but it should be possible to run it on Windows
### Clone repo
```bash
git clone git@https://github.com/MSDLLCpapers/AnNoBrainer.git
```

### Create python virtual environment, install dependencies
```bash
# go to repo and build dockerfile
Docker build . -t annobrainer:0.1
```


### (Optional) Download allen mouse brain atlas data
* The users can provide it's own reference slides, instead of using Allen Mouse Brain ones
* Before downloading data from Allen Institute, please read the license terms carefully 
here: https://alleninstitute.org/terms-of-use/, make sure that you accept these terms
* Run the download script 
```bash
docker build -t allen-downloader:latest -f Dockerfile_scrape_data .
docker run -it allen-downloader:latest
```

### prepare data for the pipeline
Create a new folder with data you want to process or use a sample file for getting familiar with the pipeline.

### Run the pipeline in docker
```bash
`docker run -it -v "${STATIC_DIR_PATH}/static_data:/static_data" -v "${DATA_DIR_PATH}/Example:/input" --gpus all annobrainer:0.1 `/annoBrainer/run_annobrainer.sh
```
