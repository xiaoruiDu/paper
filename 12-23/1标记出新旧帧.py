import pandas as pd
import numpy as np
import cv2
import os


ID = 0
UpDownflag = {}


#主流程
def mainthread(posepath):
    getrightorder(posepath)
    file = open(pospath)
    all_postlist = []    #所有图片的路径和坐标,每一个元素代表一张图片的信息
    while 1:
        line = file.readline()
        if not line:
            break
        else:
            poslist = []
            splitline = line.replace('\n',' ').split(',')
            picabsolutepath = splitline[0]
            picrelativepath = 'out/' + picabsolutepath.split('/')[-1].split('.')[0] + '.png'
            poslist.append(picrelativepath)
            for i in range(1,len(splitline)):
                poslist.append(splitline[i])
            all_postlist.append(poslist)

    
    
    isfirst = 0    #第一次出现边框的标记/进行初始化判定
    for i in range(len(all_postlist)):
        nbox = int(len(all_postlist[i])/4)
        if nbox != 0:
            isfirst += 1
        if isfirst == 1:
#            print('detect the head for the first time...succuessfully')
            firstdetect(all_postlist[i], 365)
        elif isfirst == 0:
#            print("up and down is not start...")
            continue
        else:
#            print("Start continuous detection...")
            isfirst += 1            
            if (i < len(all_postlist) - 1):
                newbox_list, oldbox_list = isnewBox(all_postlist[i],all_postlist[i+1],0.5)
                
                continutDrawPic(all_postlist[i+1],newbox_list,oldbox_list)
        
    
    return



#fun:读取yolo保存的原始txt信息,并保存为标准的读取格式
#posepath: yolov3保存的检测图片的结果的txt文档路径
def getrightorder(posepath):
    info = {}
    temp = {}
    with open(posepath) as file:
        while 1:
            line = file.readline()
            if not line:
                break
            else:
                splitline = line.split(',')[0].split('/')[-1].split('.')[0]
                info[splitline] = line
        temp = sorted(info)
    os.remove(posepath)
    with open(posepath,'a+') as fw:
         for i in range(1,len(temp)+1):
             i = "%06d"%i
#             print(info[str(i)])
             fw.write(info[str(i)])
            

#func:第一次检测到边框出现时,根据y_thre初步判断乘客上下行
#message:为一个列表(包含图片位置信息,和坐标信息)
#y_thre:图片的y坐标阈值,大于y_thre判断为下行,小于判断为上行
def firstdetect(message, y_thre):
    im = cv2.imread(message[0])
    nbox = int(len(message)/4)
    up_people = 0
    down_people = 0
    for i in range(nbox):
        #draw nbox
        cv2.rectangle(im,(int(message[(i*4 + 1)]),int(message[(i*4 + 2)])),(int(message[(i*4 + 3)]),int(message[(i*4 + 4)])),color = (255,255,255))
        #draw labels
        if int(message[(i+1)*4]) < y_thre:
            up_people += 1
            cv2.putText(im,'up',(int(message[(i*4 + 3)]),int(message[(i*4 + 4)])),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,255,255),1)
        else:
            down_people += 1
            cv2.putText(im,'down',(int(message[(i*4 + 3)]),int(message[(i*4 + 4)])),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,255,255),1)
    allpeople = ('ALL_NUM: %d')%nbox
    uppeopleshow = ('UP_NUM: %d')%up_people
    downpeopleshow = ('DOWN_NUM: %d')%down_people
    
    cv2.putText(im,allpeople,(540,50),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,255),1)
    cv2.putText(im,uppeopleshow,(540,100),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,255),1)
    cv2.putText(im,downpeopleshow,(540,150),cv2.FONT_HERSHEY_COMPLEX,0.5,(0,0,255),1)
    
    cv2.imshow('puttex',im)
    cv2.waitKey(100)
    return nbox
    


