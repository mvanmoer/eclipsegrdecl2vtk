# Mark Van Moer
# NCSA, University of Illinois
# 20140312 - start

# Convert Eclipse format to VTK
# 2 inputs, a grid file and a data file.
# 
# This file format uses a type of primitive compression.
# E.g., a term of 500*45.0 means "repeat 45.0 500 times".
# This can appear in any section, apparently.

from collections import OrderedDict
import sys

def ReadGrid(gridfilename):

	# X dim, Y dim, Z dim	
	celldims = []

	# x0 y0 zmin x0 y0 zmax x0 y1 zmin x0 y1 zmax
	# so z, y, x, fastest, with z flipping between min and max
    # size should be Xdim+1*Ydim+1*2
	coords = []
		
	# ONLY the z-coord for the bricks.
    # size should be Xdim*Ydim*Zdim*8
	# this runs fastest in x then y
	zcorn = []

	gridfile = open(gridfilename)

	for line in gridfile:
		if line.startswith('SPECGRID'):
			celldims = next(gridfile).split()[0:3]
			celldims = map(int, celldims)
		elif line.startswith('COORDSYS'):
			# Skip for now
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

	print 'len(celldims): ', len(celldims)
	print 'len(coords):   ', len(coords)
	print 'len(zcorn):    ', len(zcorn)
	WriteArrayToFile(coords, 'coords.csv')

	# skip by 3 because the top and bottom grids are doubled.
	xcoords = coords[0::3]
	xcoords = list(OrderedDict.fromkeys(xcoords))
	print xcoords
	ycoords = coords[1::3]
	ycoords = list(OrderedDict.fromkeys(ycoords))
	print ycoords

	i = 0
	j = 0
	points = []
	for z in zcorn:
		p = [xcoords[i], ycoords[j], z]
		i = i + 1
		if i == len(xcoords):
			i = 0
			j = j + 1
			if j == len(ycoords):
				j = 0
		
		points.extend(p)

	WriteArrayToFile(points, 'points.csv')

def ConvertTokens(line):
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
