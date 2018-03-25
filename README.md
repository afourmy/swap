[![Build Status](https://travis-ci.org/afourmy/SWAP.svg?branch=master)](https://travis-ci.org/afourmy/SWAP)
[![Coverage Status](https://coveralls.io/repos/github/afourmy/SWAP/badge.svg?branch=master)](https://coveralls.io/github/afourmy/SWAP?branch=master)

# SWAP

SWAP is a solver for the Routing and Wavelength Assignment Problem (RWA).
Two methods were implemented to solve the wavelength assignment problem:
- Linear programming (optimal solution)
- "Largest degree first" heuristic

![SWAP: Europe](readme/swap.gif)

# The Wavelength Assignment Problem

In optical networks, the Wavelength Divison Multiplexing (WDM) technology is used to increase the capacity of fibers to transmit information, by splitting a beam of light into different wavelengths, which travel simultaneously.

![Wavelength Divison Multiplexing](readme/wdm.png)

In an all-optical network, a wavelength can cross an optical switch without Optical-Electrical-Optical (OEO) conversion. While this is a step forward towards cheaper and "greener" networks, a trade-off is that there has to be an end-to-end "wavelength continuity": a wavelength stays the same from the source edge to the destination edge, and it cannot be used by different lightpaths on the same optical fiber.

The wavelength allocation problem consists in finding the minimum number of wavelengths that are required, and how to allocate them to lightpaths.

# A first example

Let's consider a situation with 5 optical switch in a line, and 5 traffic paths:
    
![Simple graph](readme/simple.png)

## Naive strategy: assign wavelengths sequentially

We will assign wavelength sequentially (in increasing order of the traffic paths indices) and always choose the smallest available wavelength index.
 
We write the n-th wavelength Ln (lambda x), and the n-th path Pn.

- L1 is assigned to P1
- We cannot reuse L1 for P2, because P1 and P2 have a link in common. Therefore, L2 is assigned to P2.
- P3 uses all four fibers: we need a new wavelength L3.
- P4 does not share any fiber with P1 or P2: we choose the smallest available wavelength index: L1.
- Finally, P5 shares fibers with P2, P3 and P4: we need to use a new wavelength L4.

With this naive strategy, **4 wavelengths** are required.


# Algorithms

## Reduction to a graph coloring problem

## "Largest degree first" heuristic

## Linear programming

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

# Credits

