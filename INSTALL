# INSTALLATION INSTRUCTIONS

pySciCam depends upon a bunch of image handling libraries to read TIFF and other formats.
Not all are mandatory - pythonMagick in particular is optional as it doesn't work on all OSes.
If you want to read 12 bit TIFFS from Photron cameras though, you'll need it.

Dependecies are mostly available through standard package repositories, but in some cases, you will need to
compile things from source code. Linux installation (in Ubuntu) is pretty straightforward. MacOS is more
tricky. I have given instructions that worked for me below. I will update them as new versions of packages
come out, and the code is updated. 

Common problems occur when you have multiple python versions on your computer, and then you build code against
the wrong version of python. Always check that the libraries are using the right python lib and include paths
and the right python3 interpreter.

## Overview of installation steps for pySciCam dependencies, in order of installation: 

### - Ensure you have a working Python setup. 
      Code currently works on Python 3.x. No longer compatible with Python 2
      You may wish to set up a development environment (I like conda)

### - Ensure you have a working C compiler (i.e. gcc) to build the extensions.

### - Install mandatory python modules using either easy_install, pip, or conda
	cython, numpy, tqdm, natsort, joblib

### - Install optional python modules to provide further compatibility/enhancement
        imageio and imageio-ffmpeg (movie formats)
        pillow (conventional image file formats)

### - If installing movie support via imageio, also need ffmpeg
      use package manager (apt, yum) in Linux or homebrew in macos
      i.e. 'apt-get install ffmpeg' or 'brew install ffmpeg' 

### - Install ImageMagick
      Use package manager (apt, yum) in Linux or use homebrew on MacOS
      (nb. Homebrew requires Xcode and the Command Line Tools). 
      On MacOS under homebrew, you will need to install using the command 'brew install imagemagick --with-python'

### - Install additional PythonMagick dependencies once ImageMagick is installed.
      We require 'boost-python3', as well as working c/c++ compilers. These can be obtained through package manager in Linux (apt, yum).
      
      On Ubuntu Linux you also need to install 'libmagickcore-dev' and 'libmagick++-dev'.
      On MacOS you also need to install 'pkg-config'.

      As of September 2020, homebrew installation on macOS works: brew install python3 boost boost-python3 imagemagick
      If you need to build your own boost-python3 see below section. Otherwise skip to installing llvm
  
###  How to set up a MacOS compiler that's OpenMP-compatible so we can build PythonMagick:
          brew install llvm   
     (or use other package manager)

### - Now time to install PythonMagick
          git clone https://github.com/ImageMagick/PythonMagick
    
    On Linux, try './configure' then check all is ok, if so 'make -j8' and 'sudo make install'.
    
    On MacOS: See the PythonMagick_MacOS.md file for details - there are a few extra steps here.

### - Check that the above modules load without errors
        cd; python3 -c 'import PythonMagick'
	You should see no error messages.
        If you have trouble, Stack Oveflow is your friend!

###  - Now go to pySciCam and run 'python setup.py install'
      n.b. if you don't have sudo permission to install the packages for the system, append the --user switch to install locally.

      The setup.py script should find the numpy cython header files automatically. If this fails you'll get the error "fatal error: 'numpy/arrayobject.h' file not found".
      On MacOS with homebrew, this is a known issue.  Run homebrew-install.sh to automatically fix it.

### - Go into 'pySciCam/test' and run 'python3 run_tests.py' to check all is working ok.
