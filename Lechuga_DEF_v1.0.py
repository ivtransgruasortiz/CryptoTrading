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
crypto = 'LTC-EUR'
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
        signature_b64 = signature.digest().encode('base64').rstrip('\n')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request
api_url = 'https://api.pro.coinbase.com/' ## la real
kiko = sys.argv[1] # text
sandra = sys.argv[2] # text
pablo = sys.argv[3] # text
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
b = []
final1 = 0
comp = False
cont = 0
pag_historic = 150 #100
print ('### Gathering Data... ')

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
        c = dict(zip(b,a))
        vect_hist.update(c)
if system == 'win32':
    for i in range (pag_historic):
        r = rq.get(api_url + 'products/' + crypto + '/trades?after=%s' %(cifra_origen+coincide*100-i*100), auth = auth)
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
        c = dict(zip(b,a))
        vect_hist.update(c)

hist_df = pd.DataFrame.from_dict(vect_hist, orient = 'index')
hist_df.columns = ['ltc_eur']
hist_df = hist_df.sort_index(axis = 0)

## LIMITS UPPER AND LOWER TO LIMIT OPERATIONS BY STATISTICS
lim_sup = hist_df['ltc_eur'].max()
lim_inf = hist_df['ltc_eur'].min()
## PERCENTILES
percent_sup = 30 # 70
percent_inf = 100 - percent_sup
lim_sup_1 = stats.scoreatpercentile(hist_df['ltc_eur'], percent_sup)
lim_inf_1 = stats.scoreatpercentile(hist_df['ltc_eur'], percent_inf)
p70 = stats.scoreatpercentile(hist_df['ltc_eur'], 70)
p50 = stats.scoreatpercentile(hist_df['ltc_eur'], 50)
p30 = stats.scoreatpercentile(hist_df['ltc_eur'], 30)
p10 = stats.scoreatpercentile(hist_df['ltc_eur'], 10)
fig1 = plt.figure(1)
plt.hist(hist_df['ltc_eur'], bins=55)
plt.show()
print('\nLimite PRINCIPAL para limitar operaciones en  P%s = %s eur.' %(percent_sup, lim_sup_1) )
print('\nLimite SECUNDARIO para limitar operaciones en P%s = %s eur.' %(percent_inf, lim_inf_1) )

### CALCULO MEDIAS MOVILES EXPONENCIALES - EMA'S
mediavar_rapida = []
mediavar_lenta = []
expmediavar_rapida = []
expmediavar_lenta = []
n_rapida = 100
n_lenta = 200
for i in range(len(hist_df['ltc_eur'])):
    mediavar_rapida.append(sma(n_rapida,hist_df['ltc_eur'].values[:i+1]))
    mediavar_lenta.append(sma(n_lenta,hist_df['ltc_eur'].values[:i+1]))
    if len(expmediavar_rapida) <= n_rapida+1:
        expmediavar_rapida.append(mediavar_rapida[-1])
    else:
        expmediavar_rapida.append(ema(n_rapida,hist_df['ltc_eur'].values[:i+1], 2.0/(n_rapida+1), expmediavar_rapida))

    if len(expmediavar_lenta) <= n_lenta+1:
        expmediavar_lenta.append(mediavar_lenta[-1])
    else:
        expmediavar_lenta.append(ema(n_lenta,hist_df['ltc_eur'].values[:i+1], 2.0/(n_lenta+1), expmediavar_lenta))

### ADD COLUMNS TO DATAFRAME
hist_df['expmedia_rapida'] = expmediavar_rapida
hist_df['expmedia_lenta'] = expmediavar_lenta

## PLOT TRADES AND EMA'S
fig2 = plt.figure(2)
ax2 = fig2.add_subplot(111)
ax2.plot(hist_df['ltc_eur'],label='ltc_eur')
ax2.plot(hist_df['expmedia_rapida'],label='expmedia_rapida')
ax2.plot(hist_df['expmedia_lenta'],label='expmedia_lenta')
ax2.legend()
plt.xticks(rotation = '45')
plt.show()
######################################################################
##### FIN tramo datos anteriores ####################################
####################################################################

# ok!

#########################################################
########################################################
### Bucle con interrupt [ctrl+c] válido!!!!! ##########
######################################################
#####################################################
####################################################
### START REAL-TIME TRADING #######################
##################################################
print ('\n### Data OK! ###')
print ('\n### Real-Time Processing... ### - \nPress CTRL+C (QUICKLY 2-TIMES!!) to cancel and view results')

