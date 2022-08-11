#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Movie file decoding routines for pySciCam module
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2022 LTRAC
    @license GPL-3.0+
    @version 0.4.4
    @date 06/07/2021
    
    Please see help(pySciCam) for more information.
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/
    
    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.4.4"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018-2022 LTRAC"

# Known movie file extensions supported & tested.
movie_formats=['.mp4','.avi']

import time, os
import numpy as np
from . import image_sequence_handler

####################################################################################
def load_movie(ImageSequence,filename,frames=None,monochrome=False,dtype=None):
    t0 = time.time()
    
    try:
        import imageio
    except ImportError:
        raise ImportError("Cannot open movie: imageio not installed.")
    try:
        import tqdm
        it_fun = lambda a,b: tqdm.tqdm(range(a,b))
    except ImportError:
        print("Warning: tqdm library not installed. No progress bar!")
        it_fun = range
    
    try:
        vid = imageio.get_reader(filename,'ffmpeg')
    except ImportError:
        raise ImportError("Cannot open movie: ffmpeg not installed.")
    

    # Copy metadata of video into ImageSequence
    for k in vid.get_meta_data().keys():
        ImageSequence.__dict__[k] = vid.get_meta_data()[k]
        print('\t%s: %s' % (k,vid.get_meta_data()[k]))

    start = 0
    #end = vid.get_length() # removed in python3 implementation, was returning infinity
    end = vid.count_frames()
    # Reduce range of frames?
    if frames is not None:
        start=frames[0]
        end=frames[1]
    
    
    # Initialize array with first frame
    frame = vid.get_data(start)
    ImageSequence.mode='MOVIE'
    if dtype is None: ImageSequence.dtype=frame.dtype
    else: ImageSequence.dtype=dtype
    ImageSequence.width=frame.shape[1]
    ImageSequence.height=frame.shape[0]
    if len(frame.shape)<3: monochrome=True # Force mono mode if no colour channels
    elif monochrome:
        if dtype is None: ImageSequence.increase_dtype()
        ImageSequence.arr = np.zeros((int(end-start),int(ImageSequence.height),int(ImageSequence.width)),dtype=ImageSequence.dtype)
    else:
        ImageSequence.arr = np.zeros((end-start,height,width,3),dtype=ImageSequence.dtype)
    
    # Loop through frames, loading.
    i=0
    for framenum in it_fun(start, end):
        frame = vid.get_data(framenum)
        if monochrome and (len(frame.shape)>2):
            frame = image_sequence_handler.__make_monochromatic__(frame,ImageSequence.dtype)
        ImageSequence.arr[i,...]=frame.copy()
        i+=1
    vid.close()

    # Estimate bits per pixel
    read_nbytes = os.path.getsize(filename)
    print('Read %.1f MiB in %.1f sec' % (read_nbytes/1048576,time.time()-t0))
    ImageSequence.src_bpp = 8*read_nbytes/float(np.product(ImageSequence.arr.shape))
    return
