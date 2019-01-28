import pandas as pd
import numpy as np
import cv2
import os
from PIL import Image, ImageDraw, ImageFont

from math import sqrt

###

IDflag = 0



# %%
#主流程
def mainthread(posepath):
    getrightorder(posepath)
    file = open(pospath)
    all_postlist = []    #所有图片的路径和坐标,每一个元素代表一张图片的信息
    
    Misjudgment=False    # 为真则开始执行处理误判
    dic_addweightPic = pixProbabilityMap(58,480,1,640) #获得整副图片的所有像素点消失概率的分布字典,非梯度概率图
    

    gradientbox = [[0, 0, 639, 479], [64, 48, 575, 431], [128, 96, 511, 383], [192, 144, 447, 335], [256, 192, 383, 287]]
    pro1 = getprobdic(gradientbox[0],gradientbox[1],90)
    pro2 = getprobdic(gradientbox[1],gradientbox[2],70)
    pro3 = getprobdic(gradientbox[2],gradientbox[3],50)
    pro4 = getprobdic(gradientbox[3],gradientbox[4],30)
    pro5 = getsinggleboxpro(gradientbox[4],10)
    dic_addweightPic_gradient = {**pro1,**pro2,**pro3,**pro4,**pro5}   #h获得整副图的区域消失概率的分布字典

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


    allbox_dic = {'up':{},'down':{}} 
    preframe_dic = {}   #记录上一帧的信息字典
    for i in range(len(all_postlist)):               
        if (i < len(all_postlist) - 1):
            preframe_dic = allbox_dic   
            newbox_dic, oldbox_dic, allbox_dic = isnewBox(allbox_dic, all_postlist[i+1], 0.5, 365) #返回的allbox_dic代表当前帧的框,输入的是上一帧的框信息 
            
            
            
            #===========================处理误判开始================================//
            if Misjudgment:
                newboxappeared,oldboxdisappeared = detectdisappearbox(preframe_dic,allbox_dic) #获得目前相对于前一帧,获得消失的旧框,和新出现的框list           
                boxshouldexit = {}
                for key in oldboxdisappeared:
    #                addweight_pro = calculateBoxProbility(dic_addweightPic,oldboxdisappeared[key])  #前一帧中,目前框的消失概率
                    addweight_pro = calculategradientboxProbility(dic_addweightPic_gradient,oldboxdisappeared[key])
                    if addweight_pro < 50:
                        print('消失概率没超过一半,执行改进的欧氏距离匹配寻找')
          
    #                drawrectangle(all_postlist[i+1], oldboxdisappeared[key])
                        searchArea = SearchRectangle([oldboxdisappeared[key][1],oldboxdisappeared[key][3],oldboxdisappeared[key][0],oldboxdisappeared[key][2]])   #扩大的怀疑框的检索区域[x1,y1,x2,y2],(绝对坐标)
                        big_ROI = getScreenshot(all_postlist[i+1],searchArea)  #新图
                        cv2.imshow('big_ROI',big_ROI)
                        cv2.waitKey(10)
    
                        ROI = getScreenshot(all_postlist[i],[oldboxdisappeared[key][1],oldboxdisappeared[key][3],oldboxdisappeared[key][0],oldboxdisappeared[key][2]])   #获得上一帧的截图cv2格式图片
                        cv2.imshow('small_ROI',ROI)
                        cv2.waitKey(10)
                        
                        mindistance = float('inf')  #无穷大
                        flag_rows = 0
                        flag_cols = 0
                        for rows in range(0,(big_ROI.shape[0] - ROI.shape[0]),20):
                            for cols in range(0,(big_ROI.shape[1] - ROI.shape[1]),20):
    #                            print((big_ROI.shape[0] - ROI.shape[0]) )
    #                            print((big_ROI.shape[1] - ROI.shape[1]))
                                im_new = big_ROI[rows:(rows+ROI.shape[0]),cols:(cols+ROI.shape[1])]
    #                            print('ori_ROI:',ROI.shape)
    #                            print('im_new:',im_new.shape)
                                cv2.imshow('000',im_new)
                                cv2.waitKey(10)
                                temp = calculateEuropeanDistance(ROI,im_new)
                                if mindistance > temp:
                                    mindistance = temp
                                    flag_rows = rows
                                    flag_cols = cols
                        print('min:',mindistance)          
                        
                        if mindistance < 400:
                            boxshouldexit[key] = [flag_rows + searchArea[0],flag_rows + searchArea[0] + ROI.shape[0],flag_cols + searchArea[2],flag_cols + searchArea[2] + ROI.shape[1]] 
    
                box1 = cv2.imread(all_postlist[i+1][0])    #在下一帧进行补全   
                for key in boxshouldexit:
                    for keypre in preframe_dic:
                        for subkeypre in preframe_dic[keypre]:
                            if(int(subkeypre) == int(key)):
                                allbox_dic[keypre][subkeypre] = [boxshouldexit[key][2],boxshouldexit[key][0],boxshouldexit[key][3],boxshouldexit[key][1]]        
                for key in allbox_dic:
                    for subkey in allbox_dic[key]:
                        box1 = cv2.rectangle(box1, (int(allbox_dic[key][subkey][0]),int(allbox_dic[key][subkey][1])), (int(allbox_dic[key][subkey][2]),int(allbox_dic[key][subkey][3])), (0,255,0),2)
          
                cv2.imshow('buquan',box1)
                cv2.waitKey(100)
        
                  
             #===========================处理误判结束================================//
                
             
             
             
            #drawPro置True则显示人头消失概率,drawupdown=True显示上下行,drawnun=True 显示框编号
            #注意根据输入概率图的不同需要改变输入的dic_addweightPic_gradient  或者 dic_addweightPic
            continutDrawPic(all_postlist[i+1],allbox_dic,dic_addweightPic_gradient,drawPro=True,drawupdown=True,drawnum=True)

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

