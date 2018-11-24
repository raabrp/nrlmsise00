
Python wrapper for [NRLMSISE-00](https://en.wikipedia.org/wiki/NRLMSISE-00)

Uses NRLMSISE-00 (model 2001) C version, written by Dominik Brodowski - a
translation of the original publication in FORTRAN by Mike Picone, Alan Hedin,
and Doug Drob. Snapshots of both sources are included for reference.

C-source: https://www.brodo.de/space/nrlmsise/
Fortran source: https://ccmc.gsfc.nasa.gov/pub/modelweb/atmospheric/msis/nrlmsise00/

Contents:

libnrlmsise00.so  - compiled from c with gcc on Windows
nrlmsise00.py     - wraps .so using ctypes

Use:

Class `Atmosphere` allows for some convenience (such as using current date and
time), but most direct access to the model is available through the function 
`nrlmsise00`, which features a hefty docstring.

Finally, the flag `ENABLE_SPACE_WEATHER` (disable by default) defined at the top
of the file allows the instantiation of `Atmosphere` to poll online resources 
[NWRA](https://spawx.nwra.com/spawx/env_latest.html) for current 10.7cm solar 
flux and geomagnetic activity.

Notes:

on Windows, libnrlmsise00.so compiled with gcc via:

`gcc -fPIC -shared -o libnrlmsise00.so nrlmsise-00.c nrlmsise-00.h nrlmsise-00_data.c`

(gcc installed via choco with package `mingw`)

