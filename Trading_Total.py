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
import requests as rq
import math
import pymongo
import dateutil.parser
import datetime
from statistics import mean
import dns
# import datetime
import pandas as pd
# import numpy as np
# import json
import matplotlib.pyplot as plt
# import timeit
# import signal
# import threading
# import keyboard
# import pymongo
# import hmac, hashlib, base64
# from requests.auth import AuthBase
# import datetime as dt
# from scipy import stats
# import tqdm

sys.stdout.flush() #Para cambiar el comportamiento de los print -- sin esta línea los escribe del tirón...

### SYSTEM DATA ###
#
if '__file__' in locals():
    wd = os.path.dirname(__file__)
    sys.path.append(wd)
else:
    wd = os.path.abspath("./Documents/Repositorio_Iv/CryptoTrading/")
    wd = wd + '/'
    sys.path.append(wd)
if sys.platform == 'win32':
    system = sys.platform
else:
    system = sys.platform

from utils import sma, ema, lag, percent, rsi, compare_dates, valor_op, assign_serial, tiempo_pausa_new, \
    CoinbaseExchangeAuth, buy_sell, pinta_historico, condiciones_buy_sell, medias_exp, df_medias_bids_asks, \
    pintar_grafica, limite_tamanio, historic_df
import yaml

## Importar datos-configuraciones-funciones
try:
    with open('config.yaml', 'r') as config_file:
        doc = yaml.safe_load(config_file)
except:
    pass

print('#####################################')
print(sys.platform + ' System')
print('#####################################')
print('\n### Importing Libraries... ###')

# ### AUTHENTICATION INTO COINBASE ###
print('\n### Authenticating into CoinbasePro... ###')
try:
    auth = CoinbaseExchangeAuth(doc['Credentials'][0], doc['Credentials'][1], doc['Credentials'][2])
except:
    auth = CoinbaseExchangeAuth(sys.argv[1], sys.argv[2], sys.argv[3])

# ### AUTHENTICATION INTO MongoDB-Atlas ###
print('\n### Authenticating into MongoDB-Atlas... ###')
try:
    client = pymongo.MongoClient(
        "mongodb+srv://%s:%s@cluster0.vsp3s.mongodb.net/%s?retryWrites=true&w=majority"
        % (doc['Credentials'][3], doc['Credentials'][4], doc['Credentials'][5]))
    db = client.get_database(doc['Credentials'][5])
except:
    client = pymongo.MongoClient(
        "mongodb+srv://%s:%s@cluster0.vsp3s.mongodb.net/%s?retryWrites=true&w=majority"
        % (sys.argv[4], sys.argv[5], sys.argv[6]))
    db = client.get_database(sys.argv[6])

### GET ACCOUNTS ###
crypto = "LTC-EUR"
crypto_short = crypto.split('-')[0]
api_url = 'https://api.pro.coinbase.com/'

### Disp_iniciales ###
account = rq.get(api_url + 'accounts', auth=auth)
account = account.json()
disp_ini = {}
for item in account:
    disp_ini.update({item['currency']: float(item['available'])})

### fees ###
fees = rq.get(api_url + 'fees', auth=auth)
fees = round(float('%.4f' % (float(fees.json()['taker_fee_rate']))), 4)

####################################################
### START REAL-TIME TRADING #######################
##################################################
print('\n### Data OK! ###')
print('\n### Real-Time Processing... ### - \nPress CTRL+C (QUICKLY 2-TIMES!!) to cancel and view results')

### INITIAL RESET FOR VARIABLES ###
porcentaje_caida_1 = 0.05
porcentaje_beneficio_1 = 0.02
tiempo_caida_1 = 120 * 60  # en segundos... (180 minutos)
freq_exec = 0.5
contador_ciclos = 0
tamanio_listas_min = freq_exec * tiempo_caida_1
factor_tamanio = 100
ordenes_lanzadas = []
# size_order_bidask = 0.1 ## Para LIMIT

### Lectura BBDD-Last_Buy ###
records = db.ultima_compra_records
lista_last_buy = list(records.find({}, {"_id": 0}))  # Asi omitimos el _id que por defecto nos agrega mongo
if lista_last_buy == []:
    lista_last_buy = [9999999]
    lista_last_sell = [9999999]
    trigger = True
else:
    lista_last_buy = [lista_last_buy[-1]['last_buy']]
    lista_last_sell = [9999999]
    trigger = False