#fun:在图片上画框,标识上下,画线等
#message:列表,第一项为图片路径,后面的是框的坐标
#allbox_dic:字典,包含了读入图片框的位置,框的编号,框的上下行{'up':{'id':[],'id':[],...},'down':{'id':[],'id':[],...}}
#drawPro:为True则显示消失概率,默认False不显示
def continutDrawPic(message,allbox_dic,dic_addweightPic,drawPro = False,drawupdown = False, drawnum = False):
    
    
    nbox = len(allbox_dic['up']) + len(allbox_dic['down'])
    up_people = len(allbox_dic['up']) 
    down_people = len(allbox_dic['down'])
    
    allpeople = ('总人头数: %d')%nbox
    uppeopleshow = ('上行人数: %d')%up_people
    downpeopleshow = ('下行人数: %d')%down_people
    
    
    
    im = cv2.imread(message[0])
    
    
    for key in allbox_dic:
        if key == 'up':
            for subkey in (allbox_dic[key]):
                if len(allbox_dic[key][subkey]) == 0:
                    continue
                else:
                    if drawnum:
                        numbox = ('%d 号框')%(int(subkey))
                        im = drawchinese(im,numbox,int(allbox_dic[key][subkey][0])+25,int(allbox_dic[key][subkey][1])+25,[0,255,0])
                    if drawupdown:
                        im = drawchinese(im,'上行',int(allbox_dic[key][subkey][0]),int(allbox_dic[key][subkey][1]),[0,201,255])                        
                    im = cv2.rectangle(im,(int(allbox_dic[key][subkey][0]),int(allbox_dic[key][subkey][1])),(int(allbox_dic[key][subkey][2]),int(allbox_dic[key][subkey][3])),(50,100,255),2)
                    
                    if drawPro == True:      #消失概率显示

