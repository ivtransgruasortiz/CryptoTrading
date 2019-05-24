#!/usr/bin/python2.7
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
sys.stdout.flush()
if sys.platform == 'win32':
    path = 'C:\\Users\\ivan.ortiz\\Documents\\MisProgramas_Iv_PYTHON\\CRIPTOMONEDAS\\'
    print ('\n#### Windows System ####')
    system = sys.platform
else:
    path = '/home/iv/Desktop/MasterBIGDATA/CRIPTOMONEDAS/'
    print ('\n#### Linux System ####')
    system = sys.platform

print('\n' + sys.platform + ' System\n')
print ('#####################################')
print ('#####################################')
print ('\n### Importing Libraries... ###')

import time
import datetime
import pandas as pd
import numpy as np
import csv
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import lxml
import urllib
import statsmodels
import requests as rq
import scipy
import tables
import hmac, hashlib, base64
from requests.auth import AuthBase
import datetime as dt
import timeit
from scipy import stats
import tqdm
#import math
#import pylab as pl
#import seaborn as sns
#import pylab
#from pandas.tools.plotting import scatter_matrix
#import sklearn
#import nltk
#from pandas_datareader import wb, DataReader
#import wget

hora_ejecucion = 12 # time to stop and restart en utc --- +1 invierno +2 verano
minuto_ejecucion = 55
hora_inicio = datetime.datetime.utcnow()
crypto = 'BTC-EUR'
###########################################################################################
## Create custom authentication for Exchange #############################################
#########################################################################################
#######################################################################
## CUENTA REAL - ACTIVAR PARA HACER TRANSFER REALES ##################
#####################################################################
print('\n### Authenticating... ###')
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message, hashlib.sha256)
#        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        signature_b64 = signature.digest().encode('base64').rstrip('\n')
#        signature_b64 = base64.b64encode(signature.digest()).decode()

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request
api_url = 'https://api.pro.coinbase.com/' ## la real
kiko = '' #sys.argv[1] # text
sandra = '' #sys.argv[2] # text
pablo = '' #sys.argv[3] # text
auth = CoinbaseExchangeAuth(kiko, sandra, pablo)
#######################################################################
#######################################################################

#######################################################################
## FIN CUENTA REAL ###################################################
#####################################################################

######################################################################
## GET ACCOUNTS #####################################################
####################################################################
account = rq.get(api_url + 'accounts', auth=auth)
print (account.json())
account1 = account.json()
# Disp_iniciales
disp_ini = {}
for item in account1:
    disp_ini.update({item['currency']:item['available']})
######################################################################
### FUNCIONES #######################################################
####################################################################
print ('\n### Defining functions... ###')

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
        valor.append(time.strptime(item,'%Y-%m-%dT%H:%M:%S.%fZ')>=fecha_inicio)and(time.strptime(item,'%Y-%m-%dT%H:%M:%S.%fZ')<=fecha_final)
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
###############################################################################
##############################################################################

######################################################################
##### INICIO tramo para datos anteriores ###########################
###################################################################
vect_hist = {}
cifra_origen = 1000000
final1 = 0
comp = False
cont = 0
pag_historic = 3000 #1000
print ('### Gathering Data... ')
b = pd.DataFrame()
for i in tqdm.tqdm([10000000,1000000,100000,10000,1000,100]):
    while comp == False:
        r = rq.get(api_url + 'products/'+ crypto +'/trades?after=%s' %(cifra_origen+cont*i), auth = auth) # va de 100 en 100
        try:
            origen1 = [x['trade_id'] for x in r.json()]
        except:
            continue
        final = origen1[0]
        comp = (final == final1)
        coincide = cont-1
        final1 = final
        cont += 1

    cifra_origen=cifra_origen + (coincide-1)*i
    cont=0
    comp = False

if system == 'linux2':
    for i in tqdm.trange (pag_historic): # 200  SON UNOS 12 DIAS APROX
        r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' %(cifra_origen+coincide*100-i*100), auth = auth)
        try:
            a = [x for x in r.json()]
            a2 = pd.DataFrame(a)
            b = b.append(a2)
        except:
            continue

hist_df = b.sort_values('trade_id', ascending = True)
hist_df.to_csv('btc_tot.csv', sep = ',')




