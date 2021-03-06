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
import pandas as pd
import numpy as np
import time
import datetime
import json
import matplotlib.pyplot as plt
import requests as rq
import hmac, hashlib, base64
from requests.auth import AuthBase
import datetime as dt
from scipy import stats
import tqdm
import dateutil.parser
from statistics import mean
import math
# import sys
# import os
# import datetime
# import timeit
# import scipy
# import tables
# import matplotlib as mpl
# import csv
# import lxml
# import urllib
# import statsmodels
# import math
# import pylab as pl
# import seaborn as sns
# import pylab
# from pandas.tools.plotting import scatter_matrix
# import sklearn
# import nltk
# from pandas_datareader import wb, DataReader
# import wget
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

def tiempo_pausa_new(exec_time, freq):
    """
    FUNCION de usuario que nos da la pausa que debe
    tener un programa para ejecutar algo según una frecuencia
    preestablecida p. ejemplo 1/3 (3 ciclos por segundo) etc... al princicipio del blucle se reinicia la variable inicio now()
    """
    pausa = 1/freq - exec_time
    if pausa < 0:
        pausa = 0
        print("la ejecución va ralentizada, hay que disminuir la frecuencia de ejecucion")
    return pausa

def disposiciones_iniciales(api_url, auth):
    try:
        account = rq.get(api_url + 'accounts', auth=auth)
        account = account.json()
        disp_ini = {}
        for item in account:
            disp_ini.update({item['currency']: float(item['available'])})
    except:
        pass
    return disp_ini

def porcentaje_variacion_inst(lista_hist, precio_instantaneo, tiempo_caida, freq_exec):
    '''
    :param lista_hist: lista de precios de referencia
    :param precio_instantaneo: precio instantaneo
    :param tiempo_caida: tiempo en segundos sobre el que calcular la variacion
    :param freq_exec: freq. ejecucion
    :return: porcentaje en % de variacion
    '''
    porcentaje = math.trunc(((precio_instantaneo - lista_hist[-int(tiempo_caida * freq_exec)])
                             / lista_hist[-int(tiempo_caida * freq_exec)] * 100) * 100) / 100
    return porcentaje

def stoploss(lista_last_buy, precio_instantaneo, porcentaje_limite_stoploss, nummax):
    if (lista_last_buy[-1] != nummax) \
            & (precio_instantaneo < (lista_last_buy[-1] * (1 - porcentaje_limite_stoploss))):
        stop = True
    else:
        stop = False
    return stop

def condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                         tiempo_caida_1, ordenes_lanzadas, tipo, trigger, freq_exec, ordenes, last_buy,
                         medias_exp_rapida_bids, medias_exp_lenta_bids, medias_exp_rapida_asks, medias_exp_lenta_asks,
                         indicador_tiempo_de_gracia, hist_df):
    ciclos_1 = int(freq_exec * tiempo_caida_1)
    ciclos_media = 10
    if indicador_tiempo_de_gracia:
        dif_ahora = datetime.datetime.now() - datetime.timedelta(seconds=tiempo_caida_1)
        media_prev = hist_df[pd.to_datetime(hist_df['time']).apply(lambda x: x.replace(tzinfo=None)) > dif_ahora]
        media_prev = media_prev[['bids', 'asks', 'sequence']]
        media_prev = media_prev.to_dict('records')
        media_prev = media_prev[:10]
    else:
        media_prev = ordenes[-ciclos_media-ciclos_1:-ciclos_1]
    try:
        media_prev_float = mean([float(x['asks'][0][0]) for x in media_prev])
    except:
        media_prev_float = round(float(ordenes[-ciclos_1]['asks'][0][0]), 2)
    condicion_media_compra = medias_exp_rapida_asks[-1] > medias_exp_lenta_asks[-1]
    condicion_media_venta = medias_exp_rapida_bids[-1] < medias_exp_lenta_bids[-1]
    if (tipo == 'buy') & (trigger) & (ordenes_lanzadas == []) & condicion_media_compra & \
            (precio_venta_bidask < float(media_prev_float) * (1 - porcentaje_caida_1)):
        condicion = True
        precio = precio_venta_bidask
        print('buy')
    elif (tipo == 'sell') & (not trigger) & (ordenes_lanzadas == []) & condicion_media_venta & \
            (precio_compra_bidask > last_buy[-1] * (1 + porcentaje_beneficio_1)):
        condicion = True
        precio = precio_compra_bidask
        print('sell')
    else:
        condicion = False
        precio = None
    return [condicion, precio]