## INITIAL RESET FOR VARIABLES
n_orders = 2 # Para los aleatorios
n_ciclos_to_cancel = 30 #80
ndisparador = 1 #5 ##60 Tiempo en segundos o ciclos entre ordenes de compra #5
disparador1 = ndisparador ## Espaciado entre ordenes compras
n_eur_hold = 100 # 800 # Estaba a 80... es el limite para limitar el numero de compras segun las ordenes de compra emitidas
size_order_bidask = 0.2 # 0.5
porcentaje_beneficio = 1.8 # 0.5 ## En %, es decir 0.6 significa 0.6% que es ademas cantidad recomendada 0.6%
disp = 0 # Para ajustar historico
disp1 = 0 # Para ajustar historico
lim_dif_bidask = 0.03 # Dif_Bidask limite para hacer aleatorios o no.
stop_loss = 0.04
serial_number = 1 # Para relacionar las ordenes de compra-venta

precio=[]
precio_bidask = []
fecha=[]
ltc_price=[]
expmediavar_rapida_bidask = [expmediavar_rapida[-1]]
expmediavar_lenta_bidask = [expmediavar_lenta[-1]]
seg = 0
rango = 'NotDefined'
t_time=[]
trigger1 = 0
n_rapida_bidask = 4 #4 Cantidad recomendada
n_lenta_bidask = 12 #12 Cantidad recomendada
limit_dif_bidask = 0.31 #Diferencia o ǴAP Bid-Ask para lanzar orden compra RECOMENDADA 0.31 - Distinto a LIM_DIF_BIDASK que es para los aleatorios
alpha_rapida_bidask = 2.0/(n_rapida_bidask+1)
alpha_lenta_bidask = 2.0/(n_lenta_bidask+1)
precio_compra_bidask_ejecutado = []
precio_venta_bidask_ejecutado = []
ganancias = []
list_trades_id = []
n_precios_hist = len(hist_df) # Longitud de lista de valores para calcular el hist y actualizar el valor máximo
hist_margin = np.around(list(hist_df['ltc_eur'][-n_precios_hist-1:-1].values),2) # vector de precios pasados al que agregar los nuevos precios y que nos sirva para establecer nuevos límites a la compra...
n_ciclos_to_hist = 50 # 120 estaba inicialmente... número de ciclos para meter ultima orden en hist para calcular limite de operacion
ids_comp_vent = {}
contadores = {}
try:
    f = open('filess_compra.txt','r')
    ordenes_compra = json.load(f)
    if (ordenes_compra != {}):
        print('\nHanging Purchases --> Yes \nDetails: ')
        print('\n')
        print(ordenes_compra)
        print('\n')
    else:
        print('\nHanging Purchases --> No')
        print('\n')

    f.close()
except:
    ordenes_compra = {}
try:
    f = open('filess_venta.txt','r')
    ordenes_venta = json.load(f)
    f.close()
except:
    ordenes_venta = {}

disparador2 = len([x for x in ordenes_compra if ordenes_compra[x]['estado_venta']==''])
seriales = {}
relacion_id_compra_venta = {}
forze_venta=False
plt.ion()

## Fecha y hora inicial del codigo
fecha_ini = datetime.datetime.utcnow()
fecha_ini = unicode(datetime.datetime.strftime(fecha_ini, '%Y-%m-%dT%H:%M:%S.%fZ'))
fecha_ini = time.strptime(fecha_ini, '%Y-%m-%dT%H:%M:%S.%fZ')
## Fecha apertura operaciones hoy
fecha_ininombre = time.strftime("%c")
if system == 'linux2':
    name_fich = 'log_' + fecha_ininombre + '.txt'
else:
    name_fich = 'log.txt'


################################################
### formas de rellenar un diccionario #########
##############################################
## Forma 1
#ordenes = {} # 'id', 'contador', 'precio_compra', 'precio_venta', 'estado_compra', 'estado_venta'
#ordenes['a123asd']={}
#ordenes['a123asd']['id']='a123asd'
#ordenes['a123asd']['precio']=27
### Forma 2
#ordenes = {} # 'id', 'contador', 'precio_compra', 'precio_venta', 'estado_compra', 'estado_venta'
#ordenes['a123asd']={'contador':1}
#ordenes['a123asd'].update({'id_venta':'jue837'})

#########################################################
### formas de escribir en un fichero de texto ##########
#######################################################
#fichero = open(name_fich, 'at')
#fichero.write('\n\n## ATTENTION!!##  SELL order %s EXECUTED in %s eur (for buy-order %s EXECUTED in %s eur)  ##' %(item, ordenes_venta[item]['precio_venta'], ordenes_venta[item]['id_compra'], ordenes_compra[ordenes_venta[item]['id_compra']]['precio_compra']))
#fichero.write('\nGanancia operacion: %s eur.' %(ganancias[-1]))
#fichero.write('\nGanancia acumulada: %s eur.' %(sum(ganancias)))
#fichero.write(time.strftime("%c") + '\n')
#fichero.close()
###########
###########

t_inicial = time.time()