#                        pro = calculateBoxProbility(dic_addweightPic,allbox_dic[key][subkey])   #像素概率
                        
                        pro = calculategradientboxProbility(dic_addweightPic,allbox_dic[key][subkey])  #梯度概率
                        disappearPro = ('消失概率:%d')%pro
                        im = drawchinese(im,disappearPro,int(allbox_dic[key][subkey][0])+25,int(allbox_dic[key][subkey][1])+25,[200,50,255])
                        



                
        elif key == 'down':
            for subkey in (allbox_dic[key]):
                if len(allbox_dic[key][subkey]) == 0:
                    continue
                else:
                    if drawnum:
                        numbox = ('%d 号框')%(int(subkey))
                        im = drawchinese(im,numbox,int(allbox_dic[key][subkey][0])+25,int(allbox_dic[key][subkey][1])+25,[0,255,0])
                    if drawupdown:
                        im = drawchinese(im,'下行',int(allbox_dic[key][subkey][0]),int(allbox_dic[key][subkey][1]),[0,201,255])
                   
                    im = cv2.rectangle(im,(int(allbox_dic[key][subkey][0]),int(allbox_dic[key][subkey][1])),(int(allbox_dic[key][subkey][2]),int(allbox_dic[key][subkey][3])),(50,100,255),2)
                    
                    if drawPro == True:   #消失概率显示

#                        pro = calculateBoxProbility(dic_addweightPic,allbox_dic[key][subkey])
                        pro = calculategradientboxProbility(dic_addweightPic,allbox_dic[key][subkey])
                        disappearPro = ('消失概率:%d')%pro
                        im = drawchinese(im,disappearPro,int(allbox_dic[key][subkey][0])+25,int(allbox_dic[key][subkey][1])+25,[200,50,255])
   
    im = drawchinese(im,allpeople,500,20,[255,201,0])
    im = drawchinese(im,uppeopleshow,500,50,[255,201,0])
    im = drawchinese(im,downpeopleshow,500,80,[255,201,0])
    
    cv2.imshow('puttex',im)
    cv2.waitKey(100)

        
# %%    
    
#func:根据前一帧的框位置,判断目前帧的所有框那些是新框,那些是旧款,并做标记
#message_pre: 位置信息字典{'up':{'id':[],'id':[],'id'..},'down':{'id':[],'id':[],'id'...}}
#message_aft: 目前帧的图片路径,框的位置信息列表
#thre_value:  用面积判定为新框的阈值0.5(表示新帧的框覆盖旧帧框面积超过一半)
#new_boxthre: 对于新框判定上下行的阈值(ex:y值大于365为down,小于为up)
def isnewBox(message_pre_dic,message_aft,thre_value,new_boxthre):
    
    global IDflag
    nbox2 = int(len(message_aft)/4)    #目前帧的框个数
    nbox1 = int(len(message_pre_dic['up']) + len(message_pre_dic['down'])) #前一帧的框个数
#    print('nbox2:',nbox2)
#    print('nbox1:',nbox1)
    newbox_dic = {'up':{},'down':{}}  #存新框(新上+新下)
    oldbox_dic = {'up':{},'down':{}}  #存旧框(旧上+旧下)
    allbox_dic = {'up':{},'down':{}}  #存所有框(上+下)
    
    if nbox2 == 0:
        newbox_dic = {'up':{},'down':{}}  #存新框(新上+新下)
        oldbox_dic = {'up':{},'down':{}}  #存旧框(旧上+旧下)
        allbox_dic = {'up':{},'down':{}}  #存所有框(上+下)
#        IDflag = 0
        return newbox_dic,oldbox_dic,allbox_dic
    
    if nbox1 == 0:        #如果前一帧没有框,那么此帧全为新框.新框就进行分配ID
        for i in range(nbox2):
            upDown = detectNewBox(message_aft[(4*i+1):(4*i+5)],new_boxthre)
#            print('upDown',upDown)
            idflag = str(IDflag)  #唯一框标志
#            print('idflag:',idflag)
            IDflag += 1
            newbox_dic[upDown][idflag] = message_aft[(4*i+1):(4*i+5)]
