# Mark Van Moer
# NCSA, University of Illinois
# 20140312 - start

# Convert Eclipse format to VTK
# inputs, a grid file and a data file.

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

	# various scalars
	permx = []
	permy = []
	permz = []
	poro  = []

	gridfile = open(gridfilename)

	for line in gridfile:
		if line.startswith('--'):
			# skip comments
			next
		elif line.startswith('SPECGRID'):
			xdim, ydim, zdim = next(gridfile).split()[0:3]
			xdim = int(xdim)
			ydim = int(ydim)
			zdim = int(zdim)
		elif line.startswith('COORDSYS'):
			# Skip, was matching against just COORD
			next
		elif line.startswith('COORD'):
			coords = ReadSection(gridfile)
		elif line.startswith('ZCORN'):
			zcorn = ReadSection(gridfile)
		# Are comments guaranteed to be the 2nd line in the following?
		elif line.startswith('PERMX'):
			# discard comment line
			next(gridfile)
			permx = ReadSection(gridfile)
		elif line.startswith('PERMY'):
			next(gridfile)
			permy = ReadSection(gridfile)
		elif line.startswith('PERMZ'):
			next(gridfile)
			permz = ReadSection(gridfile)	
		elif line.startswith('PORO'):
			next(gridfile)
			poro = ReadSection(gridfile)	
		else:
			print "skipped section"

	gridfile.close()

	# These are the unique xs and ys
	# skip by 3 because the top and bottom grids are doubled.
	xcoords = coords[0::3]
	xcoords = list(OrderedDict.fromkeys(xcoords))
	ycoords = coords[1::3]
	ycoords = list(OrderedDict.fromkeys(ycoords))
	
	ugrid = vtkUnstructuredGrid()
	ugrid = CreateVTKCells(ugrid, xdim, ydim, zdim)
	ugrid.SetPoints(CreateVTKPoints(xcoords, ycoords, zcorn))

	ugrid.GetCellData().AddArray(CreateVTKArray('PERMX', permx))
	ugrid.GetCellData().AddArray(CreateVTKArray('PERMY', permy))
	ugrid.GetCellData().AddArray(CreateVTKArray('PERMZ', permz))
	ugrid.GetCellData().AddArray(CreateVTKArray('PORO', poro))

	legacyWriter = vtkUnstructuredGridWriter()
	legacyWriter.SetFileName(gridfilename + '.vtk')
	legacyWriter.SetInputData(ugrid)
	legacyWriter.Write()

	xmlWriter = vtkXMLUnstructuredGridWriter()
	xmlWriter.SetFileName(gridfilename + '.vtu')
	xmlWriter.SetInputData(ugrid)
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

def ReadSection(f):
	'''Reads a data section. Assumes no interior comments. Returns an
	   expanded array.'''
	section = []
	while True:
		vals = ConvertTokens(next(f))
		section.extend(vals)
		if section[-1] == '/':	
			section.pop()
			section = map(float, section)
			break	
	return section

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
	
	ConvertGrid(sys.argv[1])
