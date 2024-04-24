#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
    Tests for pySciCam
    
    Try reading several sample file formats.
    
    @author Daniel Duke <daniel.duke@monash.edu>
    @copyright (c) 2018-2022 LTRAC
    @license GPL-3.0+
    @version 0.5
    @date 24/04/2024
    
    Department of Mechanical & Aerospace Engineering
    Monash University, Australia
    
    Code in this directory is subject to the GPL-3.0+ license, please see ../LICENSE

    IMAGES, MOVIES and BINARY GRAPHICS FILES in this directory are subject to the Creative Commons Attribution-NonCommerical 4.0 International License. In short, this means you may adapt and share copies of these images provided that they carry the same license, but that you may NOT use these images for commerical purposes. Please see: https://creativecommons.org/licenses/by-nc/4.0/
    
"""

__author__="Daniel Duke <daniel.duke@monash.edu>"
__version__="0.5"
__license__="GPL-3.0+"
__copyright__="Copyright (c) 2018-2024 D.Duke"


import pySciCam
from pySciCam.pySciCam import ImageSequence
import numpy as np
import glob
import os
import matplotlib.pyplot as plt

from run_tests import plot_arrangement


def movie_tests():
    """ Try each movie format listed by the handler and attempt to show a frame
    """

    fig=plt.figure()
    plt.subplots_adjust(wspace=0.2,hspace=0.5)
    plt.suptitle("movie format tests")
    i=1
    passed=0
    nh, nv = plot_arrangement(len(pySciCam.movie_handler.movie_formats))
    
    for movie_ext in pySciCam.movie_handler.movie_formats:
    
        print("\n*** %s MOVIE ***" % movie_ext.strip('.').upper())
        
        filename=glob.glob('*%s' % movie_ext)
        if len(filename) == 0:
            print("Test file not found")
            plt.text(0.1,0.5,"Test failed - no file found")
        else:
            filename=filename[0]
        
        try:
            
            ax=fig.add_subplot(nv,nh,i)
            plt.title(filename)
            
            # Attempt to load test data. The height and width parameters are
            # ignored when not required.
            data = ImageSequence(filename)
            
            if len(data.shape()) == 2: oneFrame = data.arr
            elif len(data.shape()) == 3: oneFrame = data.arr[0,:,:]
            elif len(data.shape()) == 4: oneFrame = data.arr[0,0,:,:]
            else: print("I don't know what to do with an array of shape %s" % data.shape)
            
            plotHandle=ax.imshow(oneFrame)
            plt.colorbar(plotHandle)
            passed += 1
        
        except IOError as e:
            print(e)
            plt.text(0.1,0.5,"Test failed - I/O error")
    
        except:
            plt.text(0.1,0.5,"Test failed")
            raise # debugging only

        i+=1
    
    return passed, i-1




#################################
if __name__=='__main__':
    """ Run the tests when the run_tests.py script is invoked from command line """
    
    # Move to test directory if in parent directory.
    cwd = os.getcwd()
    if os.path.basename(cwd)=='pySciCam': os.chdir('test')
    if os.path.basename(os.getcwd()) != 'test': raise IOError("Tests must be run from pySciCam or pySciCam/test")
    
    # Run tests.
    p2,n2 = movie_tests()
    
    print('*'*80)
    print("Passed %i of %i tests with serial I/O\nClose windows to continue\n" % (p2,n2))
    
    plt.show()


    exit()

