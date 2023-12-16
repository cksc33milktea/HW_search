import numpy as np
import random
import math
import matplotlib.pyplot as plt
import time


num_of_stage=1
num_of_op=0

DSP_limit=2500
BRAM_limit=912

convs=[]
DLAs=[]
cut_point=[]
op_time=[]
ich=[]



class node:

    def __init__(self, node_number):
        self.node_number=node_number
    
    def estimate_cycle(self, tr, tc, tn, tm, K):
    
        add1=6*6
        add2=6*6
        add3=18*1.7
        
        
        factor1=float(tc+K-1+add1)/float(tc+K-1)
        factor2=float(tn*K*K+add2)/float(tn*K*K)
        
        if(tc==7):
            factor3=1.8
        else:
            factor3=float(tc+add3)/float(tc) 
            
        times_r=int(self.H1/tr)
        times_c=int(self.W1/tc)
        times_o=int(self.C2/tm)
        times_i=int(self.C1/tn)
        
        if(times_o==0):
            times_o=1
        if(times_i==0):
            times_i=1
            
        cost=0
        exceed_flag=0
        
        #for row in range(0,self.H1,tr):
            #for col in range(0,self.W1,tc):
        if(True):
            if(True):
                for to in range(0,self.C2,tm):
                    
                    cost_now=0
                    
                    for ti in range(0,self.C1+tn,tn):
                        
                        if(ti+tn>=self.C1+tn):
                        
                            compute=tr*tc*K*K
                            
                            store=tm*tr*tc*factor3
                            
                            cc=cost_now
                            
                            cost_now=cost_now+compute
                            
                            if(store>cost_now):
                                cost_now+=(store)
                                cost_now-=compute
                                exceed_flag=1
                                
                        else:
                            flag1=0 
                            
                            if(to==0):
                                flag1=1
                                
                            input_=0
                            
                            if(flag1==1):
                                input_=tn*(tr+K-1)*(tc+K-1)*factor1
                                
                                
                            flag1_r=flag1 
                            
                            kernel=tn*tm*K*K*factor2
                            
                            
                            
                            compute=tr*tc*K*K 
                            max1=max(kernel,input_)
                            
                            if(ti!=0):
                                cost_now=cost_now+max(max1,compute)
                            else:
                                cost_now=cost_now+max1
                                
                    cost+=cost_now
                    
        cost=cost*times_r*times_c
        
        store=tm*tr*tc*factor3
        cost=cost+store
        cost=cost-tr*tc*K*K
        
        if(exceed_flag==1):
        
            if(self.C2>tm):
            
                t1=int(self.C2/tm)
                t2=int(self.C2%tm)
                
                gap=(float(tc/7)*0.5)
                gap=gap*250
                
                cost=tm*tr*tc*t1*factor3
                
                cost=cost+t2*tr*tc*t1*factor3+tr*gap
                
                cost=cost*times_r*times_c
                
            else:
                cost=self.H1*self.W1*tm*(times_o)*factor3
        
        return cost

class DLA:

    def __init__(self, tr, tc, tn, tm):
        self.tr=tr
        self.tc=tc
        self.tn=tn
        self.tm=tm
        
    def dump(self):
        print(self.tr,self.tc,self.tn,self.tm)

