#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Python wrapper for the DC1394 Bayer Decoding library
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.3
    @date 08/04/2018
    
    Please see help(pySciCam) for more information.
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/
    
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.1.1"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018 LTRAC"

import site, itertools, glob
import numpy as np

dc1394bayer_methods = ['DC1394_BAYER_METHOD_NEAREST', 'DC1394_BAYER_METHOD_SIMPLE',
                       'DC1394_BAYER_METHOD_BILINEAR', 'DC1394_BAYER_METHOD_HQLINEAR',
                       'DC1394_BAYER_METHOD_DOWNSAMPLE', 'DC1394_BAYER_METHOD_EDGESENSE',
                       'DC1394_BAYER_METHOD_VNG', 'DC1394_BAYER_METHOD_AHD']
    
dc1394color_filters = ['DC1394_COLOR_FILTER_RGGB','DC1394_COLOR_FILTER_GBRG',
                       'DC1394_COLOR_FILTER_GRBG','DC1394_COLOR_FILTER_BGGR']

# Import required ctypes
from ctypes import cdll, c_uint, c_uint8, c_uint16, c_uint32, POINTER

##########################################################################################
# internal Parallel wrapper to bayer-decode a some frames.
# arguments are defined in fbayerDecode.
def __libbayer_wrapper__(frames,s,enum_tile,enum_method,bits,C_UINT_T,out_nx,out_ny,libpath):

    # Load library in this thread
    libbayer = cdll.LoadLibrary(libpath)
    
    # allocate memory for output frame and make pointer to it
    frame_out = np.zeros((3*out_nx*out_ny),dtype=frames.dtype)
    rgb_out = frame_out.ctypes.data_as(POINTER(C_UINT_T * (3 * s[1] * s[2])))
    
    # determine which function to run (can't pickle a function and send thru Joblib!)
    if C_UINT_T is c_uint16: func = libbayer.dc1394_bayer_decoding_16bit
    elif C_UINT_T is c_uint8: func = libbayer.dc1394_bayer_decoding_8bit
    else: raise ValueError("Unhandled dtype "+str(arr.dtype)+" for bayer decode")
    
    # make ctypes for sx, sy
    sx = c_uint32(s[1])
    sy = c_uint32(s[2])
    
    # decode one frame
    if len(frames.shape)==2:
        # allocate memory for input frame and make pointer to it
        frame_in = np.asfortranarray(frames)
        bayer_in = frame_in.ctypes.data_as(POINTER(C_UINT_T * (s[1] * s[2])))
        # run decode
        flag = func(bayer_in, rgb_out, sx, sy, enum_tile, enum_method, bits)
        if flag != 0: raise ValueError("Bayer decode error %i" % flag)
        # return array re-ordered to channel,x,y for pySciCam.ImageSequence
        return np.moveaxis( frame_out.reshape(out_ny,out_nx,3) , [0,1,2], [2,1,0] )

    # decode several frames
    elif len(frames.shape)==3:
        frames_out = np.zeros((frames.shape[0],3,out_nx,out_ny),dtype=frames.dtype)
        for i in range(frames.shape[0]):
            # allocate memory for input frame and make pointer to it
            frame_in = np.asfortranarray(frames[i,...])
            bayer_in = frame_in.ctypes.data_as(POINTER(C_UINT_T * (s[1] * s[2])))
            
            # run decode
            flag = func(bayer_in, rgb_out, sx, sy, enum_tile, enum_method, bits)
            if flag != 0: raise ValueError("Bayer decode error %i" % flag)

            # write array re-ordered to channel,x,y for pySciCam.ImageSequence
            frames_out[i,...] = np.moveaxis( frame_out.reshape(out_ny,out_nx,3) , [0,1,2], [2,1,0] )

        return frames_out

    else: raise IndexError("Not sure how to handle input of shape "+str(frames.shape))


