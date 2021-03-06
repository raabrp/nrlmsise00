Python wrapper for [NRLMSISE-00](https://en.wikipedia.org/wiki/NRLMSISE-00)

# About

Wraps the C version of NRLMSISE-00 (model 2001), written by Dominik Brodowski
and based on the original FORTRAN publication by Mike Picone, Alan Hedin, and
Doug Drob.

Copies of these original sources are included for reference, obtained from:
* C-source: https://www.brodo.de/space/nrlmsise/
* Fortran source: https://ccmc.gsfc.nasa.gov/pub/modelweb/atmospheric/msis/nrlmsise00/

# Contents

```
.
├── /src_c            C source code (Dominik Brodowski)
├── /src_f            FORTRAN source code (Picone, Hedin, Drob)
├── libnrlmsise00.so  compiled from c with gcc for Windows
├── nrlmsise00.py     wraps compiled code using ctypes
├── ref_output.txt    Test values to recreate by running nrlmsise.py directly
└── readme.md         You are reading it now
```

# Requirements

If and only if you wish to allow the script to automatically query internet
resources for current space weather (10.7 cm solar flux and geomagnetic ap
index):

* [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)

This may be ignored for modeling below 80 km.

# Installation

## Windows

One *should* have to do nothing other than copy this repo (the compiled binary
should just work)...this assertion is yet untested however.

The included copy of `libnrlmsise00.so` was compiled with gcc via:

`gcc -fPIC -shared -o libnrlmsise00.so nrlmsise-00.c nrlmsise-00.h nrlmsise-00_data.c`

(where gcc installed via choco with package `mingw`)

## Linux

Navigate to `src_c` and compile the shared object file:

`gcc -Wall -g -DINLINE -fPIC -shared -o libnrlmsise00.o nrlmsise-00.c nrlmsise-00.h nrlmsise-00_data.c`

Copy the output (`libnrlmsise00.o`) to the repository root.

# Usage

Class `Atmosphere` allows for some convenience (such as using current date/time
and optionally fetching current space weather), but the most direct access to
the model is available through the function `nrlmsise00` (featuring a hefty
docstring).

Finally, the flag `ENABLE_SPACE_WEATHER` (disable by default) defined at the top
of `nrlmsise00.py` allows instantiation of `Atmosphere` to poll online resources
[NWRA](https://spawx.nwra.com/spawx/env_latest.html) for current 10.7cm solar 
flux and geomagnetic activity.

# Tests

Sample output given by the C and Fortran sources was successfully recreated.
Running `nrlmsise00.py` and comparing against `ref_output.txt` (copied from the
C source) should demonstrate this. I could not tell how the input to test 17
differed from test 16 by inspecting the c source however, so this test has been
omitted.
