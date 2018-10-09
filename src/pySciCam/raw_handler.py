#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    RAW format handling routines for pySciCam module
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018 LTRAC
    @license GPL-3.0+
    @version 0.2.2
    @date 09/10/2018
    
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
__version__="0.2.2"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018 LTRAC"

# Known RAW file extensions supported
raw_formats=['.raw','.mraw','.b16','.b16dat']

# Valid values for rawtype kwarg.
raw_types = ['b16','b16dat',\
             'chronos14_mono_12bit','chronos14_mono_16bit',\
             'chronos14_color_12bit','chronos14_color_16bit',\
             'chronos14_mono_old12bit','chronos14_color_old12bit',\
             'photron_mraw_color_12bit_bayer','photron_mraw_color_12bit',\
             'photron_mraw_mono_12bit','photron_mraw_color_8bit_bayer',\
             'photron_mraw_color_8bit','photron_mraw_mono_8bit',\
             'photron_mraw_color_16bit_bayer','photron_mraw_color_16bit',\
             'photron_mraw_mono_16bit']

import numpy as np

def load_raw(ImageSequence,all_images,rawtype=None,width=None,height=None,\
             frames=None,dtype=None,b16_doubleExposure=True,start_offset=0):
    """
    Read RAW files.
    Args:
        ImageSequence: class instance to write data to
        
        all_images: list of filenames
        
        rawtype: the string rawtype specifies which reader is to be used, as the .raw extension
                 does not tell us anything about how data is stored.
                 
        width,height: specification of dimensions for raw formats which do not indicate this
                 in their header. Ignored if image encodes this.
                 
        frames: 2-tuple (start,end) to trim range of files/frames loaded
        
        dtype: Override data storage type (otherwise autodetected based on source)
        
        b16_doubleExposure: For PCO B16 images, are they double exposed (ie PIV)?
                Ignored for non-B16 formats
                
        start_offset: starting byte offset for RAW blobs (in case of unexpected header
                data or write error.) Ignored for B16, which has a header length internal
                variable.
    """
    
    if rawtype is None:
        raise ValueError("Specify RAW format. Allowed choices:\n\trawtype = %s" % raw_types)
    
    else:
        rawtype = rawtype.lower().strip()
    
    # Chronos camera formats - firmware <= 0.3 12-bit packed
    if rawtype == 'chronos14_mono_old12bit' or rawtype == 'chronos14_color_old12bit':
        print 'Chronos 12-bit RAW (Deprecated firmware <=0.3.0 packing order)'
        import chronos14_raw as ch
        if (width is None) or (height is None):
            raise ValueError("Specify height and width") # no header data
        ImageSequence.arr = ch.read_chronos_raw(all_images[0],width,height,\
                                       frames,bits_per_pixel=12,start_offset=start_offset,\
                                                     old_packing_order=1)
        ImageSequence.src_bpp = 12
        ImageSequence.dtype = ImageSequence.arr.dtype
        if 'color' in rawtype.lower():
            ImageSequence.bayerDecode(interpolation_method='DC1394_BAYER_METHOD_BILINEAR',\
                                      camera_filter='DC1394_COLOR_FILTER_GBRG')

    # Chronos camera formats - firmware >= 0.3.1 12-bit packed
    elif rawtype == 'chronos14_mono_12bit' or rawtype == 'chronos14_color_12bit':
        print 'Chronos 12-bit RAW'
        import chronos14_raw as ch
        if (width is None) or (height is None):
            raise ValueError("Specify height and width") # no header data
        ImageSequence.arr = ch.read_chronos_raw(all_images[0],width,height,\
                                                     frames,bits_per_pixel=12,start_offset=start_offset)
        ImageSequence.src_bpp = 12
        ImageSequence.dtype = ImageSequence.arr.dtype
        if 'color' in rawtype.lower():
            ImageSequence.bayerDecode(interpolation_method='DC1394_BAYER_METHOD_BILINEAR',\
                                      camera_filter='DC1394_COLOR_FILTER_GBRG')

    # Chronos camera formats - 16-bit padded formats
    elif rawtype == 'chronos14_mono_16bit' or rawtype == 'chronos14_color_16bit':
        print 'Chronos 16-bit RAW'
        import chronos14_raw as ch
        if (width is None) or (height is None):
            raise ValueError("Specify height and width") # no header data
        ImageSequence.arr = ch.read_chronos_raw(all_images[0],width,height,
                                       frames,bits_per_pixel=16,start_offset=start_offset)
        ImageSequence.src_bpp = 16
        ImageSequence.dtype = ImageSequence.arr.dtype
        if 'color' in rawtype.lower():
            ImageSequence.bayerDecode(interpolation_method='DC1394_BAYER_METHOD_BILINEAR',\
                                      camera_filter='DC1394_COLOR_FILTER_GBRG')

    # Photron camera MRAW formats
    elif 'photron_mraw' in rawtype:
        import photron_mraw
        
        if '8bit' in rawtype:
            print 'PFV 8-bit MRAW'
            ImageSequence.src_bpp = 8
        elif '12bit' in rawtype:
            print 'PFV 12-bit MRAW'
            ImageSequence.src_bpp = 12
        elif '16bit' in rawtype:
            print 'PFV 16-bit MRAW'
            ImageSequence.src_bpp = 16

        if 'color' in rawtype.lower() and not 'bayer' in rawtype.lower(): rgbmode=1
        else: rgbmode=0

        ImageSequence.arr = photron_mraw.read_mraw(all_images[0],width,height,rgbmode,\
                                       frames,bits_per_pixel=ImageSequence.src_bpp,\
                                       start_offset=start_offset)

        if 'bayer' in rawtype.lower():
            ImageSequence.bayerDecode(interpolation_method='DC1394_BAYER_METHOD_SIMPLE',\
                                      camera_filter='DC1394_COLOR_FILTER_GRBG')

    # PCO B16 formats
    elif rawtype == 'b16' or rawtype == 'b16dat':
        import b16_raw
        
        if len(all_images) == 1:
            print 'b16 / b16dat format (single file)'
            ImageSequence.arr = b16_raw.b16_reader(all_images[0],b16_doubleExposure)
        
        else:
            print 'b16 / b16dat format (multiple files)'
            if frames is None: image_subset=all_images
            else:
                try:
                    image_subset = all_images[frames[0]:frames[1]]
                except IndexError:
                    print "Error specifying frame range for b16 sequence."
                    print "There are only %i frames available." % len(all_images)
                    print "Frames are numbered starting from zero regardless of filename!"
                    raise IndexError
        
            from joblib import Parallel, delayed
            list_of_images = Parallel(n_jobs=ImageSequence.IO_threads,verbose=ImageSequence.Joblib_Verbosity)(delayed(b16_raw.b16_reader)(filename,b16_doubleExposure,quiet=1) for filename in image_subset)
            ImageSequence.arr = np.stack(list_of_images,axis=0)
            del list_of_images
        
        ImageSequence.src_bpp = 16

    # Future - add more RAW formats here.
    #
    #

    else:
        raise ValueError("Unknown RAW format `%s'. Allowed choices:\n\trawtype = %s" % (rawtype,raw_types))
    
    return
