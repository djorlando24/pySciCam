#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Python wrapper for the DC1394 Bayer Decoding library
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.1.2
    @date 08/04/2018
    
    Please see help(pySciCam) for more information.
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

""" Wrapper for DC1394 Bayer decoding C library.
    user must choose the interpolation method (see bayer_decode.dc1394bayer_methods)
    and the color filter for the camera (see bayer_decode.dc1394color_filters).
    Parallel decoding of multiple frames is supported.
"""
def fbayerDecode(arr, interpolation_method='DC1394_BAYER_METHOD_NEAREST',\
                 camera_filter='DC1394_COLOR_FILTER_RGGB',ncpus=1):
    
    # Import required ctypes
    from ctypes import cdll, c_uint, c_uint8, c_uint16, c_uint32, POINTER

    # load libbayer
    for libext in ['so','dylib','dll','a']:
        path_to_libbayer = list(itertools.chain.from_iterable([ glob.glob(p+'/libbayer.'+libext)\
                                for p in site.getsitepackages() ]))
        if len(path_to_libbayer)>0: break
    if len(path_to_libbayer)==0: raise IOError("Can't find libbayer.so, bayer decode aborted")
    libbayer= cdll.LoadLibrary(path_to_libbayer[0])
    
    # validate method and tile choices
    if not interpolation_method.upper() in dc1394bayer_methods:
        raise ValueError('Invalid bayer decoding method. Options are: '+str(dc1394bayer_methods))
    else:
        enum_method = c_uint(dc1394bayer_methods.index(interpolation_method.upper()))

    if not camera_filter.upper() in dc1394color_filters:
        raise ValueError('Invalid color filter. Options are: '+str(dc1394color_filters))
    else:
        enum_tile = c_uint(dc1394color_filters.index(camera_filter.upper()) + 512)

    # Check numpy array
    try:
        assert isinstance(arr,np.ndarray)
        s=arr.shape
        sx = c_uint32(s[1])
        sy = c_uint32(s[2])
        out_nx = s[1]
        out_ny = s[2]
    except IndexError:
        raise IndexError("Image array must be at least 2D. Aborting bayer decode")

    if interpolation_method.upper() == 'DC1394_BAYER_METHOD_DOWNSAMPLE':
        out_nx /=2
        out_ny /=2

    # build empty RGB array
    newarr = np.zeros((s[0],3,out_nx,out_ny),dtype=arr.dtype)

    # Settings depending on 8 or 16 bit type.
    if arr.dtype == np.uint16:
        bits = c_uint32(16)
        C_UINT_T = c_uint16
        func = libbayer.dc1394_bayer_decoding_16bit
    elif arr.dtype == np.uint8:
        bits = c_uint32(8)
        C_UINT_T = c_uint8
        func = libbayer.dc1394_bayer_decoding_8bit
    else:
        raise ValueError("Cannot do bayer decoding on image array with dtype "+str(arr.dtype))
        
    # Run serially
    if ncpu <= 1:
        frame_out = np.zeros((3*out_nx*out_ny),dtype=frame_in.dtype)
        rgb_out = frame_out.ctypes.data_as(POINTER(C_UINT_T * (3 * s[1] * s[2])))
        for i in range(s[0]):
            frame_in = np.asfortranarray(arr[i,...])
            bayer_in = frame_in.ctypes.data_as(POINTER(C_UINT_T * (s[1] * s[2])))
            flag = func(bayer_in, rgb_out, sx, sy, enum_tile, enum_method, bits)
            if flag != 0: raise ValueError("Bayer decode error %i" % flag)
            newarr[i,...] = np.moveaxis( frame_out.reshape(out_ny,out_nx,3) , [0,1,2], [2,1,0] )

    # Run parallel over all frames
    else:
        pass


    return newarr