### Historico ###
historico = True
if historico:
    pag_historic = 50
    hist_df = historic_df(crypto, api_url, auth, pag_historic)
    ordenes = hist_df[['bids', 'asks', 'sequence']].to_dict(orient='records')
else:
    ordenes = []

### MEDIAS EXP HISTORICAS ###
bids = [x[0][0] for x in list(hist_df['bids'].values)]
asks = [x[0][0] for x in list(hist_df['asks'].values)]
fechas = [dateutil.parser.parse(x) for x in hist_df['time']]

# ### PINTAR GRAFICAS ###
# pintar_grafica(df_medias_bids_asks(asks, crypto, fechas, 60, 360), crypto)

### Inicializacion y medias_exp ###
n_rapida_bids = 120
n_lenta_bids = 420
n_rapida_asks = 60
n_lenta_asks = 360
medias_exp_rapida_bids = [medias_exp(bids, n_rapida_bids, n_lenta_bids)[0][-1]]
medias_exp_lenta_bids = [medias_exp(bids, n_rapida_bids, n_lenta_bids)[1][-1]]
medias_exp_rapida_asks = [medias_exp(asks, n_rapida_asks, n_lenta_asks)[0][-1]]
medias_exp_lenta_asks = [medias_exp(asks, n_rapida_asks, n_lenta_asks)[1][-1]]

time.sleep(5)
t00 = time.perf_counter()