def estimate_stage_time(DLAs1, cut_point1, num_of_stage):
    
    bottle_neck=-1
    biggest=-1
    
    pre_stage_input_size=-1
    
    time=[]
    
    
    for i in range(num_of_stage):
        start=cut_point1[i]
        end=cut_point1[i+1]
        
        real_start=start
        real_end=cut_point1[i+1]-1
        
        stage_time=0
        
        wait_stage=0
        forward_stage=0
        
        
        for j in range(start,end):
            
            K=convs[j].K
            
            cost=convs[j].estimate_cycle(DLAs1[i].tr, DLAs1[i].tc, DLAs1[i].tn, DLAs1[i].tm, K)/1000000
            
            cost=cost*1000
            cost=cost/150
            
            
            #print("FPGA:", cost)
            load_kernel=float((convs[j].C1*convs[j].C2*K*K)/(512*512*3*3))*15
            #print("load kernel",load_kernel)
            
            
            if(j==real_start and i!=0):
                wait_stage=float((pre_stage_input_size)/(128*112*112))*20
            
            if(j==real_end and i!=num_of_stage-1):
                forward_stage=float((convs[j].C2*convs[j].H2*convs[j].W2)/(128*112*112))*10
                pre_stage_input_size=convs[j].C2*convs[j].H2*convs[j].W2
            
            cost=cost+load_kernel+5
            
            #print("invoke time:",cost)
            
            stage_time=stage_time+cost
            
            stage_time=stage_time+op_time[j]
            if(j==end-1):
                stage_time=stage_time+op_time[j+1]
            
        stage_time_r=stage_time
        
        stage_time=stage_time+wait_stage+forward_stage
        
        time.append(stage_time)
        
        if(stage_time>bottle_neck):
            bottle_neck=stage_time
            biggest=i
        #print(stage_time)
        
    bottle_neck=bottle_neck
    
    return bottle_neck, biggest, time
    
    
def estimate_DSP(DLAs1, num_of_stage):
    
    DSP_count=0
    
    for i in range(num_of_stage):
        
        DSP_count=DSP_count+(DLAs1[i].tn*DLAs1[i].tm)*2+130
        
    return DSP_count
    
def estimate_BRAM(DLAs1, num_of_stage, cut_point):
    
    BRAM_count=0
    
    bb=[]
    
    for i in range(num_of_stage):
        
        
        start=cut_point[i]
        end=cut_point[i+1]
        
        temp_ich=[]
        for j in range(start,end):
            temp_ich.append(ich[j])
        
        max_ich=max(temp_ich)
        
        Ntime=max_ich/DLAs1[i].tn
        Ntime=Ntime/2
        BRAM_count_temp=Ntime*DLAs1[i].tn*(DLAs1[i].tr+3-1)*(DLAs1[i].tc+3-1)+DLAs1[i].tm*DLAs1[i].tr*DLAs1[i].tc
        BRAM_count_temp=BRAM_count_temp*2*32/18000
        BRAM_count_temp=BRAM_count_temp+2*DLAs1[i].tm
        BRAM_count_temp=BRAM_count_temp/2
        
        BRAM_count=BRAM_count+BRAM_count_temp
        bb.append(BRAM_count_temp)
    
    #print(bb)
    return BRAM_count

