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
import dateutil.parser
import hmac, hashlib, base64
from requests.auth import AuthBase
import datetime as dt
from scipy import stats
import tqdm

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

from utils import sma, ema, lag, percent, rsi, compare_dates, valor_op, assign_serial, tiempo_pausa, historic_df, \
    CoinbaseExchangeAuth, buy_sell, pinta_historico
import yaml

## Importar datos-configuraciones-funciones
#
with open('config.yaml', 'r') as config_file:
    doc = yaml.safe_load(config_file)

print('#####################################')
print(sys.platform + ' System')
print('#####################################')
print('\n### Importing Libraries... ###')

# ## Parte para cumplir 3 ejecuciones por segundo como ejemplo
# #
# for i in range(10):
#     inicio = datetime.now()
#     time.sleep(.32635373)
#     a = tiempo_pausa(inicio, 1/3)
#     time.sleep(a)

# ### AUTHENTICATION INTO COINBASE ###
#
print('\n### Authenticating... ###')
kiko = doc['Credentials'][0] #sys.argv[1] #text
sandra = doc['Credentials'][1]  #sys.argv[2] #text
pablo = doc['Credentials'][2] #sys.argv[3] #text
auth = CoinbaseExchangeAuth(kiko, sandra, pablo)

### GET ACCOUNTS ###
#
crypto = "LTC-EUR"
api_url = 'https://api.pro.coinbase.com/'
account = rq.get(api_url + 'accounts', auth=auth)
account1 = account.json()

### Disp_iniciales ###
#
disp_ini = {}
for item in account1:
    disp_ini.update({item['currency']: item['available']})

### INICIO tramo para datos anteriores ###
#
cifra_origen = 100
pag_historic = 10
hist_df = historic_df(crypto, api_url, auth, system, cifra_origen, pag_historic, version='new')

pinta_historico(hist_df, crypto)


####################################################
### START REAL-TIME TRADING #######################
##################################################
print('\n### Data OK! ###')
print('\n### Real-Time Processing... ### - \nPress CTRL+C (QUICKLY 2-TIMES!!) to cancel and view results')

## INITIAL RESET FOR VARIABLES

size_order_bidask = 0.1
limit_dif_bidask = 1
n_ciclos_to_cancel = 50
porcentaje_caida = 8
porcentaje_beneficio = 3
disp = 0 # Para ajustar historico
disp1 = 0 # Para ajustar historico

serial_number = 1 # Para relacionar las ordenes de compra-venta

precio = []
precio_bidask = []
fecha = []
crypto_price = []

seg = 0

t_time = []

n_rapida_bidask = 4
n_lenta_bidask = 12
n_rapida = 100
n_lenta = 200
alpha_rapida_bidask = 2.0/(n_rapida_bidask+1)
alpha_lenta_bidask = 2.0/(n_lenta_bidask+1)
precio_compra_bidask_ejecutado = []
precio_venta_bidask_ejecutado = []

list_trades_id = []
n_precios_hist = len(hist_df) # Longitud de lista de valores para calcular el hist y actualizar el valor máximo
hist_margin = np.around(list(hist_df[crypto][-n_precios_hist-1:-1].values), 2) # vector de precios pasados al que agregar los nuevos precios y que nos sirva para establecer nuevos límites a la compra...
n_ciclos_to_hist = 120 # 120 estaba inicialmente... número de ciclos para meter ultima orden en hist para calcular limite de operacion
ids_comp_vent = {}
contadores = {}

seriales = {}
relacion_id_compra_venta = {}
forze_venta = False
plt.ion()

try:
    f = open('filess_compra.txt', 'r')
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
    f = open('filess_venta.txt', 'r')
    ordenes_venta = json.load(f)
    f.close()
except:
    ordenes_venta = {}

####################################################################################################################### END-NEW

