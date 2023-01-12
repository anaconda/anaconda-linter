FROM gitpod/workspace-python-3.8
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
bash Miniconda3-latest-Linux-x86_64.sh -b -u -p /workspace/anaconda-linter/miniconda3 && \
rm Miniconda3-latest-Linux-x86_64.sh