def tune_DLA_size(biggest, num_of_stage):

    DLAs_new=[]
    cut_point_new=[]
    
    
    '''
    for i in range(num_of_stage):
        if(i==0):
            DLA_temp=DLA(28,14,4,64)
        if(i==1):
            DLA_temp=DLA(28,14,4,64)
        if(i==2):
            DLA_temp=DLA(28,14,4,64)
        if(i==3):
            DLA_temp=DLA(14,14,4,64)
            
        DLAs_new.append(DLA_temp)
    
    return DLAs_new, cut_point
    '''
    
    for i in range(num_of_stage):
        DLA_temp=DLA(DLAs[i].tr,DLAs[i].tc,DLAs[i].tn,DLAs[i].tm)
        DLAs_new.append(DLA_temp)
    
    for i in range(num_of_stage+1):
        cut_point_new.append(cut_point[i])
    
    new_num_of_stage=num_of_stage
    
    i = random.randint(0, num_of_stage-1)#select a stage
    
    j=random.randint(0, 1)
    
    if(j==0):
        i=biggest
    
    #i=biggest
        
    #print(biggest)
    
    #print(i, len(cut_point))
    ops_in_stage=cut_point[i+1]-cut_point[i]
    
    operation= random.randint(0, 11)
    '''
    if(j==0 and i%2!=0):
        return DLAs, cut_point
    elif(j==1 and i%2==0):
        return DLAs, cut_point
    '''
    #if(i!=biggest and operation%2!=0):
    #    operation=operation+1
    
    if(operation==0):#increase tr
        
        start=cut_point[i]
        end=cut_point[i+1]
        
        min_H=999
        
        for j in range(start,end):
            if(convs[j].H1<min_H):
                min_H=convs[j].H1
        
        if(DLAs_new[i].tr*2<=min_H):
            DLAs_new[i].tr=int(DLAs_new[i].tr*2)
        else:
            DLAs_new[i].tr=DLAs_new[i].tr
    elif(operation==1):#decrease tr
        
        if(DLAs_new[i].tr/2>7):
            DLAs_new[i].tr=int(DLAs_new[i].tr/2)
        else:
            DLAs_new[i].tr=DLAs_new[i].tr
    elif(operation==2):#increase tc
        
        start=cut_point[i]
        end=cut_point[i+1]
        
        min_W=999
        
        for j in range(start,end):
            if(convs[j].W1<min_W):
                min_W=convs[j].W1
        
        if(DLAs_new[i].tc*2<=DLAs_new[i].tr and DLAs_new[i].tc*2<=min_W):
            DLAs_new[i].tc=int(DLAs_new[i].tc*2)
        else:
            DLAs_new[i].tc=DLAs_new[i].tc
    elif(operation==3):#decrease tc
        
        if(DLAs_new[i].tc/2>7):
            DLAs_new[i].tc=int(DLAs_new[i].tc/2)
        else:
            DLAs_new[i].tc=DLAs_new[i].tc
    elif(operation==4):#increase tn
    
        start=cut_point[i]
        end=cut_point[i+1]
        
        min_C1=999
        
        for j in range(start,end):
            if(convs[j].C1<min_C1):
                min_C1=convs[j].C1
        
            
        if(DLAs_new[i].tn*2<=DLAs_new[i].tm and DLAs_new[i].tn<min_C1):
            DLAs_new[i].tn=int(DLAs_new[i].tn*2)
        else:
            DLAs_new[i].tn=DLAs_new[i].tn
            
    elif(operation==5):#decrease tn
        if(DLAs_new[i].tn>=4):
            DLAs_new[i].tn=int(DLAs_new[i].tn/2)
        else:
            DLAs_new[i].tn=DLAs_new[i].tn
    elif(operation==6):#increase tm
    
        start=cut_point[i]
        end=cut_point[i+1]
        
        min_C2=999
        
        for j in range(start,end):
            if(convs[j].C2<min_C2):
                min_C2=convs[j].C2
                
        if(DLAs_new[i].tm<min_C2):
            DLAs_new[i].tm=DLAs_new[i].tm+4
        else:
            DLAs_new[i].tm=DLAs_new[i].tm
        
    elif(operation==7):#decrease tm
        if(DLAs_new[i].tm-4>0):
            DLAs_new[i].tm=DLAs_new[i].tm-4
        else:
            DLAs_new[i].tm=DLAs_new[i].tm
    elif(operation==8 and num_of_stage+1<=5):#increase stage
        expand_stage=random.randint(0, num_of_stage-1)
        
        prob=random.randint(0, 1)
        if(prob==1):
            expand_stage=i
        
        
        divide_op=random.randint(cut_point[expand_stage], cut_point[expand_stage+1])
        
        
        
        if(divide_op==cut_point[expand_stage] or divide_op==cut_point[expand_stage+1]):
            return DLAs_new, cut_point_new, new_num_of_stage
        
        cut_point_new.insert(expand_stage+1,divide_op)
        
        DLA_temp=DLA(DLAs[expand_stage].tr,DLAs[expand_stage].tc,DLAs[expand_stage].tn,DLAs[expand_stage].tm)
        DLAs_new.insert(expand_stage+1,DLA_temp)
        
        new_num_of_stage=num_of_stage+1
        
        
    elif(operation==9 and num_of_stage-1):#decrease stage
    
    
        #print("op9 ",num_of_stage)
        #print(cut_point_new)
        #print(DLAs_new)
        prob=random.randint(0, 1)
        if(prob==1):
            return DLAs_new, cut_point_new, new_num_of_stage
        
        
        decrease_stage=random.randint(0, num_of_stage-2)
        
        if(i<=num_of_stage-2):
            decrease_stage=i
        cut_point_new.pop(decrease_stage+1)
        
        
        
        prob=random.randint(0, 1)
        if(prob==0):
            DLAs_new.pop(decrease_stage)
        elif(prob==1):
            DLAs_new.pop(decrease_stage+1)
        
        new_num_of_stage=num_of_stage-1
    elif(operation==10):#increase operation size
        
        k=random.randint(0, 1)
        
        if(k==0 and i!=0):#modify front
            if(cut_point[i]-cut_point[i-1]>1):
                cut_point_new[i]=cut_point_new[i]-1
        elif(k==1 and i!=num_of_stage-1):#modify back
            if(cut_point[i+2]-cut_point[i+1]>1):
                cut_point_new[i+1]=cut_point_new[i+1]+1
            
            
    elif(operation==11):#decrease operation size
        
        k=random.randint(0, 1)
        
        if(k==0 and i!=0 and ops_in_stage>1):#modify front
            cut_point_new[i]=cut_point_new[i]+1
        elif(k==1 and i!=num_of_stage-1 and ops_in_stage>1):#modify back
            cut_point_new[i+1]=cut_point_new[i+1]-1
        
    
    #print(num_of_stage,len(cut_point_new),len(DLAs_new),"op:",operation)
    #print(DLAs_new[i].tr,DLAs_new[i].tc,DLAs_new[i].tn,DLAs_new[i].tm)
    return DLAs_new, cut_point_new, new_num_of_stage