while True:
    try:
        start_time = time.time()
        try:
            r = rq.get(api_url + 'products/' + crypto + '/trades?before=1&limit=2', auth = auth)
            r1 = rq.get(api_url + 'orders', auth = auth)
            try:
                ordenes_lanzadas = r1.json()
            except:
                continue
        except:
            time.sleep(0.1)
            continue #pass
        try:
            ids_lanzadas = [x['id'] for x in ordenes_lanzadas] ## pone compra pero incluye compra y venta
        except:
            time.sleep(0.1)
            continue #pass
        for item in ordenes_venta.keys():
            if item not in ids_lanzadas:
                print('## ATTENTION!!##  SELL order %s EXECUTED in %s eur (for buy-order %s EXECUTED in %s eur)  ##' %(item, ordenes_venta[item]['precio_venta'], ordenes_venta[item]['id_compra'], ordenes_compra[ordenes_venta[item]['id_compra']]['precio_compra']))
                ganancias.append(size_order_bidask*ordenes_venta[item]['precio_venta'] - size_order_bidask*ordenes_compra[ordenes_venta[item]['id_compra']]['precio_compra'])
                ordenes_compra[ordenes_venta[item]['id_compra']]['estado_venta']='filled'
                ordenes_venta[item]['estado_venta'] = 'filled'
                print ('\nGanancia operacion: %s eur.' %(ganancias[-1]))
                print ('\nGanancia acumulada: %s eur. \n' %(sum(ganancias)))

#                ######## WITHDRAWALS INTO COINBASE ACCOUNT ################
#                r1b = rq.get(api_url + 'fills?product_id=' + crypto, auth = auth)
#                ordenes_fill = r1b.json()
#                beneficio = round((np.sum([float(x['size'])*float(x['price']) for x in ordenes_fill if x['order_id']==item])-np.sum([float(x['size'])*float(x['price']) for x in ordenes_fill if x['order_id']==ordenes_venta[item]['id_compra']])) - (np.sum([float(x['fee']) for x in ordenes_fill if x['order_id']==item])+np.sum([float(x['fee']) for x in ordenes_fill if x['order_id']==ordenes_venta[item]['id_compra']])),2)
##                r1c = rq.get(api_url + 'coinbase-accounts', auth = auth) ## 'coinbase-accounts' ## 'payment-methods'
##                payment_methods = r1c.json() #### This 2 lines are to know pay methods availables
#                order_withdrawals = {
#                'amount': beneficio,
#                'currency': 'EUR',
#                'coinbase_account_id': '274f1010-b7d9-5fba-b43b-4b3f7f756f3c'
#                }
#                if (beneficio > 0):
#                    r1d = rq.post(api_url + 'withdrawals/coinbase-account', json=order_withdrawals, auth=auth)
#                    withdrawals = r1d.json()
#                    print('%s eur benefits transferred by withdrawals into coinbase EUR-wallet' %(beneficio))
#                ######## Withdrawals finished #######

                del (ordenes_compra[ordenes_venta[item]['id_compra']])
                del (ordenes_venta[item])
        for item in ordenes_lanzadas:
            if ((item['side']=='buy')&(float(item['filled_size'])==0)&(item['id'] in ordenes_compra.keys())):
                ordenes_compra[item['id']]['contador']+=1
                if ordenes_compra[item['id']]['contador'] > n_ciclos_to_cancel:
                    r2 = rq.delete(api_url + 'orders/'+ item['id'], auth = auth)
                    disparador2 -= 1
                    print('## --CANCELED-- BUY order %s in %s eur ##' %(item['id'],ordenes_compra[item['id']]['precio_compra']))
                    del (ordenes_compra[item['id']])
        for item in ordenes_compra.keys():
            if ((item not in ids_lanzadas) and (ordenes_compra[item]['estado_compra']=='open')) :
                print('## BUY order %s EXECUTED in %s eur ##' %(item, ordenes_compra[item]['precio_compra']))
                ordenes_compra[item]['estado_compra']='filled'

        ### INITIAL DATA READING ###
        ######################################################################
        ### Get accounts ####################################################
        ####################################################################
        try:
            account = rq.get(api_url + 'accounts', auth=auth)
            try:
                account1 = account.json()
            except:
                continue
        except:
            time.sleep(0.1)
            continue #pass
        ######################################################################
        ## Initial disponibilities in my account #######################
        ####################################################################
        try:
            eur_hold = float([x['hold'] for x in account1 if x['currency']=='EUR'][0])
            eur_avai = float([x['available'] for x in account1 if x['currency']=='EUR'][0])
            ltc_hold = float([x['hold'] for x in account1 if x['currency']=='LTC'][0])
            ltc_avai = float([x['available'] for x in account1 if x['currency']=='LTC'][0])
        except:
            time.sleep(0.1)
            continue #pass
        ######################################################################
        ## bid-ask READINGS ##########################################################
        ####################################################################
        try:
            bidask = rq.get(api_url + 'products/' + crypto + '/book?level=1') # nivel 2 para 50 mejores bidask
            try:
                bidask1 = bidask.json()
            except:
                time.sleep(0.2)
                continue
            try:
                media_bidask = np.mean([float(bidask1['asks'][0][0]), float(bidask1['bids'][0][0])])
            except:
                continue
            dif_bidask = float(bidask1['asks'][0][0])-float(bidask1['bids'][0][0])
        except:
            time.sleep(0.1)
            continue #pass

        ### OPERATIVA ###
        ###############################################
        ### OPERATIVA REAL CON BID-ASK ###
        ###############################################
        precio_bidask.append(media_bidask)
        if (len(precio_bidask) > (n_lenta_bidask + 10000)):
            precio_bidask.pop(0)
        expmediavar_rapida_bidask.append(ema(n_rapida_bidask,precio_bidask, 2.0/(n_rapida_bidask+1), expmediavar_rapida_bidask))
        expmediavar_lenta_bidask.append(ema(n_lenta_bidask,precio_bidask, 2.0/(n_lenta_bidask+1), expmediavar_lenta_bidask))
        if disp1 == 0: # para eliminar el valor de referencia del principio y que cuadren las longitudes de los vectores
            expmediavar_rapida_bidask = [expmediavar_rapida_bidask[1]]
            expmediavar_lenta_bidask = [expmediavar_lenta_bidask[1]]
            disp1 = 1

        if (len(expmediavar_rapida_bidask) > (n_lenta_bidask + 10000)):
            expmediavar_rapida_bidask.pop(0)
        if (len(expmediavar_lenta_bidask) > (n_lenta_bidask + 10000)):
            expmediavar_lenta_bidask.pop(0)

        ## ALGORITMO VENTA CRYPTO
