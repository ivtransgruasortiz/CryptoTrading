#!/usr/bin/python3.5
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  6 19:22:32 2017
@author: iv
"""
###############################
## SELECT PLATFORM: ##########
#############################
###-- WINDOWS OR LINUX --###
###########################
import sys
import os
import time
import datetime
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import requests as rq
import hmac, hashlib, base64
from requests.auth import AuthBase
import datetime as dt
from scipy import stats
import tqdm
import timeit
import scipy
import tables
import matplotlib as mpl
import csv
import lxml
import urllib
import statsmodels
#import math
#import pylab as pl
#import seaborn as sns
#import pylab
#from pandas.tools.plotting import scatter_matrix
#import sklearn
#import nltk
#from pandas_datareader import wb, DataReader
#import wget

def sma(n,datos):
    if (len(datos) > n):
        media = sum(datos[-n:])/n
        return media
    else:
        return datos[0]

def ema(n,datos,alpha,media_ant):
    if len(datos) > n:
        expmedia = datos[-1]*alpha+(1-alpha)*media_ant[-1]
        return expmedia
    else:
        return datos[0]

def lag(n, df):
    for i in range(n):
        df['lag_%s' %(i+1)] = df['ltc_eur'].shift(i) - df['ltc_eur'].shift(i+1)

def percent(p_ini,p_fin):
    percen = (p_fin-p_ini)/abs(p_ini)
    return percen

def rsi(n,df1):
    u = []
    d = []
    for i in range(1,len(df1)):
        if df1[i]>=0:
            u.append(df1[i])
        else:
            d.append(df1[i])
    sumapos = sum(u)
    sumneg = sum(d)
    if (sumneg != 0):
        rs = abs(sumapos/sumneg)
        rsi_index = 100 - (100/(1+rs))
    else:
        rsi_index = 100
    return rsi_index

def compare_dates(df,fecha_inicio,fecha_final):
    valor = []
    for item in df:
        try:
            valor.append(time.strptime(item,'%Y-%m-%dT%H:%M:%S.%fZ')>=fecha_inicio)and(time.strptime(item,'%Y-%m-%dT%H:%M:%S.%fZ')<=fecha_final)
        except:
            valor.append(time.strptime(item,'%Y-%m-%dT%H:%M:%SZ')>=fecha_inicio)and(time.strptime(item,'%Y-%m-%dT%H:%M:%SZ')<=fecha_final)
    return valor

def valor_op(side,size,price,fee):
    if side == 'buy':
        signo = -1
    elif side == 'sell':
            signo = 1
            fee = -float(fee)
    valor = signo*(float(size)*float(price)+float(fee))
    return valor

def assign_serial(id_number, serial_dicc):
    if id_number in serial_dicc.keys():
        valor = seriales[id_number]
    else:
        valor = 0
    return valor