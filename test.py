#!/usr/bin/env python

zdim = 10
ydim = 5
xdim = 5

cellZeroPattern = [0, 1, 2*xdim, 2*xdim+1, 2*ydim*2*xdim, 2*ydim*2*xdim+1, 2*ydim*2*xdim+2*xdim, 2*ydim*2*xdim+2*xdim+1]

for k in range(zdim):
	for j in range(ydim):
		for i in range(xdim):
			print [x + (2*i) + (4*j*xdim) + (8*k*xdim*ydim) for x in cellZeroPattern]