### para los ficheros de registro ###
#
# ## Fecha y hora inicial del codigo
# fecha_ini = datetime.datetime.utcnow()
# #fecha_ini = unicode(datetime.datetime.strftime(fecha_ini, '%Y-%m-%dT%H:%M:%S.%fZ'))
# fecha_ini = datetime.datetime.strftime(fecha_ini, '%Y-%m-%dT%H:%M:%S.%fZ')
# fecha_ini = time.strptime(fecha_ini, '%Y-%m-%dT%H:%M:%S.%fZ')
# ## Fecha apertura operaciones hoy
# fecha_ininombre = time.strftime("%c")
# if system == 'linux2':
#     name_fich = 'log_' + fecha_ininombre + '.txt'
# else:
#     name_fich = 'log.txt'


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
freq = 3
period = 1/freq

# while True:
#     try:
        start_time = time.time()

        ## Ultimas ordenes lanzadas tanto de compra como de venta
        #
        try:
            # r = rq.get(api_url + 'products/' + crypto + '/trades?before=1&limit=2', auth=auth)
            r1 = rq.get(api_url + 'orders', auth=auth)
            try:
                ordenes_lanzadas = r1.json()
            except:
                pass
        except:
            time.sleep(0.1)
            pass
        try:
            ids_lanzadas = [x['id'] for x in ordenes_lanzadas] ## pone compra pero incluye compra y venta
        except:
            time.sleep(0.1)
            pass

        ### Borrado ordenes de Compra/Venta/Canceladas ###
        #
        for item in ordenes_venta.keys():
            if item not in ids_lanzadas:
                print('## ATTENTION!!##  SELL order %s EXECUTED in %s eur (for buy-order %s EXECUTED in %s eur)  ##' %(item, ordenes_venta[item]['precio_venta'], ordenes_venta[item]['id_compra'], ordenes_compra[ordenes_venta[item]['id_compra']]['precio_compra']))
                ordenes_compra[ordenes_venta[item]['id_compra']]['estado_venta'] = 'filled'
                ordenes_venta[item]['estado_venta'] = 'filled'
                print ('\nGanancia operacion: %s eur.' %(ganancias[-1]))
                print ('\nGanancia acumulada: %s eur. \n' %(sum(ganancias)))
                del (ordenes_compra[ordenes_venta[item]['id_compra']])
                del (ordenes_venta[item])

        for item in ordenes_lanzadas:
            if ((item['side']=='buy')&(float(item['filled_size'])==0)&(item['id'] in ordenes_compra.keys())):
                ordenes_compra[item['id']]['contador']+=1
                if ordenes_compra[item['id']]['contador'] > n_ciclos_to_cancel:
                    r2 = rq.delete(api_url + 'orders/' + item['id'], auth=auth)
                    disparador2 -= 1
                    print('## --CANCELED-- BUY order %s in %s eur ##' %(item['id'], ordenes_compra[item['id']]['precio_compra']))
                    del (ordenes_compra[item['id']])

        for item in ordenes_compra.keys():
            if ((item not in ids_lanzadas) and (ordenes_compra[item]['estado_compra']=='open')) :
                print('## BUY order %s EXECUTED in %s eur ##' %(item, ordenes_compra[item]['precio_compra']))
                ordenes_compra[item]['estado_compra'] = 'filled'

        disparador2 = len([x for x in ordenes_compra if ordenes_compra[x]['estado_venta'] == '']) ## ojo!!

        ### Get accounts ###
        #
        try:
            account = rq.get(api_url + 'accounts', auth=auth)
            try:
                account1 = account.json()
            except:
                pass
        except:
            time.sleep(0.1)
            pass

        ### Initial disponibilities in my account ###
        #
        activos_disponibles = {x['currency']: {'hold': x['hold'], 'available': x['available']} for x in account1}
        eur_avai = float(activos_disponibles['EUR']['available'])
        ### bid-ask READINGS ###
        #
        try:
            bidask = rq.get(api_url + 'products/' + crypto + '/book?level=1') # nivel 2 para 50 mejores bidask
            try:
                bidask1 = bidask.json()
            except:
                time.sleep(0.1)
                pass
            try:
                media_bidask = np.mean([float(bidask1['asks'][0][0]), float(bidask1['bids'][0][0])])
                dif_bidask = round(float(bidask1['asks'][0][0]) - float(bidask1['bids'][0][0]), 2)
            except:
                pass
        except:
            time.sleep(0.1)
            pass

        ### OPERATIVA REAL CON BID-ASK ###
        #
        precio_bidask.append(media_bidask)

        ### Limitacion tamaño lista ###
        #
        if (len(precio_bidask) > (n_lenta_bidask + 50000)):
            precio_bidask.pop(0)

        precio_compra_bidask = "%.2f" % (float(bidask1['bids'][0][0]))
        precio_venta_bidask = "%.2f" % (float(bidask1['asks'][0][0]))

        ##############
        ## COMPRA ###
        ############

        ############################################

        # disparador1 += 1 # para espaciar las compras que no las haga seguidas #####
        eur_disponibles_orden = round(float(precio_compra_bidask), 2) * size_order_bidask

        regla_inicio_disponibilidad_eur = eur_avai > eur_disponibles_orden
        regla_orden_compra_lanzada = disparador2 == 0
        regla_dif_bidask = (dif_bidask < limit_dif_bidask * media_bidask)
        n_ciclos5 = freq * 1200
        n_ciclos10 = freq * 2400
        n_ciclos15 = freq * 5400
        n_ciclos20 = freq * 10800
        regla_tiempo_minimo_ejecucion = len(precio_bidask) > n_ciclos5

        if regla_tiempo_minimo_ejecucion:
            regla_oportunidad_5 = (precio_venta_bidask <= precio_bidask[-n_ciclos5])
        else:
            regla_oportunidad_5 = False
        # regla_oportunidad_10 = (precio_venta_bidask <= precio_bidask[-n_ciclos10])
        # regla_oportunidad_15 = (precio_venta_bidask <= precio_bidask[-n_ciclos15])
        # regla_oportunidad_20 = (precio_venta_bidask <= precio_bidask[-n_ciclos20])

        sum_conditions = (regla_inicio_disponibilidad_eur and regla_orden_compra_lanzada and
            regla_dif_bidask and regla_tiempo_minimo_ejecucion and regla_oportunidad_5)
        sum_conditions = True
        precio_venta_bidask=100

        ordenes_compra_realizadas = buy_sell('buy', crypto, sum_conditions, float(size_order_bidask),
                                             float(precio_venta_bidask), 'limit', api_url, auth)

        id_compra = ordenes_compra_realizadas['id']


        ## implementar esto -->
        # ordenes_compra[id_compra] = {'id_compra': id_compra}
        # ordenes_compra[id_compra].update({'precio_compra': round(float(ordenes_compra_realizadas['price']), 2)})
        # ordenes_compra[id_compra].update({'contador': 1})
        # ordenes_compra[id_compra].update({'id_venta': ''})
        # ordenes_compra[id_compra].update({'estado_compra': 'open'})
        # ordenes_compra[id_compra].update({'estado_venta': ''})  ## '' or 'open' or 'filled'
        # ordenes_compra[id_compra].update({'serial': serial_number})
        # serial_number += 1
        # disparador2 += 1  # Para limitar el numero de compras
        # print('## BUY order %s SHOOTED in %s eur ##' % (ordenes_compra[id_compra]['id_compra'],
        #                                                 ordenes_compra[id_compra]['precio_compra']))  ## añadir en eur el valor que he comprado y el valor al que lo vendo reflejando ganancia
        # print(ordenes_compra_realizadas)


        ### old
        # if sum_conditions:
        #             order_buy = {
        #                 # 'type': "market",
        #                 "size": size_order_bidask,
        #                 "price": precio_venta_bidask,
        #                 "side": "buy",
        #                 "product_id": crypto
        #             }
        #
        #             try:
        #                 # r3 = rq.post(api_url + 'orders', json=order_buy, auth=auth)
        #                 r3 = rq.post(api_url + 'orders', data=json.dumps(order_buy), auth=auth)
        #                 ordenes_compra_realizadas = r3.json()
        #                 id_compra = ordenes_compra_realizadas['id']
        #                 ordenes_compra[id_compra] = {'id_compra': id_compra}
        #                 ordenes_compra[id_compra].update({'precio_compra': round(float(ordenes_compra_realizadas['price']), 2)})
        #                 ordenes_compra[id_compra].update({'contador': 1})
        #                 ordenes_compra[id_compra].update({'id_venta': ''})
        #                 ordenes_compra[id_compra].update({'estado_compra': 'open'})
        #                 ordenes_compra[id_compra].update({'estado_venta': ''}) ## '' or 'open' or 'filled'
        #                 ordenes_compra[id_compra].update({'serial': serial_number})
        #                 serial_number += 1
        #                 disparador2 += 1 # Para limitar el numero de compras
        #                 print('## BUY order %s SHOOTED in %s eur ##' % (ordenes_compra[id_compra]['id_compra'], ordenes_compra[id_compra]['precio_compra'])) ## añadir en eur el valor que he comprado y el valor al que lo vendo reflejando ganancia
        #             except:
        #                 time.sleep(0.1)
        #                 pass

        ##############
        ### VENTA ###
        ##############

