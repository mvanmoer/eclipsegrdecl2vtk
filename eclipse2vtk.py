# Mark Van Moer
# NCSA, University of Illinois
# 20140312 - start

# Convert Eclipse format to VTK
# inputs, a grid file and a data file.

#!/usr/bin/env vtkpython

from collections import OrderedDict
import sys
from vtk import *

def ReadGrid(gridfilename):

	# Contains expanded COORDS section.
	coords = []
		
	# Contains expanded ZCORN section which has ONLY the z-coord 
	# for the bricks. x- y-coords are derived from coords[].
    # Size should be Xdim*Ydim*Zdim*8.
	# This runs fastest in x then y but to account for faults, all
	# cells have individual corners.
	zcorn = []

	gridfile = open(gridfilename)

	for line in gridfile:
		if line.startswith('SPECGRID'):
			xdim, ydim, zdim = next(gridfile).split()[0:3]
			xdim = int(xdim)
			ydim = int(ydim)
			zdim = int(zdim)
		elif line.startswith('COORDSYS'):
			# Skip, was matching against just COORD
			next
		elif line.startswith('COORD'):
			while True:
				vals = ConvertTokens(next(gridfile))
				coords.extend(vals)
				if coords[-1] == '/':
					coords.pop()
					coords = map(float, coords)
					break
		elif line.startswith('ZCORN'):
			while True:
				vals = ConvertTokens(next(gridfile))
				zcorn.extend(vals)
				if zcorn[-1] == '/':	
					zcorn.pop()
					zcorn = map(float, zcorn)
					break	

	gridfile.close()

	# These are the unique xs and ys
	# skip by 3 because the top and bottom grids are doubled.
	xcoords = coords[0::3]
	xcoords = list(OrderedDict.fromkeys(xcoords))
	print xcoords
	ycoords = coords[1::3]
	ycoords = list(OrderedDict.fromkeys(ycoords))
	print ycoords

	# This section needs serious clean up, but it works.
	# The issue is that while z's are unique, x's and y's
	# are repeated, but not always.
	i = 0
	j = 0
	pts = vtkPoints()
	repeatY = False
	for k in range(0,len(zcorn)-1,2):
		p1 = [xcoords[i], ycoords[j], zcorn[k]] 	
		p2 = [xcoords[i+1], ycoords[j], zcorn[k+1]]
		pts.InsertPoint(k, p1)
		pts.InsertPoint(k+1, p2)
		i = i + 1
		if i > len(xcoords) - 2:
			i = 0
			if not repeatY:
				if j < len(ycoords) - 1:
					j = j + 1
					repeatY = True
					if j == len(ycoords) - 1:
						repeatY = False
				elif j == len(ycoords) - 1:
					j = 0
			else:
				repeatY = False
	
	ugrid = vtkUnstructuredGrid()
	ugrid.SetPoints(pts)

	# The index pattern for ZCORN of the zeroeth cell.
	cellZeroPattern = [0, 1, 2*xdim, 2*xdim+1, 4*ydim*xdim, 4*ydim*xdim+1, 4*ydim*xdim+2*xdim, 4*ydim*xdim+2*xdim+1]

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
	
				ugrid.InsertNextCell(cell.GetCellType(), cell.GetPointIds())

	legacyWriter = vtkUnstructuredGridWriter()
	legacyWriter.SetFileName(gridfilename + '.vtk')
	legacyWriter.SetInputData(ugrid)
	legacyWriter.Write()

	xmlWriter = vtkXMLUnstructuredGridWriter()
	xmlWriter.SetFileName(gridfilename + '.vtu')
	xmlWriter.SetInputData(ugrid)
	xmlWriter.Write()

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

def WriteArrayToFile(a, name):
	flag = 0
	f = open(name, 'w')
	for e in a:
		f.write(str(e))
		flag = flag + 1
		if flag != 3:
			f.write(' ')
		else:
			f.write('\n')
			flag = 0	
	f.close()

if __name__ == '__main__':
	
	ReadGrid(sys.argv[1])
