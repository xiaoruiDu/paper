#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 15:08:01 2018

@author: amie
"""
import cv2



def getprobdic(im,nbox1,nbox2,pro,color):  #大框为nbox1,大框与小框nbox2形成的环形概率为pro
    probdic = {}
    for i in range(nbox1[0],nbox1[2]):
        for j in range(nbox1[1],nbox2[1]):
            key = str(i) + str(j)
            probdic[key] = pro
            cv2.circle(im,(i,j),0,color,0)
    
    for i in range(nbox1[0],nbox1[2]):
        for j in range(nbox2[3],nbox1[3]):
            key = str(i) + str(j)
            probdic[key] = pro
            cv2.circle(im,(i,j),0,color,0)
    
    for i in range(nbox1[0],nbox2[0]):
        for j in range(nbox2[1],nbox2[3]):
            key = str(i) + str(j)
            probdic[key] = pro
            cv2.circle(im,(i,j),0,color,0)
            
    for i in range(nbox2[2],nbox1[2]):
        for j in range(nbox2[1],nbox2[3]):
            key = str(i) + str(j)
            probdic[key] = pro
            cv2.circle(im,(i,j),0,color,0)
    
#    cv2.imshow('oo1',im)
#    cv2.waitKey(100)    
        
    return probdic


def getsinggleboxpro(im,box1,pro,color):
    prodic = {}
    for i in range(box1[0],box1[2]):
        for j in range(box1[1],box1[3]):
            key = str(i) + str(j)
            prodic[key] = pro
            cv2.circle(im,(i,j),0,color,0)
    cv2.imshow('oo',im)
    cv2.waitKey(100)  
    return prodic



im = cv2.imread('orig.jpg')
#print(im.shape[0])

box = []
for i in range(5):
#    cv2.rectangle(im,(im.shape[1] - 64 * (10-i), im.shape[0] - 48 *(10-i)),(im.shape[1] - 64 * i -1, im.shape[0] - 48 *i - 1),(0,255,0),2)
    box.append( [im.shape[1] - 64 * (10-i), im.shape[0] - 48 *(10-i),im.shape[1] - 64 * i -1, im.shape[0] - 48 *i - 1])
print(box)


pro1 = getprobdic(im,box[0],box[1],90,(255,0,0))
pro2 = getprobdic(im,box[1],box[2],70,(0,255,0))
pro3 = getprobdic(im,box[2],box[3],50,(0,0,255))
pro4 = getprobdic(im,box[3],box[4],30,(100,100,255))
pro5 = getsinggleboxpro(im,box[4],10,(255,100,100))




    