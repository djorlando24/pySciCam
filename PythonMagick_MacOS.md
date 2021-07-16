
#    PythonMagick installation helper notes
    author Daniel Duke <daniel.duke@monash.edu>
    copyright (c) 2021 LTRAC
    license GPL-3.0+
    version 0.4.3
    date 16/07/2021
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    Updated 16/07/2021 for python3.9 on Big Sur

## Homebrew requirements
brew install python3 boost boost-python3 imagemagick

## Clone PythonMagick
git clone https://github.com/ImageMagick/PythonMagick

## edit line 17046 and 17458 of configure script to:
	ax_python_lib=boost_python39

## Now run in terminal:
export BOOST_ROOT=/usr/local/Cellar/boost/1.76.0

## Configure script
It needs to use correct clang to allow openMP usage.
CPPFLAGS & LDFLAGS must be set so boost and boost-python libs can be found from homebrew.

    ./configure CC=/usr/local/opt/llvm/bin/clang CXX=/usr/local/opt/llvm/bin/clang++ PYTHON=python3.9 CPPFLAGS="-I/usr/local/Cellar/boost/1.76.0/include" LDFLAGS="-L/usr/local/lib"

If configure works right, then make needs nothing more than:
    
    make -j8

If there is a syntax error at linking with ld: library not found for -l-L/usr/local/Cellar/imagemagick/7.0.11-8/lib then this indicates a library has not been linked properly - probably libboost_python.  The error ought to go away if boost-python3 is properly installed & linked.

## Finally...

    make install
