#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Tests for pySciCam - Chronos part ROI
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.2
    @date 08/04/2018
    
    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    
    Code in this directory is subject to the GPL-3.0+ license, please see ../LICENSE

    IMAGES, MOVIES and BINARY GRAPHICS FILES in this directory are subject to the Creative Commons Attribution-NonCommerical 4.0 International License. In short, this means you may adapt and share copies of these images provided that they carry the same license, but that you may NOT use these images for commerical purposes. Please see: https://creativecommons.org/licenses/by-nc/4.0/
    
"""

import pySciCam
import numpy as np
import glob
import os
import matplotlib.pyplot as plt

# Determine how to arrange plots semi-neatly
def plot_arrangement(n):
    nh = int(np.sqrt(n))
    nv = int(np.ceil(n/float(nh)))
    return nh,nv

filename = 'chronos14_mono_12bit_336x96 12db 38550fps 100f 12bp.raw'
rawtype = 'chronos14_mono_12bit_noheader'
#height = 96; width = 336
width = 1280/2; height = 3225600/width
data = pySciCam.ImageSequence(filename,rawtype=rawtype,\
                              height=height,width=width)

N=1
start=0
stride=1
fig=plt.figure(figsize=(12,8))
nh, nv = plot_arrangement(N)
j=1
for i in range(N):
    if start + i*stride < data.shape()[0]:
        ax=fig.add_subplot(nh,nv,j)
        ax.imshow(data.arr[start + i*stride,...])
        plt.title('%i' % (start + i*stride))
        j+=1

plt.show()
