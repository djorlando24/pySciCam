
#    PythonMagick installation helper notes
    author Daniel Duke <daniel.duke@monash.edu>
    copyright (c) 2021 LTRAC
    license GPL-3.0+
    version 0.4.4
    date 24/04/2024
        __   ____________    ___    ______
       / /  /_  ____ __  \  /   |  / ____/
      / /    / /   / /_/ / / /| | / /
     / /___ / /   / _, _/ / ___ |/ /_________
    /_____//_/   /_/ |__\/_/  |_|\__________/

    Laboratory for Turbulence Research in Aerospace & Combustion (LTRAC)
    Monash University, Australia

    Updated 24/04/2024 for python3.12 on macOS Sonoma

Installing PythonMagick is a bit of a pain because it's not maintained any more. But these hacks can get it to work under homebrew.

## Homebrew requirements
brew install python3 boost boost-python3 imagemagick

## Clone PythonMagick
git clone https://github.com/ImageMagick/PythonMagick

## edit line 17046 and 17458 of configure script
Update these lines to reflect your python version. For python3.12 I put:

	ax_python_lib=boost_python312

## edit line 16206 of configure script

In order to support python versions beyond python3.9 and fix an annoying little bug, change the 3 to a 4 a the end of this line so it reads:

	am_cv_python_version=`$PYTHON -c "import sys; sys.stdout.write(sys.version[:4])"`

## edit the source code slightly to hide calls to no-longer-supported functions in ImageMagick-7

Comment out line 219 of pythonmagick_src/_Image.cpp to hide this function call. It should look like:

	//        .def("roll", (void (Magick::Image::*)(const size_t, const size_t) )&Magick::Image::roll)

## Now run in terminal:
export BOOST_ROOT=/opt/homebrew/Cellar/boost/1.84.0_1 

## Configure script
It needs to use correct clang to allow openMP usage.
CPPFLAGS & LDFLAGS must be set so boost and boost-python libs can be found from homebrew.
Python directories must be set as Homebrew's setup is non conventional.

    ./configure --prefix /opt/homebrew CC=/opt/homebrew/Cellar/llvm/18.1.4/bin/clang CXX=/opt/homebrew/Cellar/llvm/18.1.4/bin/clang++ PYTHON="python3.12" CPPFLAGS="-I/opt/homebrew/Cellar/boost/1.84.0_1/include" LDFLAGS="-L/opt/homebrew/lib"

If configure works right, you can now compile (replace N with the number of cores on your system):
    
    make -jN

If there is a syntax error at linking with ld: library not found for -l-L/usr/local/Cellar/imagemagick/7.0.11-8/lib then this indicates a library has not been linked properly - probably libboost_python.  The error ought to go away if boost-python3 is properly installed & linked.

## Finally...

    make install

If make install returns errors, check your --prefix at the configure stage and ensure the script is trying to find site-packages in the right place.
