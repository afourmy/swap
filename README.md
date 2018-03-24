# Introduction

[![Build Status](https://travis-ci.org/afourmy/SWAP.svg?branch=master)](https://travis-ci.org/afourmy/SWAP)
[![Coverage Status](https://coveralls.io/repos/github/afourmy/SWAP/badge.svg?branch=master)](https://coveralls.io/github/afourmy/SWAP?branch=master)

# Algorithms



# Installation

### (Optional) Set up a [virtual environment](https://docs.python.org/3/library/venv.html) 

### 1. Get the code
    git clone https://github.com/afourmy/SWAP.git
    cd SWAP

### 2. Install requirements 
    pip install -r requirements.txt

### 3. Run the code
    cd swap
    python flask_app.py

### 4. Go the http://127.0.0.1:5000/

# Run SWAP in a docker container

### 1. Fetch the image on dockerhub
    docker pull afourmy/swap

### 2. Find the name of the docker image
    docker images

### 3. Run the image on port 5000
    docker run -p 5000:5000 image_name
