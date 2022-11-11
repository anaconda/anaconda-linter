FROM continuumio/miniconda3:latest

COPY . .
RUN conda update --all -y -q && conda install -y -q make
RUN make environment