#            newbox_dic[upDown].append(message_aft[(4*i+1):(4*i+5)])
            
                
        for key in newbox_dic:
            for subkey in (newbox_dic[key]):
                if len(newbox_dic[key][subkey]) == 0:
                    continue
            
                else:
                    allbox_dic[key][subkey] = newbox_dic[key][subkey]
                    
        return newbox_dic,oldbox_dic,allbox_dic
        
    
    
    else:
        for i in range(nbox2):
            areaMax = -1
            maxflag = None
            mflag = None
#            boxposlist = []
            

            for key in message_pre_dic:
                for subkey in (message_pre_dic[key]): #subkey为每个框的唯一标志(0-10000))
                    if len(message_pre_dic[key][subkey]) == 0:
                        continue
                    else:
                        IOU_area = calculateAreaIOU(message_aft[(4*i+1):(4*i+5)],message_pre_dic[key][subkey])
#                        print('message_pre_dic[key][subkey]:',message_pre_dic[key][subkey])
#                        print('message_aft[(4*i+1):(4*i+5)]:',message_aft[(4*i+1):(4*i+5)])
                        if IOU_area > areaMax:
                            areaMax = IOU_area
                            maxflag = key    
                            mflag = subkey
#                            boxposlist.clear()   #注意深拷贝问题
#                            boxposlist = message_pre_dic[key][subkey]
            
            
            box_preArea = abs(int(message_pre_dic[maxflag][mflag][1]) - int(message_pre_dic[maxflag][mflag][3])) * abs(int(message_pre_dic[maxflag][mflag][0]) - int(message_pre_dic[maxflag][mflag][2]))       
#            print('areaMax:',areaMax)
#            print('box_preArea*0.5:',box_preArea * thre_value)
            if areaMax > box_preArea * thre_value:  #设置为旧框条件
                oldbox_dic[maxflag][mflag] = message_aft[(4*i+1):(4*i+5)]
            else:                                  #新框条件
                newflag = detectNewBox(message_aft[(4*i+1):(4*i+5)],new_boxthre)
                idflag = str(IDflag)  #唯一框标志
                IDflag += 1
                newbox_dic[newflag][idflag] = message_aft[(4*i+1):(4*i+5)]

        for key in oldbox_dic:
            for subkey in (oldbox_dic[key]):
                if len(oldbox_dic[key][subkey]) == 0:
                    continue
                else:
                    allbox_dic[key][subkey] = oldbox_dic[key][subkey]
                
        for key in newbox_dic:
            for subkey in (newbox_dic[key]):
                if len(newbox_dic[key][subkey]) == 0:
                    continue
                else:
                    allbox_dic[key][subkey] = newbox_dic[key][subkey]
                                               
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
    

# %%
#fun: 此两个函数是画阶梯概率分布图
#im:输入图像
#y_begin:整副图片有效区域的上边界
#y_end:整副图片有效区域的下边界
#partitionnum:需要分成多个个部分
def drawProbabilityMapRow(im,y_begin,y_end,partitionnum):
    dic_partition = {}
    dic_partition['0'] = y_begin
    width = im.shape[0]
    avgwidth = int((y_end - y_begin)/partitionnum)
    for i in range(1,partitionnum):        
        flag_pre = str(i - 1)
        flag = str(i)
        dic_partition[flag] = dic_partition[flag_pre] + avgwidth
    flag = str(partitionnum)
    dic_partition[flag] = width
    cv2.line(im,(0,y_begin),(640,y_begin),(140,230,240),2)
    for i in range(1,partitionnum+1):
        flag = str(i)
#        Vanishingprobability
        cv2.line(im,(0,dic_partition[flag]),(640,dic_partition[flag]),(140,230,240),2)
        
        if i <= int((partitionnum+1)/2):
            Vanishingprobability = (int((partitionnum+1)/2) -i + 1) * 10
            showtext = str(Vanishingprobability)
            cv2.putText(im,showtext,(0,dic_partition[flag]),cv2.FONT_HERSHEY_COMPLEX,0.6,(0,0,255),2)
        else:
            Vanishingprobability = (i - int((partitionnum+1)/2) + 1) * 10
            showtext = str(Vanishingprobability)
            cv2.putText(im,showtext,(0,dic_partition[flag]),cv2.FONT_HERSHEY_COMPLEX,0.6,(0,0,255),2)
            