#        for item in ordenes_compra.keys():

 #           if((ordenes_compra[item]['precio_compra']-precio_bidask[-1]) >= (stop_loss*ordenes_compra[item]['precio_compra'])):
  #              forze_venta=True
   #             percent_sup = 1
    #        else:
     #           forze_venta=False

      #      if ((ordenes_compra[item]['estado_venta']=='') and (ordenes_compra[item]['estado_compra']=='filled')):
       #         #if (((seg > n_lenta_bidask) and (ltc_avai >= size_order_bidask) and (disparador2 > 0) and (round(float(precio_venta_bidask),2) >= ((1+(porcentaje_beneficio/100))*ordenes_compra[item]['precio_compra'])) and ((expmediavar_rapida_bidask[-2] >= expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] < expmediavar_lenta_bidask[-1]))) or (forze_venta==True)):
        #        if (((seg > n_lenta_bidask) and (ltc_avai >= size_order_bidask) and (round(float(precio_venta_bidask),2) >= ((1+(porcentaje_beneficio/100))*ordenes_compra[item]['precio_compra'])) and ((expmediavar_rapida_bidask[-2] >= expmediavar_lenta_bidask[-2]) and (expmediavar_rapida_bidask[-1] < expmediavar_lenta_bidask[-1]))) or (forze_venta==True)):  ## disparador2 cancelled

        for item in ordenes_compra.keys():

            regla_stoploss = ((ordenes_compra[item]['precio_compra']-precio_bidask[-1]) >= (stop_loss*ordenes_compra[item]['precio_compra']))
            regla_estado = ((ordenes_compra[item]['estado_venta']=='') and (ordenes_compra[item]['estado_compra']=='filled'))
            regla_disponibilidad_crypto = ((seg > n_lenta_bidask) and (ltc_avai >= size_order_bidask))
            regla_beneficio = (round(float(precio_venta_bidask),2) >= ((1+(porcentaje_beneficio/100))*ordenes_compra[item]['precio_compra']))
            regla_medias_exp_venta = ((expmediavar_rapida_bidask[-2] >= expmediavar_lenta_bidask[-2]) and
                (expmediavar_rapida_bidask[-1] < expmediavar_lenta_bidask[-1]))

            if regla_stoploss:
                forze_venta=True
                percent_sup = 1
            else:
                forze_venta=False

            if regla_estado:
                if ((regla_disponibilidad_crypto and regla_beneficio and regla_medias_exp_venta) or (forze_venta == True)):  ## disparador2 cancelled
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

        if seg%30 == 0:
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
            print(trigg_oportunidad)
            print(trigg_oportunidad2)

            ## LOG ARCHIVE CREATION FROM GDAX API - NEW!!
            ## Fecha y hora final del codigo
            fecha_fin = datetime.datetime.utcnow()
            #fecha_fin = unicode(datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ'))
            fecha_fin = datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ')
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
#fecha_fin = unicode(datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ'))
fecha_fin = datetime.datetime.strftime(fecha_fin, '%Y-%m-%dT%H:%M:%S.%fZ')
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