#fun:
def continutDrawPic(message,newbox_list,oldbox_list):
    
    im = cv2.imread(message[0])
    for i in range(len(newbox_list)):
        cv2.putText(im,'new',(int(newbox_list[i][0]),int(newbox_list[i][3])),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
    for i in range(len(oldbox_list)):
        cv2.putText(im,'old',(int(oldbox_list[i][0]),int(oldbox_list[i][3])),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)

    
    for i in range(len(newbox_list) + len(oldbox_list)):
        #draw nbox
        cv2.rectangle(im,(int(message[(i*4 + 1)]),int(message[(i*4 + 2)])),(int(message[(i*4 + 3)]),int(message[(i*4 + 4)])),color = (255,255,255))
    cv2.imshow('puttex',im)
    cv2.waitKey(100)
#    return nbox
        
    
    
    
#func:根据前一帧的框位置,判断目前帧的所有框那些是新框,那些是旧款,并做标记
#message_pre:前一帧的图片路径,位置信息列表
#message_aft: 目前帧的图片路径,框的位置信息列表
#thre_value:  用面积判定为新框的阈值0.5(表示新帧的框覆盖旧帧框面积超过一半)
def isnewBox(message_pre,message_aft,thre_value):
    nbox2 = int(len(message_aft)/4)
    nbox1 = int(len(message_pre)/4)
    newbox_list = []     #存新框
    oldbox_list = []     #存旧框
    for i in range(nbox2):
        areaMax = -1         #更新新帧中某个框与旧帧中重叠度最大的框的面积,初始为10
        maxflag = None
        boxposlist = []      #记录新帧中某个框与旧帧中重叠度最大的框的位置,内容为坐标list
        if nbox1 == 0:
            newbox_list.append(message_aft[(4*i+1):(4*i+5)])
        
        for j in range(nbox1):
            IOU_area = calculateAreaIOU(message_aft[(4*i+1):(4*i+5)],message_pre[(4*j+1):(4*j+5)])
            if IOU_area > areaMax:
                areaMax = IOU_area
                maxflag = j     #旧框中的第j个框
                boxposlist.clear()
                boxposlist = message_aft[(4*i+1):(4*i+5)]
        if areaMax == -1:
            print('前帧没框,或者后帧没框...')
            return newbox_list,oldbox_list
        box_preArea = abs(int(message_pre[(4*maxflag+1)]) - int(message_pre[(4*maxflag+3)])) * abs(int(message_pre[(4*maxflag+2)]) - int(message_pre[(4*maxflag+4)]))       
        if areaMax > box_preArea * thre_value: #若新框和旧框的IOU超过旧框面积的一半,则判定新帧中的第i个框为旧框                
            oldbox_list.append(message_aft[(4*i+1):(4*i+5)])    #旧框
        else:                                 
            newbox_list.append(message_aft[(4*i+1):(4*i+5)])    #新框
            
    return newbox_list, oldbox_list

        
       



def isoldBox(message1,message2):
    pass


def isdisappear(message1,message2):
    pass



def recordNewboxUporDown(newbox_list,thre_value):
#    for i in range(len(newbox_list)):
#        if max(newbox_list[i][1],newbox_list[i][3]) > thre_value:
#            D += 1
#            key = str(D)
#            UpDownflag(key) = 
    pass
            
    



#fun:计算两个边框重叠的面积
#box1:边框1的(x1,y1,x2,y2)
#box2:边框2的(x3,y3,x4,y4)
def calculateAreaIOU(box1,box2):
    rec_x = 0
    rec_y = 0
    box1 = [int(x) for x in box1]
    box2 = [int(x) for x in box2]
    box_x = [box1[0],box1[2],box2[0],box2[2]] #边框x的list 为了sorted()
    box_y = [box2[1],box2[3],box2[1],box2[3]] #边框y的list 为了sorted()
    
    linelength_x = max(box1[0],box1[2],box2[0],box2[2]) - min(box1[0],box1[2],box2[0],box2[2]) 
    linelength_y = max(box1[1],box1[3],box2[1],box2[3]) - min(box1[1],box1[3],box2[1],box2[3])
    lineaddlength_x = max(box1[0],box1[2]) - min(box1[0],box1[2]) + (max(box2[0],box2[2]) - min(box2[0],box2[2]))
    lineaddlength_y = max(box1[1],box1[3]) - min(box1[1],box1[3]) + (max(box2[1],box2[3]) - min(box2[1],box2[3]))
    
    if linelength_x >= lineaddlength_x or linelength_y >= lineaddlength_y:
        return 0
    else:
        x_list = sorted(box_x)
        rec_x = x_list[2] - x_list[1]
        y_list = sorted(box_y)
        rec_y = y_list[2] - y_list[1]
#        print('box_IOU:',rec_x*rec_y)
        return rec_x * rec_y

    

    


if __name__ == '__main__':
    pospath = 'objpose/objpose.txt'
    a = mainthread(pospath)
#    getrightorder(pospath)
#    print(a)