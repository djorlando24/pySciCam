#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
    Sample script to read Chronos 1.4 RAW file and spit out 16-bit TIFFs quickly using libtiff.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2017 LTRAC
    @license GPL-3.0+
    @version 0.2.1
    @date 08/10/2018
    
    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia
    
    Code in this directory is subject to the GPL-3.0+ license, please see ../LICENSE
"""


try:
    from pySciCam import ImageSequence
    import sys, os
    from libtiff import TIFF
except ImportError as e:
    print "Missing module:",e
    exit()

if len(sys.argv)<2:
    print "Specify RAW file"
    exit()

print '-'*79

dest = os.path.splitext(sys.argv[1])[0]
prefix = os.path.basename(dest)
if not os.path.isdir(dest):
    print "Create directory",dest
    os.mkdir(dest)

if len(sys.argv)==3:
    fr = (0,int(sys.argv[2]))
elif len(sys.argv)>3:
    fr = (int(sys.argv[2]),int(sys.argv[3]))
else:
    fr=None

I = ImageSequence(sys.argv[1],rawtype='chronos14_mono_12bit',width=1280,height=1024,frames=fr)
print '-'*79

overwrite=False
for i in range(I.N):
    fn='%s/%s_%06i.tif' % (dest,prefix,i)
    if os.path.isfile(fn) and not overwrite:
        s=raw_input( "File exists! Overwrite all? ")
        if s.lower().strip() != 'y': break
        overwrite=True
    print '\t',fn
    tiff = TIFF.open(fn, mode='w')
    tiff.write_image(I.arr[i,...])
    tiff.close()

size = sum(os.path.getsize(dest+'/'+f) for f in os.listdir(dest+'/'))/(1024.**2)
print '\nDone. Destination directory size %.1f MB' % size