##########################################################################################
""" Wrapper for DC1394 Bayer decoding C library.
    user must choose the interpolation method (see bayer_decode.dc1394bayer_methods)
    and the color filter for the camera (see bayer_decode.dc1394color_filters).
    Parallel decoding of multiple frames is supported by settings ncpus>1.
    frame_chunk_size argument will give each processor a serial loop of that many
    frames to work on. Larger numbers may be better for low resolution images.
"""
def fbayerDecode(arr, interpolation_method='DC1394_BAYER_METHOD_NEAREST',\
                 camera_filter='DC1394_COLOR_FILTER_RGGB',\
                 ncpus=1,JobLib_Verbosity=5,frame_chunk_size=4):

    # find libbayer (should be built as extension by setuptools)
    for libext in ['so','dylib','dll','a']:
        path_to_libbayer = list(itertools.chain.from_iterable([ glob.glob(p+'/libbayer.'+libext)\
                                for p in site.getsitepackages() ]))
        if len(path_to_libbayer)>0: break
    if len(path_to_libbayer)==0: raise IOError("Can't find libbayer.so, bayer decode aborted")
    
    # validate method and tile choices
    if not interpolation_method.upper() in dc1394bayer_methods:
        raise ValueError('Invalid bayer decoding method. Options are: '+str(dc1394bayer_methods))
    else:
        enum_method = c_uint(dc1394bayer_methods.index(interpolation_method.upper()))

    if not camera_filter.upper() in dc1394color_filters:
        raise ValueError('Invalid color filter. Options are: '+str(dc1394color_filters))
    else:
        enum_tile = c_uint(dc1394color_filters.index(camera_filter.upper()) + 512)

    print 'Bayer settings:',interpolation_method,',', camera_filter

    # Check numpy array provided
    try:
        assert isinstance(arr,np.ndarray)
        s=arr.shape
        out_nx = s[1]
        out_ny = s[2]
    except IndexError:
        raise IndexError("Image array must be at least 2D. Aborting bayer decode")

    if interpolation_method.upper() == 'DC1394_BAYER_METHOD_DOWNSAMPLE':
        out_nx /=2
        out_ny /=2

    # Settings depending on 8 or 16 bit type.
    if arr.dtype == np.uint16:
        bits = c_uint32(16)
        C_UINT_T = c_uint16
    elif arr.dtype == np.uint8:
        bits = c_uint32(8)
        C_UINT_T = c_uint8
    else:
        raise ValueError("Cannot do bayer decoding on image array with dtype "+str(arr.dtype))

    # Check if worth it to run parallel
    if s[0] < ncpus: ncpus=1

    # Run parallel over all frames
    if ncpus > 1:
        try:
            from joblib import Parallel, delayed
            # determine number of frames for each task to work on.
            # trade-off between time to slice up arrays and time saved not re-initializing the wrapper function.
            if s[0]/ncpus < frame_chunk_size: frame_chunk_size=int(s[0]/ncpus)
            if frame_chunk_size < 1: frame_chunk_size = 1
            # run parallel loop
            frame_list = Parallel(n_jobs=ncpus,verbose=JobLib_Verbosity)(delayed(__libbayer_wrapper__)(arr[i:i+frame_chunk_size,...],s,enum_tile,enum_method,bits,C_UINT_T,out_nx,out_ny,\
                 path_to_libbayer[0]) for i in range(0,s[0],frame_chunk_size))
            # repack data into 4D array
            if len(frame_list[0].shape) == 3: newarr = np.stack(frame_list,axis=0)
            elif len(frame_list[0].shape) == 4: newarr = np.vstack(frame_list)
            else: raise IndexError("output from joblib in libbayer_wrapper has wrong number of dimensions")
            del frame_list
        except ImportError:
            print 'Unable to load joblib module for parallel processing. Falling back to serial'
            ncpus=1

    # Run serially
    if ncpus <= 1:
    
        newarr = np.stack(__libbayer_wrapper__(arr,s,enum_tile,enum_method,bits,C_UINT_T,out_nx,out_ny,\
                                               path_to_libbayer[0]),axis=0)

    return newarr