while True:
    try:
        t0 = time.perf_counter()
        tiempo_transcurrido = time.perf_counter() - t00
        if tiempo_transcurrido < tiempo_caida_1:
            indicador_tiempo_de_gracia = True
        else:
            indicador_tiempo_de_gracia = False
        ### BidAsk ###
        try:
            bidask = rq.get(api_url + 'products/' + crypto + '/book?level=1')
            bidask = bidask.json()
            ordenes.append(bidask)
            precio_compra_bidask = float(ordenes[-1]['bids'][0][0])
            precio_venta_bidask = float(ordenes[-1]['asks'][0][0])
        except:
            pass
        ### Actualizacion listas precios y medias_exp ###
        bids.append(precio_compra_bidask)
        asks.append(precio_venta_bidask)
        medias_exp_rapida_bids.append(ema(n_rapida_bids, bids, 2.0 / (n_rapida_bids + 1), medias_exp_rapida_bids))
        medias_exp_lenta_bids.append(ema(n_lenta_bids, bids, 2.0 / (n_lenta_bids + 1), medias_exp_lenta_bids))
        medias_exp_rapida_asks.append(ema(n_rapida_asks, asks, 2.0 / (n_rapida_asks + 1), medias_exp_rapida_asks))
        medias_exp_lenta_asks.append(ema(n_lenta_asks, asks, 2.0 / (n_lenta_asks + 1), medias_exp_lenta_asks))
        ### Limitacion tamaño lista ###
        bids = limite_tamanio(tamanio_listas_min, factor_tamanio, bids)
        asks = limite_tamanio(tamanio_listas_min, factor_tamanio, asks)
        medias_exp_rapida_bids = limite_tamanio(tamanio_listas_min, factor_tamanio, medias_exp_rapida_bids)
        medias_exp_lenta_bids = limite_tamanio(tamanio_listas_min, factor_tamanio, medias_exp_lenta_bids)
        medias_exp_rapida_asks = limite_tamanio(tamanio_listas_min, factor_tamanio, medias_exp_rapida_asks)
        medias_exp_lenta_asks = limite_tamanio(tamanio_listas_min, factor_tamanio, medias_exp_lenta_asks)
        ### FONDOS_DISPONIBLES ##
        try:
            account = rq.get(api_url + 'accounts', auth=auth)
            account = account.json()
            disp_ini = {}
            for item in account:
                disp_ini.update({item['currency']: float(item['available'])})
            eur = math.trunc(disp_ini['EUR']*100)/100
            crypto_quantity = math.trunc(disp_ini[crypto_short]*100)/100
        except:
            pass
        ### COMPRAS ###
        if condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                                tiempo_caida_1, ordenes_lanzadas, 'buy', trigger, freq_exec, ordenes,
                                lista_last_buy, medias_exp_rapida_bids, medias_exp_lenta_bids, medias_exp_rapida_asks,
                                medias_exp_lenta_asks, indicador_tiempo_de_gracia, hist_df)[0]:
            ### Orden de Compra ###
            try:
                # buy_sell('buy', crypto, 'limit', api_url, auth, size_order_bidask, precio_venta_bidask) ## LIMIT
                buy_sell('buy', crypto, 'market', api_url, auth, eur) ## MARKET
                lista_last_buy.append(precio_venta_bidask)
                trigger = False
                print('COMPRA!!!')
                print(ordenes[-int(tiempo_caida_1*freq_exec)])
                ### BBDD
                records = db.ultima_compra_records
                records.remove()
                records.insert_one({'last_buy': precio_venta_bidask, 'fecha': datetime.datetime.now().isoformat(),
                                    'precio_anterior': str(ordenes[-int(tiempo_caida_1*freq_exec)]['asks'])})
            except:
                pass
        ### ORDENES_LANZADAS ###
        try:
            # r = rq.get(api_url + 'products/' + crypto + '/trades?before=1&limit=2', auth=auth)
            ordenes_lanzadas = rq.get(api_url + 'orders', auth=auth)
            ordenes_lanzadas = ordenes_lanzadas.json()
        except:
            pass
        ### VENTAS ###
        if condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                                tiempo_caida_1, ordenes_lanzadas, 'sell', trigger, freq_exec, ordenes,
                                lista_last_buy, medias_exp_rapida_bids, medias_exp_lenta_bids, medias_exp_rapida_asks,
                                medias_exp_lenta_asks, indicador_tiempo_de_gracia, hist_df)[0]:
            ### FONDOS_DISPONIBLES ###
            try:
                account = rq.get(api_url + 'accounts', auth=auth)
                account = account.json()
            except:
                pass
            disp_ini = {}
            for item in account:
                disp_ini.update({item['currency']: float(item['available'])})
            funds_disp = math.trunc(disp_ini[crypto_short] * precio_compra_bidask * 100) / 100
            ### Orden de Venta ###
            try:
                # buy_sell('sell', crypto, 'limit', api_url, auth, last_size_order_bidask, precio_compra_bidask) ## LIMIT
                buy_sell('sell', crypto, 'market', api_url, auth, funds_disp) ## MARKET
                lista_last_sell.append(precio_compra_bidask)
                trigger = True
                print('VENTA!!!')
                ### BBDD
                records = db.ultima_compra_records
                records.remove()
            except:
                pass

        ### CALCULO PAUSAS ###
        contador_ciclos += 1  ## para poder comparar hacia atrśs freq*time_required = num_ciclos hacia atras
        time.sleep(tiempo_pausa_new(time.perf_counter() - t0, freq_exec))
        # print(contador_ciclos)
        if contador_ciclos % 60 == 0:
            print(contador_ciclos)
            print(precio_compra_bidask)
            print(precio_venta_bidask)
            print(condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1,
                                       porcentaje_beneficio_1, tiempo_caida_1, ordenes_lanzadas, 'buy', trigger,
                                       freq_exec, ordenes, lista_last_buy, medias_exp_rapida_bids,
                                       medias_exp_lenta_bids, medias_exp_rapida_asks, medias_exp_lenta_asks,
                                       indicador_tiempo_de_gracia, hist_df)[0])
            print(condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1,
                                       porcentaje_beneficio_1, tiempo_caida_1, ordenes_lanzadas, 'sell', trigger,
                                       freq_exec, ordenes, lista_last_buy, medias_exp_rapida_bids,
                                       medias_exp_lenta_bids, medias_exp_rapida_asks, medias_exp_lenta_asks,
                                       indicador_tiempo_de_gracia, hist_df)[0])
    except (KeyboardInterrupt, SystemExit):  # ctrl + c
        print('All done')
        break
### FIN ###

# ### LISTA OPCIONAL ###
# expmediavar_rapida_bidask.append(ema(n_rapida_bidask,precio_bidask, 2.0/(n_rapida_bidask+1), expmediavar_rapida_bidask))
# expmediavar_lenta_bidask.append(ema(n_lenta_bidask,precio_bidask, 2.0/(n_lenta_bidask+1), expmediavar_lenta_bidask))

#
# #new fills no por ahora...
# account = rq.get(api_url + 'fills?product_id=' + crypto, auth=auth)
# account.json()
# #fin new
### Tamanio ordenes ###
# last_size_order_bidask = size_order_bidask

# ### Tamanio ordenes para LIMIT###
# size_order_bidask = math.trunc((eur*(1-fees)/precio_venta_bidask)*100)/100

# ### Condiciones para compra-venta ###
# condiciones_compra = False #trigger_compra_venta(disponibilidad_fondos y on_off_compra_venta), tamaño_listas, condicionales_precios
# condiciones_venta = False #trigger_compra_venta, condicionales_para_venta(velocidad_subida estancada y margen_beneficios)
