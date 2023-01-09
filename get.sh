wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -u -p /workspace/anaconda-linter/miniconda3
eval "$(/workspace/anaconda-linter/miniconda3/bin/conda shell.bash hook)"
rm Miniconda3-latest-Linux-x86_64.sh
conda init