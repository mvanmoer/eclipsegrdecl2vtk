# Mark Van Moer
# NCSA, University of Illinois
# 20140312 - start

# Convert Eclipse format to VTK
# inputs: a grid file and a data file.
# This follows the eclipse format as described at petrofaq.org
# http://petrofaq.org/wiki/Eclipse_Input_Data

#!/usr/bin/env vtkpython

from collections import OrderedDict
import sys
from vtk import *

def ConvertGrid(gridfilename):

    # Contains expanded COORDS section.
    coords = []
        
    # Contains expanded ZCORN section which has ONLY the z-coord 
    # for the bricks. x- y-coords are derived from coords[].
    # Size should be Xdim*Ydim*Zdim*8.
    # This runs fastest in x then y but to account for faults, all
    # cells have individual corners.
    zcorn = []

    # creating an empty vtkUnstructuredGrid here so it 
    # can be filled as the scalars are read in.
    ug = vtkUnstructuredGrid()

    # various scalars
    actnum = []
    permx = []
    permy = []
    permz = []
    poro  = []
    
    gridfile = open(gridfilename)

    for line in gridfile:
        if line.startswith('--') or not line.strip():
            # skip comments and blank lines
            continue    
        elif line.startswith('PINCH'):
            SkipSection(gridfile)
        elif line.startswith('MAPUNITS'):
            SkipSection(gridfile)
        elif line.startswith('MAPAXES'):
            SkipSection(gridfile)
        elif line.startswith('GRIDUNIT'): 
            SkipSection(gridfile)
        elif line.startswith('COORDSYS'):
            SkipSection(gridfile)
        elif line.startswith('SPECGRID'):
            xdim, ydim, zdim = next(gridfile).split()[0:3]
            xdim = int(xdim)
            ydim = int(ydim)
            zdim = int(zdim)
        elif line.startswith('COORD'):
            coords = ReadSection(gridfile)
            # These are the unique xs and ys
            # skip by 3 because the top and bottom grids are doubled.
            xcoords = coords[0::3]
            xcoords = list(OrderedDict.fromkeys(xcoords))
            ycoords = coords[1::3]
            ycoords = list(OrderedDict.fromkeys(ycoords))
        elif line.startswith('ZCORN'):
            zcorn = ReadSection(gridfile)
            ug = CreateVTKCells(ug, xdim, ydim, zdim)
            ug.SetPoints(CreateVTKPoints(xcoords, ycoords, zcorn))

        elif line.startswith('ACTNUM'):
            ug = ReadScalarSection('ACTNUM', gridfile, ug)
        elif line.startswith('EQLNUM'):
            ug = ReadScalarSection('EQLNUM', gridfile, ug)
        elif line.startswith('SATNUM'):
            ug = ReadScalarSection('SATNUM', gridfile, ug)
        elif line.startswith('FIPNUM'):
            ug = ReadScalarSection('FIPNUM', gridfile, ug)
        elif line.startswith('PERMX'):
            ug = ReadScalarSection('PERMX', gridfile, ug)   
        elif line.startswith('PERMY'):
            ug = ReadScalarSection('PERMY', gridfile, ug)
        elif line.startswith('PERMZ'):
            ug = ReadScalarSection('PERMZ', gridfile, ug)   
        elif line.startswith('PORO'):
            ug = ReadScalarSection('PORO', gridfile, ug)    
        else:
            print "else section: ", line[:8]

    gridfile.close()

    return ug

def WriteUGrid(ug, n):
    legacyWriter = vtkUnstructuredGridWriter()
    legacyWriter.SetFileName(n + '.vtk')
    legacyWriter.SetInputData(ug)
    legacyWriter.Write()

    xmlWriter = vtkXMLUnstructuredGridWriter()
    xmlWriter.SetFileName(n + '.vtu')
    xmlWriter.SetInputData(ug)
    xmlWriter.Write()

def CreateVTKArray(n,a):
    '''Create a VTK array from a Python list. Doesn't appear to be a
       method that takes a list directly.'''
    fa = vtkFloatArray()
    fa.SetName(n)
    fa.SetNumberOfComponents(1)
    for i in a:
        fa.InsertNextTuple1(i)
    return fa

def CreateVTKCells(ug, xdim, ydim, zdim):
    # The index pattern for ZCORN of the zeroeth cell.
    cellZeroPattern = [0, 1, 2*xdim, 2*xdim+1, 
    4*ydim*xdim, 4*ydim*xdim+1, 4*ydim*xdim+2*xdim, 4*ydim*xdim+2*xdim+1]

    for k in range(zdim):
        for j in range(ydim):
            for i in range(xdim):
                cell = vtkHexahedron()
                pattern = [x+(2*i)+(4*j*xdim)+(8*k*xdim*ydim) for x in cellZeroPattern]
                
                # Note that VTK ordering is a winding pattern on top 
                # and bottom faces so it's not a straight translation 
                # of index order.
                cell.GetPointIds().SetId(0, pattern[0]);
                cell.GetPointIds().SetId(1, pattern[1]);
                cell.GetPointIds().SetId(2, pattern[3]);
                cell.GetPointIds().SetId(3, pattern[2]);
                cell.GetPointIds().SetId(4, pattern[4]);
                cell.GetPointIds().SetId(5, pattern[5]);
                cell.GetPointIds().SetId(6, pattern[7]);
                cell.GetPointIds().SetId(7, pattern[6]);
    
                ug.InsertNextCell(cell.GetCellType(), cell.GetPointIds())

    return ug

def CreateVTKPoints(x, y, z):
    i = 0
    j = 0
    pts = vtkPoints()
    repeatY = False
    for k in range(0,len(z)-1,2):
        p1 = [x[i], y[j], z[k]]     
        p2 = [x[i+1], y[j], z[k+1]]
        pts.InsertPoint(k, p1)
        pts.InsertPoint(k+1, p2)
        i = i + 1
        if i > len(x) - 2:
            i = 0
            if not repeatY:
                if j < len(y) - 1:
                    j = j + 1
                    repeatY = True
                    if j == len(y) - 1:
                        repeatY = False
                elif j == len(y) - 1:
                    j = 0
            else:
                repeatY = False
    return pts

def SkipSection(f):
    '''Skips over an unprocessed section.'''
    while True:
        line = next(f).rstrip()
        if line.endswith('/'):
            return  

def ReadSection(f):
    '''Reads a data section and returns an expanded array.'''
    section = []
    while True:
        line = next(f)
        if line.startswith('--'):
            continue    
        vals = ConvertTokens(line)
        section.extend(vals)
        if section[-1] == '/':  
            section.pop()
            section = map(float, section)
            break   
    return section

def ReadScalarSection(n, f, ug):
    '''Reads a section of scalars, adds them to the unstructured
    grid array.'''
    
    scalars = ReadSection(f)
    ug.GetCellData().AddArray(CreateVTKArray(n, scalars))
    
    return ug

def ConvertTokens(line):
    '''Expands tokens of the type N*data to N copies of data.'''
    values = []
    for t in line.split():
        if t.find('*') == -1:
            values.append(t)
        else:
            run = t.split('*')
            inflation = [run[1]] * int(run[0])
            values.extend(inflation)
    
    return values           

if __name__ == '__main__':
    
    ugrid = ConvertGrid(sys.argv[1])
    WriteUGrid(ugrid, sys.argv[1])
