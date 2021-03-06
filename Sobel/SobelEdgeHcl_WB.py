import heterocl as hcl
from PIL import Image
import numpy as np
import math
#import os
import imageio

#================================================================================================================================================
#initialization
#================================================================================================================================================
path = "home.jpg"                                               # Your image path 
#hcl.init(init_dtype=hcl.Float())
hcl.init(init_dtype = hcl.Fixed(30, 16))
img = Image.open(path)
width, height = img.size

#================================================================================================================================================
#main function
#================================================================================================================================================
def sobelAlgo(A, B, Fx, Fy):
    def rgb_sum(x,y):
        B[x][y] = A[x][y][0] + A[x][y][1] + A[x][y][2]
    hcl.mutate(B.shape, lambda x,y: rgb_sum(x,y))
    #B = hcl.compute((height+2, width+2), lambda x,y:A[x][y][0]+A[x][y][1]+A[x][y][2], "B")
    r = hcl.reduce_axis(0, 3)
    c = hcl.reduce_axis(0, 3)
    Gx = hcl.compute((height, width), lambda y,x:hcl.sum(B[y+r, x+c]*Fx[r,c], axis = [r,c]), "Gx")
    t = hcl.reduce_axis(0, 3)
    g = hcl.reduce_axis(0, 3)
    Gy = hcl.compute((height, width), lambda y,x:hcl.sum(B[y+t, x+g]*Fy[t,g], axis = [t,g]), "Gy")
    return hcl.compute((height, width), lambda y,x:(hcl.sqrt(Gx[y][x]*Gx[y][x]+Gy[y][x]*Gy[y][x])*0.05891867))

#================================================================================================================================================
#computations
#================================================================================================================================================
#placeholders
A = hcl.placeholder((height+2, width+2, 3), "A")  #input placeholder
B = hcl.placeholder((height+2, width+2), "B")  #input placeholder2
Fx = hcl.placeholder((3,3), "Fx")             #output placeholder1
Fy = hcl.placeholder((3,3), "Fy")             #output placeholder2

#build the schedule
s = hcl.create_schedule([A, B, Fx, Fy], sobelAlgo)
WB1 = s.reuse_at(B, s[sobelAlgo.Gx], sobelAlgo.Gx.axis[1], "WB1")
WB2 = s.reuse_at(B, s[sobelAlgo.Gy], sobelAlgo.Gy.axis[1], "WB2")
f = hcl.build(s)

#numpy inputs
F1 = np.array([[1, 0, -1],[2, 0, -2],[1, 0, -1]])
F2 = np.array([[1, 2, 1],[0, 0, 0],[-1, -2, -1]])
img = np.asarray(img)
img_pad = np.zeros((height+2, width+2, 3))
for x in range (0, height):
        for y in range (0, width):
                img_pad[x+1, y+1] = img[x, y]

for x in range (0, height):
        img_pad[x+1,0] = img[x,0]
        img_pad[x+1, width+1] = img[x, width-1]

for y in range (0, width):
        img_pad[0,y+1] = img[0,y]
        img_pad[height+1, y+1] = img[height-1, y]

img_pad[0,0] = img[0,0]
img_pad[height+1,0] = img[height-1, 0]
img_pad[0, width+1] = img[0, width-1]
img_pad[height+1, width+1] = img[height-1, width-1]
np_B = np.zeros((height+2, width+2))

#numpy output
np_img = np.zeros((height, width))

#hcl inputs transfer
hcl_F1 = hcl.asarray(F1)
hcl_F2 = hcl.asarray(F2)
hcl_A = hcl.asarray(img_pad)
hcl_B = hcl.asarray(np_B)

#hcl output transfer
hcl_img = hcl.asarray(np_img)

#call the function
f(hcl_A, hcl_B, hcl_F1, hcl_F2, hcl_img)

#change the type of output back to numpy array
new_img = hcl_img.asnumpy()

#define array for image
finalimg = np.zeros((height, width, 3))

RGB = 0
#assign (length, length, length) to each pixel
for x in range (0, height):
        for y in range (0, width):
                RGB += new_img[x,y]
                for z in range (0, 3):
                        finalimg[x,y,z] = new_img[x,y]
                                                                                                                                                       
#create an image with the array
imageio.imsave('home_fixed_30_16_WB.jpg', finalimg)
