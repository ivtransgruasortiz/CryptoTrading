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
import dns
# import datetime
# import pandas as pd
# import numpy as np
# import json
# import matplotlib.pyplot as plt
# import timeit
# import signal
# import threading
# import keyboard
# import pymongo
# import dateutil.parser
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

from utils import sma, ema, lag, percent, rsi, compare_dates, valor_op, assign_serial, tiempo_pausa_new, historic_df, \
    CoinbaseExchangeAuth, buy_sell, pinta_historico, condiciones_buy_sell
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
tiempo_caida_1 = 60 * 60
freq_exec = 0.5
t00 = time.perf_counter()
contador_ciclos = 0
tamanio_listas_min = freq_exec * tiempo_caida_1
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
    lista_last_buy = lista_last_buy[-1]['last_buy']
    lista_last_sell = [9999999]
    trigger = False

### Historico ###
historico = True
if historico:
    cifra_origen = 100
    pag_historic = 100
    hist_df = historic_df(crypto, api_url, auth, system, cifra_origen, pag_historic, version='old',
                          hist_new=True)  # OLD representa mejor
    # pinta_historico(hist_df, crypto)
    ordenes = hist_df[['bids', 'asks', 'sequence']].to_dict(orient='records')
else:
    ordenes = []

### Inicializacion ###
time.sleep(1)

while True:
    try:
        t0 = time.perf_counter()
        tiempo_transcurrido = time.perf_counter() - t00

        ### BidAsk ###
        try:
            bidask = rq.get(api_url + 'products/' + crypto + '/book?level=1')
            bidask = bidask.json()
            ordenes.append(bidask)
            precio_compra_bidask = float(ordenes[-1]['bids'][0][0])
            precio_venta_bidask = float(ordenes[-1]['asks'][0][0])
        except:
            pass

        ### Limitacion tamaño lista ###
        if len(ordenes) > tamanio_listas_min:
            ordenes.pop(0)

        ### FONDOS_DISPONIBLES ##
        account = rq.get(api_url + 'accounts', auth=auth)
        account = account.json()
        disp_ini = {}
        for item in account:
            disp_ini.update({item['currency']: float(item['available'])})
        eur = math.trunc(disp_ini['EUR']*100)/100
        crypto_quantity = math.trunc(disp_ini[crypto_short]*100)/100

        # ### Tamanio ordenes para LIMIT###
        # size_order_bidask = math.trunc((eur*(1-fees)/precio_venta_bidask)*100)/100

        # ### Condiciones para compra-venta ###
        # condiciones_compra = False #trigger_compra_venta(disponibilidad_fondos y on_off_compra_venta), tamaño_listas, condicionales_precios
        # condiciones_venta = False #trigger_compra_venta, condicionales_para_venta(velocidad_subida estancada y margen_beneficios)

        ### COMPRAS ###
        if condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                                tiempo_caida_1, ordenes_lanzadas, 'buy', trigger, freq_exec, ordenes,
                                lista_last_buy)[0]:
            # buy_sell('buy', crypto, 'limit', api_url, auth, size_order_bidask, precio_venta_bidask) ## LIMIT
            buy_sell('buy', crypto, 'market', api_url, auth, eur) ## MARKET
            lista_last_buy.append(precio_venta_bidask)
            trigger = False
            print('COMPRA!!!')
            ### BBDD
            records = db.ultima_compra_records
            records.remove()
            records.insert_one({'last_buy': precio_venta_bidask})

            # #new fills no por ahora...
            # account = rq.get(api_url + 'fills?product_id=' + crypto, auth=auth)
            # account.json()
            # #fin new
            ### Tamanio ordenes ###
            # last_size_order_bidask = size_order_bidask

        ### ORDENES_LANZADAS ###
        try:
            # r = rq.get(api_url + 'products/' + crypto + '/trades?before=1&limit=2', auth=auth)
            ordenes_lanzadas = rq.get(api_url + 'orders', auth=auth)
            try:
                ordenes_lanzadas = ordenes_lanzadas.json()
            except:
                pass
        except:
            pass

        ### VENTAS ###
        if condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                                tiempo_caida_1, ordenes_lanzadas, 'sell', trigger, freq_exec, ordenes,
                                lista_last_buy)[0]:
            ### FONDOS_DISPONIBLES ###
            account = rq.get(api_url + 'accounts', auth=auth)
            account = account.json()
            disp_ini = {}
            for item in account:
                disp_ini.update({item['currency']: float(item['available'])})
            funds_disp = math.trunc(disp_ini[crypto_short] * precio_compra_bidask * 100) / 100

            # buy_sell('sell', crypto, 'limit', api_url, auth, last_size_order_bidask, precio_compra_bidask) ## LIMIT
            buy_sell('sell', crypto, 'market', api_url, auth, funds_disp) ## MARKET
            lista_last_sell.append(precio_compra_bidask)
            trigger = False ## cambiar a 1 cuando metamos las condiciones
            print('VENTA!!!')
            ### BBDD
            records = db.ultima_compra_records
            records.remove()

        ### CALCULO PAUSAS ###
        contador_ciclos += 1  ## para poder comparar hacia atrśs freq*time_required = num_ciclos hacia atras
        time.sleep(tiempo_pausa_new(time.perf_counter() - t0, freq_exec))
        # print(contador_ciclos)
        if contador_ciclos % 60 == 0:
            print(contador_ciclos)
            print(precio_compra_bidask)
            print(precio_venta_bidask)
            print(condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1, porcentaje_beneficio_1,
                                tiempo_caida_1, ordenes_lanzadas, 'buy', trigger, freq_exec, ordenes,
                                lista_last_buy)[0])
            print(condiciones_buy_sell(precio_compra_bidask, precio_venta_bidask, porcentaje_caida_1,
                                       porcentaje_beneficio_1,
                                       tiempo_caida_1, ordenes_lanzadas, 'sell', trigger, freq_exec, ordenes,
                                       lista_last_buy)[0])

    except (KeyboardInterrupt, SystemExit):  # ctrl + c
        print('All done')
        break