#        if ((dif_bidask >= 0.0001) and (dif_bidask < 0.02)):
#            precio_compra_bidask = "%.2f" %(float(bidask1['bids'][0][0])-0.01)
#            precio_venta_bidask = "%.2f" %(float(bidask1['bids'][0][0]))
#        elif ((dif_bidask >= 0.02) and (dif_bidask <= lim_dif_bidask)):
#            precio_compra_bidask = "%.2f" %(float(bidask1['bids'][0][0]))
#            precio_venta_bidask = "%.2f" %(float(bidask1['bids'][0][0]))
#        else:

        precio_compra_bidask = "%.2f" %(float(bidask1['bids'][0][0]))
        precio_venta_bidask = "%.2f" %(float(bidask1['bids'][0][0]))

        ##############
        ## COMPRA ###
        ############

        ### NUMERO DE PAQUETES DE COMPRA - DESCOMENTAR EN DEFINITIVOOOOOOOOOO
        if ((media_bidask > p50) and (media_bidask < p70)):
            n_paquetes_compra = 1 #4
            stop_loss = 0.02
            rango = 'p50-p70'
        elif ((media_bidask > p30) and (media_bidask <= p50)):
            n_paquetes_compra = 2 #6
            stop_loss = 0.04
            rango = 'p30-p50'
        elif ((media_bidask > p10) and (media_bidask <= p30)):
            n_paquetes_compra = 3 #10
            stop_loss = 0.04
            rango = 'p10-p30'
        elif (media_bidask <= p10):
            n_paquetes_compra = 3 #5 * n_orders # Numero maximo de ordenes de compra en activo
            stop_loss = 0.04
            rango = '<p10'
        else:
            n_paquetes_compra = 0
            rango = '>p70'

##############################################
#        Esto de debajo borrarlo en def
#        if (media_bidask > p70):
#            n_paquetes_compra = 0
#        else:
#            n_paquetes_compra = 2

        n_orders_total = n_paquetes_compra * n_orders
##############################################

        ############################################

        disparador1 += 1 # para espaciar las compras que no las haga seguidas #####
        eur_disponibles_orden = round(float(precio_compra_bidask),2)*size_order_bidask
        ### COMENTAR Y/O DESCOMENTAR LINEAS para bloqueo limite superior
        if ((seg > n_lenta_bidask) and (eur_avai > n_orders*eur_disponibles_orden) and (eur_hold < n_eur_hold) and (disparador1 >= ndisparador) and (disparador2 < n_orders_total) and (dif_bidask < limit_dif_bidask) and ((expmediavar_rapida_bidask[-2] < expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] > expmediavar_lenta_bidask[-1]))):  #### ---- cambiada
