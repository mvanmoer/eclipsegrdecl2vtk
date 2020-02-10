# eclipsegrdecl2vtk
Convert Eclipse GRDECL to VTK

This follows the eclipse ASCII format as described at http://petrofaq.org/wiki/Eclipse_Input_Data
It assumes there are both an eclipse grid file and an eclipse data file for input.
The output is as a VTK Unstructured Grid (both legacy and XML formats), regardless of whether the input 
grid has a regular topology or not.

The supported scalars ACTNUM, EQLNUM, SATNUM, FIPNUM, PERM{X|Y|Z}, and PORO were based on the available test data. 
To add support for additional scalars, just follow the same elif structure and call to ReadScalarSection.

This script was developed against output from Petrel 2012.2. It may or may not work with grdecl files from any other source.

2020-02-10: This has been tested with VTK 8.0.1 using Python 2.7.12 and VTK 8.2.0 using Python 3.5.2.
