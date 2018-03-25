[![Build Status](https://travis-ci.org/afourmy/SWAP.svg?branch=master)](https://travis-ci.org/afourmy/SWAP)
[![Coverage Status](https://coveralls.io/repos/github/afourmy/SWAP/badge.svg?branch=master)](https://coveralls.io/github/afourmy/SWAP?branch=master)

# SWAP

SWAP is a solver for the Routing and Wavelength Assignment Problem (RWA).
Two methods were implemented to solve the wavelength assignment problem:
- Linear programming (GLPK, yields an optimal solution)
- "Largest degree first" heuristic

SWAP uses **Vis.js** and **Leaflet.js** to generate a visualization of the wavelength assignment.



# The Wavelength Assignment Problem

In optical networks, the Wavelength Divison Multiplexing (WDM) technology is used to increase the capacity of fibers to transmit information, by splitting a beam of light into different wavelengths, which travel simultaneously.

![Wavelength Divison Multiplexing](readme/wdm.png)

In an all-optical network, a wavelength can cross an optical switch without Optical-Electrical-Optical (OEO) conversion. While this is a step forward towards cheaper and "greener" networks, a trade-off is that there has to be an end-to-end "wavelength continuity": a wavelength stays the same from the source edge to the destination edge, and it cannot be used by different lightpaths on the same optical fiber.

The wavelength allocation problem consists in finding the minimum number of wavelengths that are required, and how to allocate them to lightpaths. 

# Algorithms

# Similar projects you might be interested in:
    
- [A vendor-agnostic NMS for graphical network automation](https://github.com/afourmy/eNMS) 
- [A 2D/3D visualization of the Traveling Salesman Problem main heuristics](https://github.com/afourmy/pyTSP) 

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
