FROM gitpod/workspace-python-3.8
FROM continuumio/miniconda3
RUN apt-get update && apt-get install make
RUN conda init bash
