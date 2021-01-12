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
# from requests.auth import AuthBase

### AUTHENTICATION INTO COINBASE ###
#
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        # timestamp = datetime.datetime.now().isoformat()
        message = timestamp + str(request.method).upper() + request.path_url + str(request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        # # signature = hmac.new(hmac_key, message, hashlib.sha256)
        signature = hmac.new(hmac_key, message.encode(), hashlib.sha256)
        # signature_b64 = signature.digest().encode('base64').rstrip('\n')
        signature_b64 = base64.b64encode(signature.digest()).decode()

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'})
        return request

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

def assign_serial(id_number, serial_dicc, seriales):
    if id_number in serial_dicc.keys():
        valor = seriales[id_number]
    else:
        valor = 0
    return valor


def imprime(cadena):
    return print(cadena)

def tiempo_pausa(inicio, freq):
    """
    FUNCION de usuario que nos da la pausa que debe
    tener un programa para ejecutar algo según una frecuencia
    preestablecida p. ejemplo 1/3 (3 ciclos por segundo) etc... al princicipio del blucle se reinicia la variable inicio now()
    """
    from datetime import datetime
    fin = datetime.now()
    dif_seconds = (fin - inicio).seconds + (fin - inicio).microseconds * 1e-6
    pausa = freq - dif_seconds
    if pausa < 0:
        pausa = 0
        print("la ejecución va ralentizada, hay que disminuir la frecuencia de ejecucion")
    print(pausa)
    return(pausa)

def historic_df(crypto, api_url, auth, system, cifra_origen, pag_historic, version='old'):
    ### INICIO tramo para datos anteriores ###
    #
    if version == 'old':
        final1 = 0
        comp = False
        cont = 0
        vect_hist = {}
        b = []
        print('### Gathering Data... ')
        for i in tqdm.tqdm([100000000, 10000000, 1000000, 100000, 10000, 1000, 100]):
            while not comp:
                r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' % (cifra_origen + cont * i),
                           auth=auth)  # va de 100 en 100
                try:
                    origen1 = [x['trade_id'] for x in r.json()]
                except:
                    continue
                final = origen1[0]
                comp = (final == final1)
                coincide = cont - 1
                final1 = final
                cont += 1
            cifra_origen = cifra_origen + (coincide - 1) * i
            cont = 0
            comp = False
        if system == 'linux':
            for i in tqdm.trange(pag_historic):  # 200  SON UNOS 12 DIAS APROX
                r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' % (cifra_origen + coincide * 100 - i * 100),
                           auth=auth)
                try:
                    a = [float(x['price']) for x in r.json()]
                except:
                    continue
                for x in r.json():
                    try:
                        b.append(dt.datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
                    except:
                        b.append(dt.datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%SZ'))
                a.reverse()
                b.reverse()
                c = dict(zip(b, a))
                vect_hist.update(c)
        if system == 'win32':
            for i in range(pag_historic):
                r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' % (cifra_origen + coincide * 100 - i * 100),
                           auth=auth)
                try:
                    a = [float(x['price']) for x in r.json()]
                except:
                    continue
                for x in r.json():
                    try:
                        b.append(dt.datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%S.%fZ'))
                    except:
                        b.append(dt.datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%SZ'))
                a.reverse()
                b.reverse()
                c = dict(zip(b, a))
                vect_hist.update(c)
        hist_df = pd.DataFrame.from_dict(vect_hist, orient='index')
        hist_df.columns = [crypto]
        hist_df = hist_df.sort_index(axis=0)
    else:
        r = rq.get(api_url + 'products/' + crypto + '/trades?before=%s&limit=%s' % (pag_historic+1, 100), auth=auth)
        hist_df = {dt.datetime.strptime(x['time'], '%Y-%m-%dT%H:%M:%S.%fZ'): float(x['price']) for x in r.json()}
        hist_df = pd.DataFrame.from_dict(hist_df, orient='index')
        hist_df.columns = [crypto]
        hist_df = hist_df.sort_index(axis=0)
    return hist_df
