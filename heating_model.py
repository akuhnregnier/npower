# -*- coding: utf-8 -*-
"""
Created on Tue Nov 03

@author: Make Weather Models Great Again
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cPickle as pickle
import os
from numpy.fft import fft
from numpy.fft import fftfreq
import scipy.optimize as opt
import copy
from scipy.optimize import minimize as minimize
import math
import time
from numba import jit,float64
from matplotlib.widgets import Slider, Button, RadioButtons

plt.close('all')

pd.options.display.expand_frame_repr = False
pd.options.display.max_columns = 15
source = 'round_1.xlsx'
picklefile = 'round1.pickle'
if not os.path.isfile(picklefile):
    df = pd.read_excel(source)
    with open(picklefile,'wb') as f:
        pickle.dump(df,f,protocol=2)
else:
    with open(picklefile,'rb') as f:
        df = pickle.load(f)
    
print "Raw Dataset, rows, columns:", df.shape

lim = df.loc[df['Demand'] != '?? FC1 ??']
new_columns = [i for i in lim.columns if 'Unnamed' not in i]
lim = lim[new_columns]
lim = lim.fillna(lim.mean())
    
temps = lim['Temperature'].values
demands = lim['Demand'].values
demands = np.array(demands,dtype=float)

@jit(nopython=True)
def model(const,temps,predictions,index):
    Tb = const[0]*(1+const[1]*np.sin((2*np.pi*index/(365.25*48))+const[2]))
    T = temps[index]
    if index%48<12:
        alpha = const[5]
    elif index%48<24:
        alpha = const[6]
    elif index%48<36:
        alpha = const[7]
    else:
        alpha = const[8]
    '''
    if Tb<T:
        heating = (1+alpha)*(Tb-T)*const[3]
    else:
        heating = 0
    '''
    heating = (1+alpha)*(Tb-T)*const[3]
    loss = const[4]*(Tb-T)
    if index%48<14 or index%48>=42:
        #night constants
        return heating+loss+const[9]
    else:
        #day heating
        return heating+loss+const[10]

@jit(nopython=True)
def sub_new(const,temps,predictions):    
    for i in range(0,len(temps)):
        predictions[i] = model(const,temps,predictions,i)
    return predictions
    
def new_optimise(const,demands=demands,temps=temps):
    predictions = np.zeros(len(temps))
    predicted = sub_new(const,temps,predictions)
    result = 1-abs(np.corrcoef(predicted,demands)[0][1])
    #print (', '.join(['%+.2e']*const.shape[0])) % tuple(const),result
    if math.isnan(result):
        return 1e100
    return result
    
def get_results(const,demands=demands,temps=temps):
    predictions = np.zeros(len(temps))
    print "Calling subnew"
    predicted = sub_new(const,temps,predictions)
    result = 1-abs(np.corrcoef(predicted,demands)[0][1])
    print (', '.join(['%+.2e']*const.shape[0])) % tuple(const),result
    if math.isnan(result):
        print "ERROR"
        return 1e100,np.zeros((len(demands)))
    return result,predicted
    
bounds = (
(0,40),
(-0.4,.4),  
(0,2*np.pi),
(-100,200),
(-100,200),
(-1.,1.),
(-1.,1.),
(-1.,1.),
(-1.,1.),
(-400,400),
(-400,400)
)

#result = opt.basinhopping(new_optimise,[20,0,0,100,100,0,0,0,0],stepsize=0.01,niter=500)
'''
x = []
f = []
for i in range(1):
    x0 = [np.random.uniform(bounds[k][0],bounds[k][1]) for k in range(len(bounds))]
    x.append(x0)
    result = opt.minimize(new_optimise,x0,method='TNC',
                          bounds = bounds,options={'disp':False})
    f.append(result.fun)
    print "finished:",('[ '+', '.join(['%+.2e']*len(x0))+' ] ') % tuple(x0),result.fun
'''
'''
0 Tb
1 A
2 phi
3 Tp
4 Lp
5         4 alphas, for 4 equally divided times of the day
6
7
8
'''
'''
ranges = (
slice(0,40,10),
slice(-0.1,.1,0.02),  
slice(0,np.pi,0.4),
slice(0,200,35),
slice(0,200,35),
slice(-1,1,1),
slice(-1,1,1),
slice(-1,1,1),
slice(-1,1,1)
)

result = opt.brute(new_optimise,ranges=ranges,finish=None,full_output=True)
'''

const = np.array([35,0.3,2,80,2,-1,-.23,1,1,0,0,0,0],dtype=np.float64)

fig, ax = plt.subplots(figsize=(23,11.5))
plt.subplots_adjust(left=0.45, bottom=0.0)
x = range(len(demands))
l1, = plt.plot(x,demands,lw=1,color='blue')
results = get_results(const)
l2, = plt.plot(x, results[1], lw=2, color='red')
ax.set_title(str(results[0]))
plt.axis([0, max(x), -50, max(demands)*1.6])

axcolor = 'lightgoldenrodyellow'
left = 0.02
width = 0.35
height = 0.03
axTb = plt.axes( [left, 0.1 , width, height], axisbg=axcolor)
axA = plt.axes(  [left, 0.15, width, height], axisbg=axcolor)
axphi = plt.axes([left, 0.2 , width, height], axisbg=axcolor)
axTp= plt.axes(  [left, 0.25, width, height], axisbg=axcolor)
axLp= plt.axes(  [left, 0.3 , width, height], axisbg=axcolor)
axa0= plt.axes(  [left, 0.35, width, height], axisbg=axcolor)
axa1= plt.axes(  [left, 0.4 , width, height], axisbg=axcolor)
axa2= plt.axes(  [left, 0.45, width, height], axisbg=axcolor)
axa3= plt.axes(  [left, 0.5 , width, height], axisbg=axcolor)
axCn= plt.axes(  [left, 0.55, width, height], axisbg=axcolor)
axCd= plt.axes(  [left, 0.6 , width, height], axisbg=axcolor)
axC = plt.axes(  [left, 0.65, width, height], axisbg=axcolor)
axM = plt.axes(  [left, 0.7,  width, height], axisbg=axcolor)

Tb = Slider(axTb, 'Tb', bounds[0][0],bounds[0][1], valinit=const[0])
A = Slider(axA, 'A',    bounds[1][0],bounds[1][1], valinit=const[1])
phi= Slider(axphi, 'phi',   bounds[2][0],bounds[2][1], valinit=const[2])
Tp= Slider(axTp, 'Tp',    bounds[3][0],bounds[3][1], valinit=const[3])
Lp= Slider(axLp, 'Lp',    bounds[4][0],bounds[4][1], valinit=const[4])
a0= Slider(axa0, 'a0',    bounds[5][0],bounds[5][1], valinit=const[5])
a1= Slider(axa1, 'a1',    bounds[6][0],bounds[6][1], valinit=const[6])
a2= Slider(axa2, 'a2',    bounds[7][0],bounds[7][1], valinit=const[7])
a3= Slider(axa3, 'a3',    bounds[8][0],bounds[8][1], valinit=const[8])
Cn= Slider(axCn, 'Cn',    bounds[9][0],bounds[9][1], valinit=const[9])
Cd= Slider(axCd, 'Cd',    bounds[10][0],bounds[10][1], valinit=const[10])
C = Slider(axC , 'C' ,    -200,200, valinit=0)
M = Slider(axM , 'M' ,    0,0.15, valinit=0.03)
'''
def plotting(const):
    r = get_results(const)[1]
    x = range(len(demands))
    plt.figure()
    plt.plot(x,demands,c='b')
    plt.plot(x,r,c='r')
'''

def update(val):
    print "Getting results"
    results = get_results(np.array([Tb.val,A.val,phi.val,Tp.val,Lp.val,a0.val,
                           a1.val,a2.val,a3.val,Cn.val,Cd.val]))
    print "Got results"
    l2.set_ydata((results[1]*M.val)+C.val)
    ax.set_title(str(results[0]))
    fig.canvas.draw_idle()
Tb.on_changed(update)
A.on_changed(update)
phi.on_changed(update)
Tp.on_changed(update)
Lp.on_changed(update)
a0.on_changed(update)
a1.on_changed(update)
a2.on_changed(update)
a3.on_changed(update)
C.on_changed(update)
M.on_changed(update)
Cn.on_changed(update)
Cd.on_changed(update)

plt.show()