#        cv2.putText(im,key,(int(allbox_dic[key][i][0]),int(allbox_dic[key][i][3])),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
    return dic_partition


#fun: 此两个函数是画阶梯概率分布图
#im:输入图像
#y_begin:整副图片有效区域左边界
#y_end:整副图片有效区域的右边界
#partitionnum:需要分成多个个部分

def drawProbabilityMapCol(im,x_begin,x_end,partitionnum):
    dic_partition = {}
    dic_partition['0'] = x_begin
    width = im.shape[1]
    avgwidth = int((x_end - x_begin)/partitionnum)
    for i in range(1,partitionnum):        
        flag_pre = str(i - 1)
        flag = str(i)
        dic_partition[flag] = dic_partition[flag_pre] + avgwidth
    flag = str(partitionnum)
    dic_partition[flag] = width
    cv2.line(im,(x_begin,0),(x_begin,640),(140,230,240),2)
    for i in range(1,partitionnum+1):
        flag = str(i)
#        Vanishingprobability
        cv2.line(im,(dic_partition[flag],0),(dic_partition[flag],640),(140,230,240),2)
        
        if i <= int((partitionnum+1)/2):
            Vanishingprobability = (int((partitionnum+1)/2) -i + 1) * 10
            showtext = str(Vanishingprobability)
            cv2.putText(im,showtext,(dic_partition[str(int(flag)-1)],20),cv2.FONT_HERSHEY_COMPLEX,0.6,(0,0,255),2)
        else:
            Vanishingprobability = (i - int((partitionnum+1)/2) + 1) * 10
            showtext = str(Vanishingprobability)
            cv2.putText(im,showtext,(dic_partition[str(int(flag)-1)],20),cv2.FONT_HERSHEY_COMPLEX,0.6,(0,0,255),2)

    return dic_partition


# %%
#fun:获得一张图的概率分布字典图
#y_begin:整副图片有效区域的上边界
#y_end:整副图有效区域的下边界
#x_begin:整副图片有效区域的左边界
#x_end:整副图片有效区域的右边界
#注意,先对整副图片(640*480)概率初始化了
def pixProbabilityMap(y_begin,y_end,x_begin,x_end):
    dic_partion = {}
    
    for i in range(640):  #初始化概率图
        for j in range(480):
            flag = str(i)+str(j)
            dic_partion[flag] = 100
    
    midpos_x = int((x_end - x_begin)/2) 
    midpos_y = int((y_end-y_begin)/2) 
    for i in range(x_begin,x_end):
        for j in range(y_begin,y_end):
            if i < (x_begin + midpos_x) and j < (y_begin + midpos_y):
                key =str(i) +str(j)
                dic_partion[key] = abs((100-(100/midpos_x * (i- x_begin + 1))) + (100- (100/midpos_y * (j-y_begin + 1)))) #某个像素点的消失概率
            elif i < (x_begin + midpos_x) and j > (y_begin + midpos_y):
                key =str(i) +str(j)
                dic_partion[key] = abs((100-(100/midpos_x * (i-x_begin + 1))) + ((100/midpos_y * (j-y_begin + 1)) - 100)) #某个像素点的消失概率
            elif i > (x_begin + midpos_x) and j <(y_begin + midpos_y):
                key =str(i) +str(j)
                dic_partion[key] = abs(((100/midpos_x * (i-x_begin + 1))-100) + (100- (100/midpos_y * (j-y_begin + 1)))) #某个像素点的消失概率
            elif i > (x_begin + midpos_x) and j > (y_begin + midpos_y):
                key =str(i) +str(j)
                dic_partion[key] = abs(((100/midpos_x * (i-x_begin + 1))-100) + ((100/midpos_y * (j-y_begin + 1))-100)) #某个像素点的消失概率
    return dic_partion
  
    