if __name__ == '__main__':
    
    f = open('./vgg16_conv.txt', "r") 
    
    sum_time=0
    
    with open('./vgg16_time.txt', 'r') as file:
        for line in file:
            number = line.strip()
            is_conv=int(number[0])
            time=int(number[2])
            
            if(is_conv==1):
                op_time.append(sum_time)
                sum_time=0
            else:
                sum_time=sum_time+time
        
    op_time.append(sum_time)
    
    
    #global num_of_op
    
    num_of_op = int(f.readline())
    
    
    for i in range(num_of_op):
        conv_node=node(i)
        conv_node.C1=int(f.readline())
        conv_node.H1=int(f.readline())
        conv_node.W1=int(f.readline())
        conv_node.C2=int(f.readline())
        conv_node.H2=int(f.readline())
        conv_node.W2=int(f.readline())
        conv_node.K=int(f.readline())
        ich.append(conv_node.C1)
        
        convs.append(conv_node)
        
        
    for i in range(num_of_stage):
        DLA_temp=DLA(7,7,4,4)
        DLAs.append(DLA_temp)
        
    f.close()
    
    
    average_op_stage=int(num_of_op/num_of_stage)
    
    for i in range(num_of_stage):
        cut_point.append(int(i*average_op_stage))
    cut_point.append(num_of_op)
    
    
    
    bottle_neck, biggest, stage_time=estimate_stage_time(DLAs, cut_point, num_of_stage)
    
    DSP_usage=estimate_DSP(DLAs, num_of_stage)
    
    
    
    #################################################
    
    
    
    t0 = 50  # Initial temperature
    tmin = 1  # End of iteration, which means minimum temperature
    k = 5  # Iteration in every temperature steps
    coolnum = 0.98

    t = t0

    evetime_distance = []
    
    optimal_cost=99999
    optimal_DLAs=[]
    optimal_cut_point=[]

    while True:
        
        print("temperature: ",t)
        if t <= tmin:
            break
        for times in range(k):
            
            operation = random.randint(0, 0)

            if (operation == 0):
                
                DLAs_new, cut_point_new, new_num_of_stage =tune_DLA_size(biggest, num_of_stage)
                # print("remove!")
            else:
                insert()
                # print("insert!")
            
            
            
            new_bottle_neck, new_biggest, stage_time = estimate_stage_time(DLAs_new, cut_point_new, new_num_of_stage)
            
            diff = new_bottle_neck - bottle_neck
            
            new_DSP_usage=estimate_DSP(DLAs_new, new_num_of_stage)
            new_BRAM_usage=estimate_BRAM(DLAs_new, new_num_of_stage, cut_point_new)
            
            abs_diff=abs(diff)
            
            
            if(new_bottle_neck<optimal_cost and new_DSP_usage<=DSP_limit and new_BRAM_usage<=BRAM_limit):
                optimal_cost=new_bottle_neck
                optimal_DLAs=DLAs_new
                optimal_cut_point=cut_point_new
                optimal_stage=new_num_of_stage
            
            
            if(new_DSP_usage>DSP_limit):
                bottle_neck = bottle_neck
                DLAs=DLAs
                cut_point=cut_point
                num_of_stage=num_of_stage
                biggest=biggest
            elif(new_BRAM_usage>BRAM_limit):
                bottle_neck = bottle_neck
                DLAs=DLAs
                cut_point=cut_point
                num_of_stage=num_of_stage
                biggest=biggest
            
            #elif(new_DSP_usage>DSP_usage):
            #    bottle_neck = new_bottle_neck
            #    DLAs=DLAs_new
            elif diff <= 0:
                bottle_neck = new_bottle_neck
                DLAs=DLAs_new
                cut_point=cut_point_new
                num_of_stage=new_num_of_stage
                biggest=new_biggest
            elif (diff > 0):
                prob = math.exp(-diff/t)

                randnum = random.uniform(0, 1)
                
                if randnum < prob:
                    bottle_neck = new_bottle_neck
                    DLAs=DLAs_new
                    cut_point=cut_point_new
                    num_of_stage=new_num_of_stage
                    biggest=new_biggest
                else:
                    bottle_neck = bottle_neck
                    DLAs=DLAs
                    cut_point=cut_point
                    num_of_stage=num_of_stage
                    biggest=biggest
                    
            #break
        #break
        evetime_distance.append(bottle_neck)
        t = t * coolnum
        print("cost: ",bottle_neck)
    
    
    bottle_neck, biggest, stage_time=estimate_stage_time(optimal_DLAs, optimal_cut_point, optimal_stage)
    
    for i in range(optimal_stage):
        print("predicted execution time of stage ",i+1," : ",int(stage_time[i]),"ms")
    
    DSP_usage=estimate_DSP(optimal_DLAs, optimal_stage)
    print("predicted DSP usage ",DSP_usage)
    BRAM_usage=estimate_BRAM(optimal_DLAs, optimal_stage, optimal_cut_point)
    print("predicted BRAM usage ",int(BRAM_usage))
    
    plt.figure(figsize=(15, 8))
    plt.xlabel("Iteration", fontsize=15)
    plt.ylabel("Distance", fontsize=15)

    plt.plot(evetime_distance, linewidth=2.5,
             label="Everytime smallest distance", color='r')
    plt.legend()
    #plt.show()
    
    f = open('cut_point.txt', 'w')
    
    for i in range(len(optimal_cut_point)-2):
        #print(optimal_cut_point[i+1]-1)
        f.write(str(optimal_cut_point[i+1]-1))
        f.write('\n')
    
    f.close()
    
    for i in range(len(optimal_DLAs)):
        
        cc=0
        f = open('stage'+str(i+1)+'.cpp', 'w')
        
        start=optimal_cut_point[i]
        end=optimal_cut_point[i+1]
        
        temp_ich=[]
        for j in range(start,end):
            temp_ich.append(ich[j])
        
        max_ich=max(temp_ich)
        if(max_ich==3):
            max_ich=4
        
        with open('./Accelerator_template.txt', 'r') as file:
            for line in file:
                cc=cc+1
                if(line.count('Tr_plug')==1):
                    line=line.replace('Tr_plug', str(optimal_DLAs[i].tr))
                elif(line.count('Tc_plug')==1):
                    line=line.replace('Tc_plug', str(optimal_DLAs[i].tc))
                elif(line.count('Tn_plug')==1):
                    line=line.replace('Tn_plug', str(optimal_DLAs[i].tn))
                elif(line.count('Tm_plug')==1):
                    line=line.replace('Tm_plug', str(optimal_DLAs[i].tm))
                elif(line.count('Ntime_plug')==1):
                    line=line.replace('Ntime_plug', str(max_ich))
                elif(line.count('test1')==1):
                    line=line.replace('test1', 'stage'+str(i+1))
                f.write(line)
            #print(cc)
        f.close()
        
        f = open('stage'+str(i+1)+'.h', 'w')

        with open('./Accelerator_header.txt', 'r') as file:
            for line in file:
                if(line.count('test1')==1):
                    line=line.replace('test1', 'stage'+str(i+1))
                f.write(line)
            #print(cc)
        f.close()
        print('stage'+str(i+1)+'.cpp is available!')


