#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""
    Tests for pySciCam - Chronos part ROI
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.2.1
    @date 08/10/2018
    
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

#filename = 'chronos14_color_12bit 800x600 2073fps.raw'
#rawtype = 'chronos14_mono_12bit_noheader'
#width=800; height=600; vmax=500

#filename='chronos14_color_12bit 640x96 21k.raw'
#rawtype = 'chronos14_mono_12bit_noheader'
#width=640; height=96; vmax=75

#filename='chronos14_color_12bit 192x96 38kfps.raw'
#rawtype = 'chronos14_mono_12bit_noheader'
#width=192; height=96; vmax=None

filename = 'chronos14_mono_12bit_336x96 12db 38550fps 100f 12bp.raw'
rawtype = 'chronos14_mono_12bit_noheader'
width=336; height=96; vmax=200


data = pySciCam.ImageSequence(filename,rawtype=rawtype,\
                              height=height,width=width,\
                              start_offset=0)


## pull out frames
#newarr = np.ndarray((oframes,oheight,owidth),dtype=data.dtype)
#print 'Cast to',newarr.shape
#a=0
#for i in range(oframes):
#    #print 'frame',i
#    for j in range(oheight):
#        if (j+i*2)%31 == 0 and j>0 : a+=512
#        #if j==31 or j==62 or j==93: a+=512
#        b=a+owidth-1
#        if b>data.shape()[1]: break
#        newarr[i,j,:(b-a)] = data.arr[0,a:b,0]
#        a+=1025-width
#
#
#data.arr = newarr


N=25
if data.shape()[0] < N: N=data.shape()[0]
start=0
stride=5
fig=plt.figure(figsize=(12,8))
nh, nv = plot_arrangement(N)
j=1
for i in range(N):
    if start + i*stride < data.shape()[0]:
        ax=fig.add_subplot(nh,nv,j)
        h_=ax.imshow(data.arr[start + i*stride,...],vmax=vmax)
        plt.title('%i' % (start + i*stride))
        j+=1
plt.colorbar(h_)
plt.show()