# %%
#fun: 计算一个框的消失概率
#dic_partion:640*480 的一个字典,记录每个像素点的消失概率 {'0':15,'1':29,.....}
#nbox: 一个输出框的列表[x1,y1,x2,y2]


def calculateBoxProbility(dic_partion, nbox):

    nbox = [int(x) for x in nbox]
    for i in range(len(nbox)):  #不要出现0
        if nbox[i] == 0:
            nbox[i] = 1
    addProbility = 0
    x_max =max(nbox[2],nbox[0])
    x_min = min(nbox[2],nbox[0])
    y_max = max(nbox[3],nbox[1])
    y_min = min(nbox[3],nbox[1])

#    dic_partion = {}
    
    for i in range(x_min,x_max):
        for j in range(y_min,y_max):
            flag = str(i) +str(j)
            addProbility += dic_partion[flag]
    
    addweightpro = addProbility / ((x_max - x_min) * (y_max - y_min) * 2)
    return addweightpro
    
                 


#%%
    
def calculategradientboxProbility(dic_partion,nbox):
    nbox = [int(x) for x in nbox]
    
    addProbility = 0
    x_max =max(nbox[2],nbox[0])
    x_min = min(nbox[2],nbox[0])
    y_max = max(nbox[3],nbox[1])
    y_min = min(nbox[3],nbox[1])

#    dic_partion = {}
    
    for i in range(x_min,x_max):
        for j in range(y_min,y_max):
            flag = str(i) +str(j)
            addProbility += dic_partion[flag]
    addweightpro = addProbility / ((x_max - x_min) * (y_max - y_min))
    return addweightpro



# %%
def boxdisappearP(box,y_begin,y_end):
    
    pass

#
#fun:输出目前帧相对与前一帧.新出现框和消失的旧框的坐标,在目前帧中,输出新出现框的位置,和旧帧消失的旧框的位置
#pre_dicnbox:前一帧的信息
#now_dicnbox:目前帧的信息

def detectdisappearbox(pre_dicnbox,now_dicnbox):
    predic = []
    nowdic = []
    disappearoldboxflag = []  #目前帧消失的框编号
    appearnewboxflag=  []     #目前帧新出现的框编号
    oldboxdisappeared = {}   #目前帧消失的框的坐标[[],[],[],[]...]
    newboxappeared = {}      #目前帧新出现的框的坐标[[],[],[],[]...]
    
    for key in pre_dicnbox:
        for subkey in pre_dicnbox[key]:
            predic.append(subkey)
    
    
    for key in now_dicnbox:
        for subkey in now_dicnbox[key]:
            nowdic.append(subkey)
            
#    print('================================================')
#    print(predic)
#    print(nowdic)
#    print('================================================')
    disappearoldboxflag = list(set(predic).difference(set(nowdic)))  #
    appearnewboxflag = list(set(nowdic).difference(set(predic)))
    
    for key in pre_dicnbox:
        for subkey in disappearoldboxflag:
            if subkey in pre_dicnbox[key]:
                oldboxdisappeared[subkey] = pre_dicnbox[key][subkey]
#                oldboxdisappeared.append(pre_dicnbox[key][subkey])

    for key in now_dicnbox:
        for subkey in appearnewboxflag:
            if subkey in now_dicnbox[key]:   
                newboxappeared[subkey] = now_dicnbox[key][subkey]
#                newboxappeared.append(now_dicnbox[key][subkey])
      
    return newboxappeared,oldboxdisappeared



# %%
#fun : 对感兴趣区域进行扩张,返回扩大后的感兴趣区域坐标[y1,y2,x1,x2]
#oldboxpose:[y1,y2,x1,x2]  list,注意在opencv中使用切片时候
def SearchRectangle(oldboxpos):
    oldboxpos = [int(x) for x in oldboxpos]
