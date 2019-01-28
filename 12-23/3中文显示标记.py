import pandas as pd
import numpy as np
import cv2
import os
from PIL import Image, ImageDraw, ImageFont


# %%
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


    allbox_dic = {'up':[],'down':[]}   
    for i in range(len(all_postlist)):               
        if (i < len(all_postlist) - 1):
            newbox_dic, oldbox_dic, allbox_dic = isnewBox(allbox_dic, all_postlist[i+1], 0.5, 365)
            continutDrawPic(all_postlist[i+1],allbox_dic)
    
    return



# %%

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
            
# %%
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
# %%


def detectNewBox(box,thre):
    up = 'up'
    down = 'down'
    if int(box[3]) < thre:
        return up
    else:
        return down


# %%

#fun:
def continutDrawPic(message,allbox_dic):
    
    nbox = len(allbox_dic['up']) + len(allbox_dic['down'])
    up_people = len(allbox_dic['up']) 
    down_people = len(allbox_dic['down'])
    
    allpeople = ('总人头数: %d')%nbox
    uppeopleshow = ('上行人数: %d')%up_people
    downpeopleshow = ('下行人数: %d')%down_people
    
    im = cv2.imread(message[0])   
    for key in allbox_dic:
        if key == 'up':
            for i in range(len(allbox_dic[key])):
                im = drawchinese(im,'上行',int(allbox_dic[key][i][0]),int(allbox_dic[key][i][3]),[0,201,255])
#                cv2.putText(im,key,(int(allbox_dic[key][i][0]),int(allbox_dic[key][i][3])),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
                
        elif key == 'down':
            for i in range(len(allbox_dic[key])):
                im = drawchinese(im,'下行',int(allbox_dic[key][i][0]),int(allbox_dic[key][i][3]),[0,201,255])
#                cv2.putText(im,key,(int(allbox_dic[key][i][0]),int(allbox_dic[key][i][3])),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
   
    im = drawchinese(im,allpeople,500,20,[255,201,0])
    im = drawchinese(im,uppeopleshow,500,50,[255,201,0])
    im = drawchinese(im,downpeopleshow,500,80,[255,201,0])
#    cv2.putText(im,allpeople,(500,50),cv2.FONT_HERSHEY_COMPLEX,0.5,(87,201,0),2)
#    cv2.putText(im,uppeopleshow,(500,100),cv2.FONT_HERSHEY_COMPLEX,0.5,(87,201,0),2)
#    cv2.putText(im,downpeopleshow,(500,150),cv2.FONT_HERSHEY_COMPLEX,0.5,(87,201,0),2)
    
    cv2.imshow('puttex',im)
    cv2.waitKey(500)
#    return nbox
        
# %%    
    
#func:根据前一帧的框位置,判断目前帧的所有框那些是新框,那些是旧款,并做标记
#message_pre: 位置信息字典{'up':[[],[],..],'down':[[],[],...]}
#message_aft: 目前帧的图片路径,框的位置信息列表
#thre_value:  用面积判定为新框的阈值0.5(表示新帧的框覆盖旧帧框面积超过一半)
#new_boxthre: 对于新框判定上下行的阈值(ex:y值大于365为down,小于为up)
def isnewBox(message_pre_dic,message_aft,thre_value,new_boxthre):
    
    nbox2 = int(len(message_aft)/4)    #目前帧的框个数
    nbox1 = int(len(message_pre_dic['up']) + len(message_pre_dic['down'])) #前一帧的框个数
    print('nbox2:',nbox2)
    print('nbox1:',nbox1)
    newbox_dic = {'up':[],'down':[]}  #存新框(新上+新下)
    oldbox_dic = {'up':[],'down':[]}  #存旧框(旧上+旧下)
    allbox_dic = {'up':[],'down':[]}  #存所有框(上+下)
    
    if nbox2 == 0:
        return newbox_dic,oldbox_dic,allbox_dic 
    
    if nbox1 == 0:        #如果前一帧没有框,那么此帧全为新框.
        for i in range(nbox2):
            upDown = detectNewBox(message_aft[(4*i+1):(4*i+5)],new_boxthre)
            print('upDown',upDown)
            newbox_dic[upDown].append(message_aft[(4*i+1):(4*i+5)])
            
        for key in oldbox_dic:
            for c in range(len(oldbox_dic[key])):
                allbox_dic[key].append(oldbox_dic[key][c])
                
        for key in newbox_dic:
            for c in range(len(newbox_dic[key])):
                allbox_dic[key].append(newbox_dic[key][c])                        
        return newbox_dic,oldbox_dic,allbox_dic   
        
    
    
    else:
        for i in range(nbox2):
            areaMax = -1
            maxflag = None
            mflag = None
#            boxposlist = []

            for key in message_pre_dic:
                for m in range(len(message_pre_dic[key])):
                    IOU_area = calculateAreaIOU(message_aft[(4*i+1):(4*i+5)],message_pre_dic[key][m])
                    if IOU_area > areaMax:
                        areaMax = IOU_area
                        maxflag = key    
                        mflag = m
#                        boxposlist.clear()
#                        boxposlist = message_aft[(4*i+1):(4*i+5)]
            
            
            box_preArea = abs(int(message_pre_dic[maxflag][mflag][1]) - int(message_pre_dic[maxflag][mflag][3])) * abs(int(message_pre_dic[maxflag][mflag][0]) - int(message_pre_dic[maxflag][mflag][2]))       
            print('areaMax:',areaMax)
            print('box_preArea*0.5:',box_preArea * thre_value)
            if areaMax > box_preArea * thre_value:

                oldbox_dic[maxflag].append(message_aft[(4*i+1):(4*i+5)])
            else:
                maxflag = detectNewBox(message_aft[(4*i+1):(4*i+5)],new_boxthre)
                newbox_dic[maxflag].append(message_aft[(4*i+1):(4*i+5)])
        
        for key in oldbox_dic:
            for c in range(len(oldbox_dic[key])):
                allbox_dic[key].append(oldbox_dic[key][c])
                
        for key in newbox_dic:
            for c in range(len(newbox_dic[key])):
                allbox_dic[key].append(newbox_dic[key][c])
            
            
        return newbox_dic,oldbox_dic,allbox_dic
        
# %%    
      
def isoldBox(message1,message2):
    pass


def isdisappear(message1,message2):
    pass

# %%
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

    
# %%
    
#fun:在显示的图片上写入中文
#im:输入图片
#chinesename:输入的中文ex'你好'
#x+pos,y_pos:中文写入的定点位置
#rgblist:写入中文的RGB颜色列表ex:[0,201,255]
#返回中文的cv格式图片

def drawchinese(im,chinesename,x_pos,y_pos,rgblist):
    cv2_im = cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(cv2_im)

    draw = ImageDraw.Draw(pil_im)
    font= ImageFont.truetype("NotoSansCJK-Black.ttc",20,encoding='utf-8')
    flag = chinesename

    draw.text((x_pos,y_pos),flag,(rgblist[0],rgblist[1],rgblist[2]),font=font)
    
    cv2_text_im = cv2.cvtColor(np.array(pil_im),cv2.COLOR_RGB2BGR)
    return cv2_text_im
    




if __name__ == '__main__':
    pospath = 'objpose/objpose.txt'
    a = mainthread(pospath)
#    getrightorder(pospath)
#    print(a)