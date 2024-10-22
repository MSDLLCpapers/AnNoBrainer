FROM ubuntu:20.04

LABEL dock.schema-version="0.1"
LABEL dock.img.name="annobrainer-docker-image"
LABEL dock.img.description="Docker image for annoBrainer opensource"
LABEL dock.maintainer.name="dped-imaging"
LABEL dock.maintainer.isid="navratjo"
LABEL dock.maintainer.email="josef.navratil@msd.com"
LABEL dock.maintainer.team="Central Software Engineering"
LABEL dock.maintainer.division="Prague IT"
LABEL dock.docker.run='docker run -it -v "${STATIC_DIR_PATH}/static_data:/static_data" -v "${DATA_DIR_PATH}/Example:/input" --gpus all annobrainer:0.1 /annoBrainer/run_annobrainer.sh'

RUN apt-get update && apt-get install -yq --no-install-recommends

RUN apt-get install -yq python3.7 python3-pip git
RUN apt-get install ffmpeg libsm6 libxext6 libgl1-mesa-glx  -y

# Upgrade pip, wheel and setuptools
RUN pip3 install -U pip wheel setuptools

# Install pip packages from requirements.test.txt
ADD requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
ADD . /annoBrainer
RUN cd /annoBrainer && git clone https://github.com/airlab-unibas/airlab.git
# extract airlab library from the repo and remove the rest of the code
RUN mv /annoBrainer/airlab /annoBrainer/airlab_source && mv /annoBrainer/airlab_source/airlab /annoBrainer/airlab && rm -R /annoBrainer/airlab_source