#    print('old:',oldboxpos)
    big_oldboxpos = []
    oldboxpos[0] = oldboxpos[0] - 80
    oldboxpos[1] = oldboxpos[1] +80
    oldboxpos[2] = oldboxpos[2] - 80
    oldboxpos[3] = oldboxpos[3] + 80
    if oldboxpos[0] < 2:
        oldboxpos[0] = 2
    if oldboxpos[1] > 478:
        oldboxpos[1] = 479
    if oldboxpos[2] <2 :
        oldboxpos[2] = 2
    if oldboxpos[3] > 638:
        oldboxpos[3] = 639
    big_oldboxpos = oldboxpos
#    print('new:',big_oldboxpos)
    return big_oldboxpos
    


#%%

#fun:返回im_ori 和 im_new的欧氏距离
#im_ori:前一帧头像所在位置的截图,cv格式图片
#im_new:与上一帧头像尺寸相同的此帧截图,cv格式图片


def calculateEuropeanDistance(im_ori,im_new):
    EuropeanDistance = 0
    for i in range(im_ori.shape[0]):
        for j in range(im_ori.shape[1]):
            (b,g,r) = im_ori[i,j]
            (b1,g1,r1) = im_new[i,j]
            b = float(b)
            g = float(g)
            r = float(r)
            b1 = float(b1)
            g1 = float(g1)
            r1 = float(r1)
            
            ravg = (r+r1)/2
            R = r - r1
            G = g - g1
            B = b - b1
            
            EuropeanDistance += sqrt((2+ravg)*R*R +4*G*G + (2+(255-ravg)/256)*B*B)
        
    EuropeanDistance /= (im_ori.shape[1] * im_ori.shape[0])
            
#            EuropeanDistance += sqrt(pow((b-b1),2) + pow((g-g1),2) + pow((r-r1),2))
    return EuropeanDistance
            



def getScreenshot(message, nbox):
    im = cv2.imread(message[0])
    nbox = [int(x) for x in nbox]
    ROI =im[nbox[0]:nbox[1],nbox[2]:nbox[3]]  #im[y1:y2,x1:x2]
#    cv2.imshow('big_ROI',ROI)
#    cv2.waitKey(10)
    return ROI

def drawrectangle(im,boxpos):

#    im = cv2.imread(message[0])
    cv2.rectangle(im, (int(boxpos[2]),int(boxpos[0])), (int(boxpos[3]),int(boxpos[1])), (0,255,0),2)
#    cv2.imshow('disappear',im)
#    cv2.waitKey(100)
    return im

#%%
#fun 获得640*480的概率分布图,返回为一个字典
#nbox1:外围大框的坐标[x1,y1,y1,y2]
#nbox2:内围小框的坐标[x1,y1,x2,y2]
#pro: nbox1,nbox2香交形成的环的概率值


def getprobdic(nbox1,nbox2,pro):  #大框为nbox1,大框与小框nbox2形成的环形概率为pro
    probdic = {}
    for i in range(nbox1[0],nbox1[2]):
        for j in range(nbox1[1],nbox2[1]):
            key = str(i) + str(j)
            probdic[key] = pro

    
    for i in range(nbox1[0],nbox1[2]):
        for j in range(nbox2[3],nbox1[3]):
            key = str(i) + str(j)
            probdic[key] = pro

    
    for i in range(nbox1[0],nbox2[0]):
        for j in range(nbox2[1],nbox2[3]):
            key = str(i) + str(j)
            probdic[key] = pro

            
    for i in range(nbox2[2],nbox1[2]):
        for j in range(nbox2[1],nbox2[3]):
            key = str(i) + str(j)
            probdic[key] = pro


        
    return probdic
# %%
# fun:对单个框进行概率标注

def getsinggleboxpro(box1,pro):
    prodic = {}
    for i in range(box1[0],box1[2]):
        for j in range(box1[1],box1[3]):
            key = str(i) + str(j)
            prodic[key] = pro

    return prodic


if __name__ == '__main__':
    
    pospath = 'objpose/objpose.txt'
    a = mainthread(pospath)
#    getrightorder(pospath)
#    print(a)
