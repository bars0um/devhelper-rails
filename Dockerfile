FROM python:3.11

RUN apt-get update

RUN curl -sL https://deb.nodesource.com/setup_20.x | bash -

RUN apt-get update
RUN apt-get install nodejs -y
RUN apt-get install yarn -y

RUN apt-get install ruby -y

RUN gem install bundler -v 2.3.26
RUN gem update bundler
RUN apt-get install -y ruby-dev
RUN gem install rails
Run apt-get install neovim -y
RUN apt-get install -y xdg-utils

# Set the environment variables to reduce the size of the Conda installation
ENV MINICONDA_VERSION=py39_4.12.0 \
    CONDA_DIR=/opt/conda \
    PATH=/opt/conda/bin:$PATH

# Install Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-${MINICONDA_VERSION}-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm -rf /tmp/miniconda.sh

# Update Conda
RUN conda update -y conda
Run conda init bash
RUN pip install open-interpreter
#Run conda install langchain -c conda-forge
#Run conda install sentence-transformers -c conda-forge
#Run pip install chroma -c conda-forge
Run conda install chromadb -c conda-forge
Run conda install pypdf -c conda-forge
Run pip install esprima 
Run pip install langchain-community
Run pip install sentence-transformers
Run pip install langchain
Run gem install rubocop
Run gem install rubocop-rails
Run gem install erb_lint
RUN pip install sseclient-py