#        if ((seg > n_lenta_bidask) and (eur_avai > n_orders*eur_disponibles_orden) and (eur_hold < n_eur_hold) and (media_bidask <= lim_sup_1) and (disparador1 >= ndisparador) and (disparador2 <= n_paquetes_compra) and (dif_bidask < limit_dif_bidask) and ((expmediavar_rapida_bidask[-2] < expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] > expmediavar_lenta_bidask[-1]))):  #### ---- original sin lim_sup
            disparador1 = 0 # Para espaciar las compras
            for i in range(n_orders):
                if (disparador2 < n_orders_total):
                    if dif_bidask > lim_dif_bidask:
                        precio_random = round(float(precio_compra_bidask) + np.random.choice([x*0.01 for x in range(-2, int(lim_dif_bidask*100)-1)]),2)
                    else:
                        precio_random = round(float(precio_compra_bidask) + np.random.choice([x*0.01 for x in range(-3, 1)]),2)
                    order_buy = {
                    'product_id': crypto,
                    'side': 'buy',
                    'type': 'limit',
                    'size': size_order_bidask, ## numero ltc comprados
                    'price': precio_random
                    }
                    try:
                        r3 = rq.post(api_url + 'orders', json=order_buy, auth=auth)
                        ordenes_compra_realizadas = r3.json()
                        id_compra = ordenes_compra_realizadas['id']
                        ordenes_compra[id_compra]={'id_compra':id_compra}
                        ordenes_compra[id_compra].update({'precio_compra':round(float(ordenes_compra_realizadas['price']),2)})
                        ordenes_compra[id_compra].update({'contador':1})
                        ordenes_compra[id_compra].update({'id_venta':''})
                        ordenes_compra[id_compra].update({'estado_compra':'open'})
                        ordenes_compra[id_compra].update({'estado_venta':''}) ## '' or 'open' or 'filled'
                        ordenes_compra[id_compra].update({'serial':serial_number})
                        serial_number += 1
                        disparador2 += 1 # Para limitar el numero de compras
                        print('## BUY order %s SHOOTED in %s eur ##' %(ordenes_compra[id_compra]['id_compra'], ordenes_compra[id_compra]['precio_compra'])) ## añadir en eur el valor que he comprado y el valor al que lo vendo reflejando ganancia
                    except:
                        time.sleep(0.1) #0.5
                        continue #pass

        ##############
        ### VENTA ###
        ##############
        for item in ordenes_compra.keys():
            if((ordenes_compra[item]['precio_compra']-precio_bidask[-1]) >= (stop_loss*ordenes_compra[item]['precio_compra'])):
                forze_venta=True
                percent_sup = 1
            else:
                forze_venta=False

            if ((ordenes_compra[item]['estado_venta']=='') and (ordenes_compra[item]['estado_compra']=='filled')):
                #if (((seg > n_lenta_bidask) and (ltc_avai >= size_order_bidask) and (disparador2 > 0) and (round(float(precio_venta_bidask),2) >= ((1+(porcentaje_beneficio/100))*ordenes_compra[item]['precio_compra'])) and ((expmediavar_rapida_bidask[-2] >= expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] < expmediavar_lenta_bidask[-1]))) or (forze_venta==True)):
                if (((seg > n_lenta_bidask) and (ltc_avai >= size_order_bidask) and (round(float(precio_venta_bidask),2) >= ((1+(porcentaje_beneficio/100))*ordenes_compra[item]['precio_compra'])) and ((expmediavar_rapida_bidask[-2] >= expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] < expmediavar_lenta_bidask[-1]))) or (forze_venta==True)):  ## disparador2 cancelled
                    order_sell = {
                    'product_id': crypto,
                    'side': 'sell',
                    'type': 'limit',
                    'size': size_order_bidask,
                    'price': round(float(precio_venta_bidask),2)
                    }
                    try:
                        r4 = rq.post(api_url + 'orders', json=order_sell, auth=auth)
                        ordenes_venta_realizadas = r4.json()
                        id_venta = ordenes_venta_realizadas['id']
                        disparador2 -= 1
                        ordenes_venta[id_venta] = {'id_venta':id_venta}
                        ordenes_venta[id_venta].update({'id_compra':item})
                        ordenes_venta[id_venta].update({'precio_venta':round(float(ordenes_venta_realizadas['price']),2)})
                        ordenes_venta[id_venta].update({'id_venta':id_venta})
                        ordenes_venta[id_venta].update({'estado_venta':'open'})
                        ordenes_venta[id_venta].update({'serial':ordenes_compra[item]['serial']})
                        ordenes_compra[item]['id_venta'] = ordenes_venta[id_venta]['id_venta']
                        relacion_id_compra_venta.update({item:id_venta}) # Agregar fichero para lectura-escritura de json
                        ordenes_compra[item]['estado_venta'] = 'open'
                        seriales[item] = ordenes_compra[item]['serial']
                        seriales[id_venta] = ordenes_venta[id_venta]['serial']
                        print ('## SELL order %s SHOOTED in %s eur (for buy-order %s in %s eur)##' %(ordenes_venta[id_venta]['id_venta'],ordenes_venta[id_venta]['precio_venta'],item,ordenes_compra[item]['precio_compra']))
                    except:
                        time.sleep(0.1) #0.5
                        continue #pass

        ## PARTE FINAL DEL BUCLE, CALCULO DE TIEMPO, DE LOS NUEVOS LIMITES SI PROCEDE Y PLOTS ##
        seg+=1
        t_time.append(seg)

        if seg%n_ciclos_to_hist == 0: # Ciclos para meter el último trade en el vector para calcular el histograma y los límites
            time.sleep(1) # estaba en 2 segundos
            r4b = rq.get(api_url + 'products/' + crypto + '/trades')
            try:
                ultimo_trade = r4b.json()
                ultimo_trade[-1]['trade_id']
            except (KeyError, ValueError):
                print('KeyError -- Restart Loop')
                continue
            if ultimo_trade[-1]['trade_id'] not in list_trades_id:
                list_trades_id.append(ultimo_trade[-1]['trade_id'])
                hist_margin = np.append(hist_margin,round(float(ultimo_trade[-1]['price']),2))
                hist_margin = np.delete(hist_margin,0)
        if (len(t_time) > (n_lenta + 100)):
            t_time.pop(0)

        if seg%120 == 0:
            dif_min = round((time.time() - t_inicial)/60,2)
            print ('\nCiclo %s' %(seg))
            print ('%s Minutos' %(dif_min))
            print ('Last price = ' + str(round(media_bidask,2)) + ' eur/crypto')
            print('Rango = ' + rango + '\n' + 'Paquetes de compra = ' + str(n_paquetes_compra))
            ## Escribimos en un diccionario las ordenes de compra filled para leerlas en la sgte ejecucion del script #############
            with open('filess_compra.txt', 'w') as file:
                file.write(json.dumps(ordenes_compra)) # use `json.loads` to do the reverse
                file.close()

            time.sleep(0.1)

            with open('filess_venta.txt', 'w') as file:
                file.write(json.dumps(ordenes_venta))
                file.close()

        if seg%300 == 0:
            lim_sup_1 = stats.scoreatpercentile(hist_margin, percent_sup)
            lim_inf_1 = stats.scoreatpercentile(hist_margin, percent_inf)
            p70 = stats.scoreatpercentile(hist_margin, 70)
            p50 = stats.scoreatpercentile(hist_margin, 50)
            p30 = stats.scoreatpercentile(hist_margin, 30)
            p10 = stats.scoreatpercentile(hist_margin, 10)
            fig1 = plt.figure(1)
            plt.hist(hist_margin, bins=55)
            plt.show()
            print('\nLimite PRINCIPAL para limitar operaciones en  P%s = %s eur.' %(percent_sup, lim_sup_1) )
            print('\nLimite SECUNDARIO para limitar operaciones en P%s = %s eur.' %(percent_inf, lim_inf_1) )

            ## LOG ARCHIVE CREATION FROM GDAX API - NEW!!
            ## Fecha y hora final del codigo
            fecha_fin = datetime.datetime.utcnow()
            fecha_fin = unicode(datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ'))
            fecha_fin = time.strptime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ')
            n_pag = 1
            lista_final = []
            for i in range(n_pag):
                exec("r_%s = rq.get(api_url + 'fills/?product_id=%s', auth = auth)" %(i, crypto))
                exec("fills%s = r_%s.json()" %(i,i))
                exec("lista_final.extend(fills%s)" %(i))

            log_dataframe = pd.DataFrame(lista_final)
            log_dataframe = log_dataframe[['created_at', 'liquidity', 'order_id', 'product_id', 'profile_id', 'settled', 'trade_id', 'user_id', 'side', 'size', 'price', 'fee']]
            log_dataframe = log_dataframe.sort_values(by = 'created_at')
            log_dataframe = log_dataframe.reset_index().iloc[:,1:]

            comparador_fechas = compare_dates(log_dataframe['created_at'].values,fecha_ini,fecha_fin)
            log_dataframe = log_dataframe[comparador_fechas]

            try:
                log_dataframe['operation_value_with_fees'] = np.vectorize(valor_op)(log_dataframe['side'], log_dataframe['size'], log_dataframe['price'], log_dataframe['fee'])
                log_dataframe['serial'] = np.vectorize(assign_serial)(log_dataframe['order_id'], seriales)
                ganancia = sum(log_dataframe['operation_value_with_fees'])-sum(log_dataframe['fee'].astype('float64'))
                if system == 'linux2':
                    log_dataframe.to_csv('log_%s.csv' %(str(fecha_ini[0])+str(fecha_ini[1])+str(fecha_ini[2])), sep = ';')
                else:
                    name_fich_df = 'log_dataframe.csv'
                    log_dataframe.to_csv(name_fich_df, sep = ';')
            except:
                pass

            ########################################################################################################################

        ## CALCULO DE TIEMPO Y PAUSA POR LIMITE CONEXION
#        time.sleep(0.1)
#        elapsed_time = time.time() - start_time
#        print("Elapsed time: %.10f seconds." % elapsed_time)

        ## PARA EJECUCION DIARIA INTERRUPT -- Commented for non-interrupt execution in pythonanywhere
#        if seg%120 == 0:
#            hora_fin = datetime.datetime.utcnow()
#            if ((hora_fin.day > hora_inicio.day) and (hora_fin.hour >= hora_ejecucion) and (hora_fin.minute >= minuto_ejecucion)):
#                print ('All done')
#                break

    except (KeyboardInterrupt, SystemExit): # ctrl + c
        print ('All done')
        #raise
        break
        # ALSO VALID "raise"

## CANCEL/EXECUTE ORDERS FOR OPEN ORDERS DURING RUN-TIME EXECUTION
# OPENED-BUY ORDERS TO CANCEL
time.sleep(0.5)
a = True
while a == True:
    try:
        r5 = rq.get(api_url + 'orders', auth = auth)
        a = False
    except:
        continue
ordenes_open = r5.json()
ordenes_compra_open_nofilled = [x['id'] for x in ordenes_open if ((x['side'] == 'buy') & (float(x['filled_size']) == 0))]
for item in ordenes_compra_open_nofilled:
        r5 = rq.delete(api_url + 'orders/'+ item, auth = auth)
        print('## --CANCELED-- BUY ORDER %s in %s eur ##' %(item, ordenes_compra[item]['precio_compra']))
        del (ordenes_compra[item])

## Escribimos en un diccionario las ordenes de compra filled para leerlas en la sgte ejecucion del script
with open('filess_compra.txt', 'w') as file:
     file.write(json.dumps(ordenes_compra)) # use `json.loads` to do the reverse
     file.close()
with open('filess_venta.txt', 'w') as file:
     file.write(json.dumps(ordenes_venta))
     file.close()


######################################################################################################################################################################################################################################################################################################################################################
## OPENED BUY-ORDERS PARTIALY FILLED TO SELL
#residuales = {}
#for item in ordenes_open:
#    if ((item['side'] == 'buy') & (float(item['filled_size']) != 0)):
#        residuales.update({item['id']:size_order_bidask - float(item['size_filled'])})
#for item in ordenes_open:
#    if ((item['side']=='buy') & (float(item['filled_size']) != 0)):
#        order_sell = {
#                    'product_id': crypto,
#                    'side': 'sell',
#                    'type': 'limit',
#                    'size': residuales[item['id']],
#                    'price': round((1+((porcentaje_beneficio + 0.2)/100))*round(float(item['price'],2)))
#                    }
#        try:
#            r6 = rq.post(api_url + 'orders', json=order_sell, auth=auth)
#            ordenes_venta_realizadas = r6.json()
#            id_venta = ordenes_venta_realizadas['id']
##            ordenes_venta[id_venta] = {'id_venta':id_venta}
##            ordenes_venta[id_venta].update({'id_compra':item['id']})
##            ordenes_venta[id_venta].update({'precio_venta':order_sell['price']})
##            ordenes_venta[id_venta].update({'id_venta':id_venta})
##            ordenes_venta[id_venta].update({'estado_venta':'open'})
##            ordenes_compra[item]['id_venta'] = ordenes_venta[id_venta]['id_venta']
##            ordenes_compra[item]['estado_venta'] = 'open'
#            print ('## SELL FORCED order %s SHOOTED in %s eur (for buy-order %s)##' %(id_venta,order_sell['price'],item))
##            fichero = open(name_fich, 'at')
##            fichero.write('\n## SELL FORCED order %s SHOOTED in %s eur (for buy-order %s in %s eur)##' %(id_venta,order_sell['price'],item))
##            fichero.close()
#        except:
#            time.sleep(0.2) #0.5
#            continue #pass
#
## OPENED BUY-ORDERS TOTALLY FILLED TO SELL
#r7 = rq.get(api_url + 'fills', auth = auth)
#ordenes_fill = r7.json()
#ordenes_compra_abiertas_fill = [x['order_id'] for x in ordenes_fill if (x['side'] == 'buy')]
#for item in ordenes_compra.keys():
#    if item in ordenes_compra_abiertas_fill:
#        order_sell = {
#                    'product_id': crypto,
#                    'side': 'sell',
#                    'type': 'limit',
#                    'size': size_order_bidask,
#                    'price': round((1+((porcentaje_beneficio + 0.4)/100))*round(float(ordenes_compra[item]['precio_compra']),2),2)
#                    }
#        try:
#            r8 = rq.post(api_url + 'orders', json=order_sell, auth=auth)
#            ordenes_venta_realizadas = r8.json()
#            id_venta = ordenes_venta_realizadas['id']
#            ordenes_venta[id_venta] = {'id_venta':id_venta}
#            ordenes_venta[id_venta].update({'id_compra':item})
#            ordenes_venta[id_venta].update({'precio_venta':round(float(ordenes_venta_realizadas['price']),2)})
#            ordenes_venta[id_venta].update({'id_venta':id_venta})
#            ordenes_venta[id_venta].update({'estado_venta':'open'})
#            ordenes_compra[item]['id_venta'] = ordenes_venta[id_venta]['id_venta']
#            ordenes_compra[item]['estado_venta'] = 'open'
#            print ('## SELL FORCED order %s SHOOTED in %s eur (for buy-order %s in %s eur)##' %(ordenes_venta[id_venta]['id_venta'],ordenes_venta[id_venta]['precio_venta'],item,ordenes_compra[item]['precio_compra']))
##            fichero = open(name_fich, 'at')
##            fichero.write('\n## SELL FORCED order %s SHOOTED in %s eur (for buy-order %s in %s eur)##' %(ordenes_venta[id_venta]['id_venta'],ordenes_venta[id_venta]['precio_venta'],item,ordenes_compra[item]['precio_compra']))
##            fichero.close()
#        except:
#            time.sleep(0.2) #0.5
#            continue #pass
######################################################################################################################################################################################################################################################################################################################################################

## FIGURA 4
plt.figure(4)
plt.plot(precio_bidask, 'blue', label = crypto)
plt.plot(expmediavar_lenta_bidask, 'red', label = 'expmedia_lenta')
plt.plot(expmediavar_rapida_bidask, 'green', label = 'expmedia_rapida')
plt.legend()
plt.show()
print ('Las ganancias totales aprox. sin contar tasas han sido %s euros' %(sum(ganancias)))

## Fecha y hora final del codigo
fecha_fin = datetime.datetime.utcnow()
fecha_fin = unicode(datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ'))
fecha_fin = time.strptime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ')

## LOG ARCHIVE CREATION FROM GDAX API
n_pag = 1
lista_final = []
for i in range(n_pag):
    exec("r_%s = rq.get(api_url + 'fills/?product_id=%s', auth = auth)" %(i, crypto))
    exec("fills%s = r_%s.json()" %(i,i))
    exec("lista_final.extend(fills%s)" %(i))

log_dataframe = pd.DataFrame(lista_final)
log_dataframe = log_dataframe[['created_at', 'liquidity', 'order_id', 'product_id', 'profile_id', 'settled', 'trade_id', 'user_id', 'side', 'size', 'price', 'fee']]
log_dataframe = log_dataframe.sort_values(by = 'created_at')
log_dataframe = log_dataframe.reset_index().iloc[:,1:]

comparador_fechas = compare_dates(log_dataframe['created_at'].values,fecha_ini,fecha_fin)
log_dataframe = log_dataframe[comparador_fechas]

try:
    log_dataframe['operation_value_with_fees'] = np.vectorize(valor_op)(log_dataframe['side'], log_dataframe['size'], log_dataframe['price'], log_dataframe['fee'])
    log_dataframe['serial'] = np.vectorize(assign_serial)(log_dataframe['order_id'], seriales)
    ganancia = sum(log_dataframe['operation_value_with_fees'])-sum(log_dataframe['fee'].astype('float64'))
    if system == 'linux2':
        log_dataframe.to_csv('log_%s.csv' %(fecha_ininombre), sep = ';')
    else:
        name_fich_df = 'log_dataframe.csv'
        log_dataframe.to_csv(name_fich_df, sep = ';')
except:
    pass
##################################
### EJECUTAR HASTA AQUÍ ####
##################################




















##### lo que falta...
#
## Modulo time para interrupt cada hora
#x = datetime.datetime.utcnow()
#y = datetime.datetime.utcnow()
#y > x
#if x.day==30 and x.hour>14
#x.hour
#
#
## Modulo sockect para interrumpir ejecucion en caso de que otra ejecución está en activo
#import logging
#import socket
#import sys
#
#lock_socket = None  # we want to keep the socket open until the very end of
#                    # our script so we use a global variable to avoid going
#                    # out of scope and being garbage-collected
#
#def is_lock_free():
#    global lock_socket
#    lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
#    try:
#        lock_id = "my-username.my-task-name"   # this should be unique. using your username as a prefix is a convention
#        lock_socket.bind('\0' + lock_id)
#        logging.debug("Acquired lock %r" % (lock_id,))
#        return True
#    except socket.error:
#        # socket already locked, task must already be running
#        logging.info("Failed to acquire lock %r" % (lock_id,))
#        return False
#
#if not is_lock_free():
#    sys.exit()
#
## then, either include the rest of your script below,
## or import it, if it's in a separate file:
#from my_module import my_long_running_process
#my_long_running_process()
#
## Meter diccionario de operaciones en un archivo y que lo lea al principio del script, en vez de lanzar órdenes de venta a diestro y siniestro
#with open('filess.txt', 'w') as file:
#     file.write(json.dumps(ordenes_compra)) # use `json.loads` to do the reverse
#
#filees = open('filess.txt','r')
#ordenes_compra = json.load(open('filess.txt','r')) # use `json.loads` to do the reverse
#
######
#with open('filess.txt', 'w') as file:
#     file.write(json.dumps(account1)) # use `json.loads` to do the reverse
#filees = open('filess.txt','r')
#ordenes_compra = json.load(filees)