def buy_sell(compra_venta, crypto, tipo, api_url, auth, sizefunds=None, precio=None):
    '''
        :param compra_venta: 'buy' or 'sell'
        :param crypto: El producto de que se trate
        :param sum_conditions: True or False, trigger para el lanzamiento si se cumplen condiciones
        :param size_order_bidask: tamaño orden
        :param precio_venta_bidask: precio al que se quiere comprar
        :param tipo: market or limit, por defecto, limit (market es para no especificar precio)
        :param api_url: url de conexion
        :param auth: auth de conexion
        :return:
    '''

    if tipo == 'limit':
        size_or_funds = 'size'
    elif tipo == 'market':
        size_or_funds = 'funds'
    if compra_venta == 'buy':
        order = {
            'type': tipo,
            size_or_funds: sizefunds,
            "price": precio,
            "side": compra_venta,
            "product_id": crypto
        }
    elif compra_venta == 'sell':
        order = {
            'type': tipo,
            size_or_funds: sizefunds,
            "price": precio,
            "side": compra_venta,
            "product_id": crypto
        }
    try:
        # r = rq.post(api_url + 'orders', json=order_buy, auth=auth) ##old
        r = rq.post(api_url + 'orders', data=json.dumps(order), auth=auth)
        ordenes = r.json()
    except:
        time.sleep(0.1)
        ordenes = []
        print('error')
        pass
    return ordenes

def historic_df(crypto, api_url, auth, pag_historic):
    vect_hist = {}
    df_new = pd.DataFrame()
    print('### Gathering Data... ')
    r = rq.get(api_url + 'products/' + crypto + '/trades', auth=auth)
    enlace = r.headers['Cb-After']
    trades = [{'bids': [[float(x['price']), float(x['size']), 1]],
                        'asks': [[float(x['price']), float(x['size']), 1]],
                        'sequence': x['trade_id'],
                        'time': x['time']} for x in r.json()]
    for i in tqdm.trange(pag_historic):
        r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' % enlace, auth=auth)
        time.sleep(0.3)
        enlace = r.headers['Cb-After']
        valores = r.json()
        # trades = trades + [float(x['price']) for x in r.json()]
        trades += [{'bids': [[float(x['price']), float(x['size']), 1]],
                'asks': [[float(x['price']), float(x['size']), 1]],
                'sequence': x['trade_id'],
                'time': x['time']} for x in r.json()]
    df_new = pd.DataFrame.from_dict(trades)
    hist_df = df_new.sort_values('time')
    return hist_df

def sma(n, datos):
    if (len(datos) > n):
        media = sum(datos[-n:]) / n
        return round(media, 5)
    else:
        return round(datos[0], 5)

def ema(n, datos, alpha, media_ant):
    if len(datos) > n:
        expmedia = datos[-1] * alpha + (1 - alpha) * media_ant[-1]
        return round(expmedia, 5)
    else:
        return round(datos[0], 5)

def medias_exp(bids_asks, n_rapida=60, n_lenta=360):
    '''
    :param bids_asks: lista de valores sobre los que calcular las medias exponenciales
    :param n_rapida: periodo de calculo media rapida-nerviosa
    :param n_lenta: periodo de calculo media lenta-tendencia
    :return: lista de listas de valores correspondientes a las medias rapida y lenta
    '''
    mediavar_rapida = []
    mediavar_lenta = []
    expmediavar_rapida = []
    expmediavar_lenta = []
    for i in range(len(bids_asks)):
        mediavar_rapida.append(sma(n_rapida, bids_asks[:i+1]))
        mediavar_lenta.append(sma(n_lenta, bids_asks[:i+1]))
        if len(expmediavar_rapida) <= n_rapida+1:
            expmediavar_rapida.append(mediavar_rapida[-1])
        else:
            expmediavar_rapida.append(ema(n_rapida, bids_asks[:i+1], 2.0/(n_rapida+1), expmediavar_rapida))

        if len(expmediavar_lenta) <= n_lenta+1:
            expmediavar_lenta.append(mediavar_lenta[-1])
        else:
            expmediavar_lenta.append(ema(n_lenta, bids_asks[:i+1], 2.0/(n_lenta+1), expmediavar_lenta))
    return[expmediavar_rapida, expmediavar_lenta]

def df_medias_bids_asks(bids_asks, crypto, fechas, n_rapida=60, n_lenta=360):
    '''
    :param bids_asks: lista para formar el dataframe
    :param crypto: moneda
    :param fechas: lista fechas
    :param n_rapida: parametros medias para calculos medias exponenciales
    :param n_lenta: parametros medias para calculos medias exponenciales
    :return:
    '''
    df_bids_asks = pd.DataFrame(fechas)
    df_bids_asks['expmedia_rapida'] = medias_exp(bids_asks, n_rapida, n_lenta)[0]
    df_bids_asks['expmedia_lenta'] = medias_exp(bids_asks, n_rapida, n_lenta)[1]
    df_bids_asks[crypto] = bids_asks
    df_bids_asks['time'] = fechas
    return df_bids_asks


def limite_tamanio(tamanio_listas_min, factor_tamanio, lista_a_limitar):
    if len(lista_a_limitar) > tamanio_listas_min * factor_tamanio:
        lista_a_limitar.pop(0)
    return lista_a_limitar

def pintar_grafica(df, crypto):
    '''
    :param df: dataframe a pintar con columnas (fecha, valores1, valores2)
    :param crypto: Moneda
    :return: grafica
    '''
    fig2 = plt.figure(2)
    ax2 = fig2.add_subplot(111)
    plt.plot(df['time'].values, df[crypto], label=crypto)
    ax2.plot(df['time'].values, df['expmedia_rapida'], label='expmedia_rapida')
    ax2.plot(df['time'].values, df['expmedia_lenta'], label='expmedia_lenta')
    ax2.legend()
    plt.xticks(rotation='45')
    plt.show()

#################3
##### OLD #####
#################3
def pinta_historico(hist_df, crypto):
    ## PERCENTILES
    #
    percent_sup = 70
    percent_inf = 100 - percent_sup
    lim_sup_1 = stats.scoreatpercentile(hist_df[crypto], percent_sup)
    lim_inf_1 = stats.scoreatpercentile(hist_df[crypto], percent_inf)
    p70 = stats.scoreatpercentile(hist_df[crypto], 70)
    p50 = stats.scoreatpercentile(hist_df[crypto], 50)
    p30 = stats.scoreatpercentile(hist_df[crypto], 30)
    p10 = stats.scoreatpercentile(hist_df[crypto], 10)
    fig1 = plt.figure(1)
    plt.hist(hist_df[crypto], bins=55)
    plt.show()
    print('\nLimite PRINCIPAL para limitar operaciones en  P%s = %s eur.' % (percent_sup, lim_sup_1))
    print('\nLimite SECUNDARIO para limitar operaciones en P%s = %s eur.' % (percent_inf, lim_inf_1))

    ### CALCULO MEDIAS MOVILES EXPONENCIALES - EMA'S
    mediavar_rapida = []
    mediavar_lenta = []
    expmediavar_rapida = []
    expmediavar_lenta = []
    n_rapida = 10
    n_lenta = 20
    for i in range(len(hist_df[crypto])):
        mediavar_rapida.append(sma(n_rapida, hist_df[crypto].values[:i + 1]))
        mediavar_lenta.append(sma(n_lenta, hist_df[crypto].values[:i + 1]))
        if len(expmediavar_rapida) <= n_rapida + 1:
            expmediavar_rapida.append(mediavar_rapida[-1])
        else:
            expmediavar_rapida.append(
                ema(n_rapida, hist_df[crypto].values[:i + 1], 2.0 / (n_rapida + 1), expmediavar_rapida))

        if len(expmediavar_lenta) <= n_lenta + 1:
            expmediavar_lenta.append(mediavar_lenta[-1])
        else:
            expmediavar_lenta.append(
                ema(n_lenta, hist_df[crypto].values[:i + 1], 2.0 / (n_lenta + 1), expmediavar_lenta))

    ### ADD COLUMNS TO DATAFRAME
    hist_df['expmedia_rapida'] = expmediavar_rapida
    hist_df['expmedia_lenta'] = expmediavar_lenta

    ## PLOT TRADES AND EMA'S
    fig2 = plt.figure(2)
    ax2 = fig2.add_subplot(111)
    ax2.plot(hist_df[crypto], label=crypto)
    ax2.plot(hist_df['expmedia_rapida'], label='expmedia_rapida')
    ax2.plot(hist_df['expmedia_lenta'], label='expmedia_lenta')
    ax2.legend()
    plt.xticks(rotation='45')
    plt.show()

def lag(n, df):
    for i in range(n):
        df['lag_%s' % (i + 1)] = df['ltc_eur'].shift(i) - df['ltc_eur'].shift(i + 1)

def percent(p_ini, p_fin):
    percen = (p_fin - p_ini) / abs(p_ini)
    return percen

def rsi(n, df1):
    u = []
    d = []
    for i in range(1, len(df1)):
        if df1[i] >= 0:
            u.append(df1[i])
        else:
            d.append(df1[i])
    sumapos = sum(u)
    sumneg = sum(d)
    if (sumneg != 0):
        rs = abs(sumapos / sumneg)
        rsi_index = 100 - (100 / (1 + rs))
    else:
        rsi_index = 100
    return rsi_index

def compare_dates(df, fecha_inicio, fecha_final):
    valor = []
    for item in df:
        try:
            valor.append(time.strptime(item, '%Y-%m-%dT%H:%M:%S.%fZ') >= fecha_inicio) and (
                    time.strptime(item, '%Y-%m-%dT%H:%M:%S.%fZ') <= fecha_final)
        except:
            valor.append(time.strptime(item, '%Y-%m-%dT%H:%M:%SZ') >= fecha_inicio) and (
                    time.strptime(item, '%Y-%m-%dT%H:%M:%SZ') <= fecha_final)
    return valor

def valor_op(side, size, price, fee):
    if side == 'buy':
        signo = -1
    elif side == 'sell':
        signo = 1
        fee = -float(fee)
    valor = signo * (float(size) * float(price) + float(fee))
    return valor

def assign_serial(id_number, serial_dicc, seriales):
    if id_number in serial_dicc.keys():
        valor = seriales[id_number]
    else:
        valor = 0
    return valor

# def tiempo_pausa(inicio, freq):
#     """
#     FUNCION de usuario que nos da la pausa que debe
#     tener un programa para ejecutar algo según una frecuencia
#     preestablecida p. ejemplo 1/3 (3 ciclos por segundo) etc... al princicipio del bucle se reinicia la variable inicio now()
#     """
#     from datetime import datetime
#     fin = datetime.now()
#     dif_seconds = (fin - inicio).seconds + (fin - inicio).microseconds * 1e-6
#     pausa = freq - dif_seconds
#     if pausa < 0:
#         pausa = 0
#         print("la ejecución va ralentizada, hay que disminuir la frecuencia de ejecucion")
#     print(pausa)
#     return pausa

# def imprime(cadena):
#     return print(cadena)
