#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from matplotlib import pyplot as plt 
import math
import scipy
import pickle as pkl
import re
import datetime
pd.set_option("display.max_colwidth", None)
import warnings
warnings.filterwarnings('ignore')
import os

# Define el directorio predeterminado
directorio_predeterminado = 'C:/GCBA/Nueva_Metrica_Semanal/data'

# Cambiar al directorio predeterminado
os.chdir(directorio_predeterminado)

# Ahora el directorio predeterminado es el nuevo directorio de trabajo


# #### Importamos los DataFrames

# In[2]:


# usuarios que mandaron @test_on @test_off @reset_user INCORPORAR LOS NUEVOS INTENT PARA TESTEO QUE SE AGREGARON EN FEBRERO DEL 2024

testers=pd.read_csv('testers.csv')
#testers=testers.f0_.values


# In[3]:


rule_ne='PLBWX5XYGQ2B3GP7IN8Q-nml045fna3@b.m-1669990832420'


# In[4]:


# Mesage metrics (mensajes)
mm=pd.read_csv('mensajes.csv')


# In[5]:


# Modificaciones necesesarias al campo creation_time segun la fuente de origen (Bq o Athena)

mm.creation_time=pd.to_datetime(mm.creation_time)

#mm.creation_time = pd.to_datetime(str(mm.creation_time)[10:30])

mm.creation_time=mm.creation_time.dt.tz_localize(None)

#mm = mm.rename(columns = {"vars_value": "value"})


# In[6]:


# Validación de fecha mínima o de rango de fecha y hora

mm1=mm[mm['creation_time']>=np.datetime64('2024-02-19 13:00:00') ]
#mm1 = mm[(mm['creation_time'] >= np.datetime64('2024-02-23 17:00:00')) & (mm['creation_time'] <= np.datetime64('2024-02-24 18:00:00'))]


# In[7]:


mm1.rule_name.nunique()


# In[8]:


# Convierte la columna 'creation_time' de mm1 al formato de fecha y hora.
mm1.creation_time = pd.to_datetime(mm1.creation_time)

# Redondea hacia arriba la columna 'creation_time' al segundo más cercano.
mm1.creation_time = mm1.creation_time.dt.ceil('s')

# Elimina filas duplicadas basadas en las columnas especificadas.
mm1.drop_duplicates(['session_id', 'creation_time', 'msg_from', 'rule_name'], inplace=True)

# Crea una nueva columna 'usuario' que toma los primeros 20 caracteres de la columna 'session_id'.
mm1['usuario'] = mm1.session_id.str[:20]

# Filtra las filas donde el valor de 'usuario' no está en la lista de testers.
mm1 = mm1[~mm1.usuario.isin(testers)]

# Reinicia los índices del DataFrame después de realizar las operaciones anteriores y descarta los índices anteriores.
mm1.reset_index(inplace=True, drop=True)


# In[9]:


mm1.usuario.nunique()


# In[10]:


# search + response = clicks

# Lee el archivo CSV y carga los datos en el DataFrame 'search'.
search=pd.read_csv('clicks.csv')

# Elimina filas duplicadas basadas en las columnas especificadas en el DataFrame 'search'.
search.drop_duplicates(['session_id', 'ts', 'id', 'message', 'mostrado', 'response_message'], inplace=True)

#####################################################
#EN ESTE LUGAR ESTARIA BUENO PROBAR EL MISMO REDONDEO DEL SEGUNDO EN TS PARA EVITAR EL PROBLEMA QUE TUVIMOS CON LA CANTIDAD DE CARACTERAS

# Redondea hacia arriba la columna 'creation_time' al segundo más cercano.
mm1.creation_time = mm1.creation_time.dt.ceil('s')
# Convierte la columna 'ts' (timestamp) de 'search' al formato de fecha y hora.
search.ts=pd.to_datetime(search.ts)
####################################################

# Crea una nueva columna 'usuario' que toma los primeros 20 caracteres de la columna 'session_id'.
search['usuario']=search.session_id.str[:20]

# Filtra las filas donde el valor de 'usuario' no está en la lista de testers.
search=search[~search.usuario.isin(testers)]

# Filtra las filas en las que la columna 'mostrado' es igual a la columna 'response_intent_id' con la condición 'RuleBuilder:'.
# Luego, elimina filas duplicadas basadas en la columna 'id' del resultado y almacena el resultado en 'searchcl'.
searchcl=search['RuleBuilder:'+search.mostrado==search.response_intent_id].drop_duplicates('id')

# Crea una nueva columna 'fecha' en 'search' que contiene solo la parte de la fecha de la columna 'ts'.
search['fecha']=search.ts.dt.date


# In[11]:


search.head()


# In[12]:


searchcl.head()


# In[13]:


# user-buttons (botones)
one=pd.read_csv('botones.csv')


# In[14]:


# Procesamiento de datos en el DataFrame 'one':  ONESHOTS

# Crea una nueva columna 'usuario' en el DataFrame 'one', que toma los primeros 20 caracteres de la columna 'session_id'.
one['usuario'] = one.session_id.str[:20]

# Filtra las filas donde el valor de 'usuario' no está en la lista de testers.
one = one[~one.usuario.isin(testers)]

# Filtra las filas en el DataFrame 'one' donde 'one_shot' es True y 'type' es 'oneShot' o 'oneShotSearch'.
os = one[np.logical_and(one.one_shot == True, one.type.isin(['oneShot', 'oneShotSearch']))]

# Convierte la columna 'ts' (timestamp) de 'os' al formato de fecha y hora. HABRIA QUE REDONDEAR LSO SEGUNDOS POR LAS DUDAS TAMBIEN?
os.ts = pd.to_datetime(os.ts)

# Crea una nueva columna 'fecha' en 'os' que contiene solo la parte de la fecha de la columna 'ts'.
os['fecha'] = os.ts.dt.date


# In[15]:


#importamos el csv con la lista de los intents mostrables (tambien aparece como showable)

mos=pd.read_csv('Actualizacion_Lista_Blanca.csv')
# Elimina los espacios en blanco alrededor de los nombres de intenciones en la columna 'Nombre de la intención'.
rules_mos = mos['Nombre de la intención'].str.strip().values


# ### Transformaciones

# In[16]:


# sacamos mensajes seguidos de boti

# Reinicia los índices del DataFrame 'mm1', descartando los índices anteriores y aplicando los cambios en el lugar.
mm1.reset_index(inplace=True, drop=True)

# Crea una lista 'drop' que contiene los índices de las filas que deben eliminarse.
drop = [i if mm1.loc[i].msg_from == mm1.loc[i+1].msg_from and mm1.loc[i].session_id == mm1.loc[i+1].session_id else None for i in mm1.index[:-1]]

# Convierte la lista 'drop' en un conjunto para eliminar duplicados y luego convierte de nuevo a lista.
drop = list(set(drop))

# Elimina los valores 'None' de la lista 'drop'.
drop.remove(None)

# Elimina las filas del DataFrame 'mm1' utilizando los índices almacenados en la lista 'drop'.
mm1.drop(drop, inplace=True)

# Reinicia los índices del DataFrame 'mm1' después de eliminar las filas, descartando los índices anteriores y aplicando los cambios en el lugar.
mm1.reset_index(inplace=True, drop=True)


# In[17]:


# Selecciona las filas en el DataFrame 'mm1' donde la columna 'max_score' no es nula y muestra las primeras filas.
mm1[~mm1['max_score'].isnull()].head()


# #### Modelo Nuevo Primera Instancia

# In[18]:


# Análisis de respuestas por usuario en el DataFrame 'mm1':


# Copia y reinicia los índices del DataFrame 'mm1'.
mm = mm1.copy()
mm.reset_index(inplace=True, drop=True)

# Filtra y selecciona columnas específicas de mensajes de texto enviados por usuarios.
mmtex1 = mm[np.logical_and(mm.msg_from == 'user', mm.message_type == 'Text')][['session_id', 'id', 'creation_time', 'msg_from', 'message_type', 'message', 'usuario']]

# Crea la columna 'rule_name' basada en ciertas condiciones.
mmtex1['rule_name'] = [r if su == sb and f == 'bot' else None for r, su, sb, f in zip(mm.loc[mmtex1.index + 1].rule_name.values, mmtex1.session_id.values, mm.loc[mmtex1.index + 1].session_id.values, mm.loc[mmtex1.index + 1].msg_from.values)]

# Filtra y selecciona las filas relacionadas con la regla 'No entendió letra no existente en WA'.
letra1 = mmtex1[mmtex1.rule_name == 'No entendió letra no existente en WA']
letra1.rename(columns={'id': 'message_id'}, inplace=True)

# Filtra 'search' y 'os' según 'mm1.session_id.values'.
search1 = search[search.session_id.isin(mm1.session_id.values)]
os1 = os[os.session_id.isin(mm1.session_id.values)]

# Filtra las instancias iniciales que no están en 'search1' o 'os1' y realiza algunas transformaciones.
primera_instancia1 = search[~search.message_id.isin(pd.concat([search1['RuleBuilder:' + search1.mostrado == search1.response_intent_id].message_id, os1.message_id]).values)].drop_duplicates('id')
primera_instancia1.rename(columns={"results_score": "score"}, inplace=True)
ne1 = primera_instancia1.groupby('id').max()[['session_id', 'message_id', 'score']]
ne1 = ne1[ne1.score <= 5.36]

primera_instancia1 = primera_instancia1[~primera_instancia1.id.isin(ne1.index)]
os1 = os1.drop_duplicates('id')[['session_id', 'message_id']]
click1 = search1['RuleBuilder:' + search1.mostrado == search1.response_intent_id].drop_duplicates('id')[['session_id', 'message_id']]
abandonos1 = primera_instancia1[primera_instancia1.response_message.isna()][['session_id', 'message_id']]
nada1 = primera_instancia1[primera_instancia1.response_intent_id == 'RuleBuilder:PLBWX5XYGQ2B3GP7IN8Q-alfafc@gmail.com-1536777380652'][['session_id', 'message_id']]
texto1 = primera_instancia1[np.logical_and(primera_instancia1.response_intent_id != 'RuleBuilder:PLBWX5XYGQ2B3GP7IN8Q-alfafc@gmail.com-1536777380652', ~primera_instancia1.response_message.isna())][['session_id', 'message_id']]
letra1 = letra1[['session_id', 'message_id']]

# Agrega una columna 'categoria' a 'os1', 'click1', 'abandonos1', 'nada1', 'texto1', 'ne1', y 'letra1'.
os1['categoria'] = 'one'
click1['categoria'] = 'click'
abandonos1['categoria'] = 'abandono'
nada1['categoria'] = 'nada'
texto1['categoria'] = 'texto'
ne1['categoria'] = 'ne'
letra1['categoria'] = 'letra'

# Concatena y filtra 'value1primera' según 'mm1.usuario.values'.
value1primera = pd.concat([os1, click1, abandonos1, nada1, texto1, ne1, letra1])
value1primera['usuario'] = value1primera.session_id.str[:20]
value1primera = value1primera[value1primera.usuario.isin(mm1.usuario.values)]

# Realiza un análisis de respuestas por usuario y categoría.
respuestas_por_usuario = value1primera.groupby(['usuario', 'categoria'], as_index=False).count()[['usuario', 'categoria', 'message_id']].pivot_table('message_id', ['usuario'], 'categoria')
respuestas_por_usuario.fillna(0, inplace=True)
respuestas_por_usuario = respuestas_por_usuario.reset_index(drop=False).reindex(['usuario', 'one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra'], axis=1)

# Calcula porcentajes por categoría para cada usuario.
respuestas_por_usuario['porcentaje_abandono']=[respuestas_por_usuario.loc[i].abandono / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_click']=[respuestas_por_usuario.loc[i].click / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_one']=[respuestas_por_usuario.loc[i].one / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_texto']=[respuestas_por_usuario.loc[i].texto / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_nada']=[respuestas_por_usuario.loc[i].nada / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_ne']=[respuestas_por_usuario.loc[i]['ne'] / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]
respuestas_por_usuario['porcentaje_letra']=[respuestas_por_usuario.loc[i]['letra'] / respuestas_por_usuario.loc[i][['one', 'click', 'texto', 'abandono', 'nada', 'ne', 'letra']].sum() for i in respuestas_por_usuario.index]


# Crea un DataFrame 'res_primera_instancia1' basado en 'respuestas_por_usuario'.
res_primera_instancia1 = respuestas_por_usuario.copy()

# Calcula promedios para diferentes categorías.
promedios1={'abandonos': round(respuestas_por_usuario['porcentaje_abandono'].mean(), 3),     
                  'click': round(respuestas_por_usuario['porcentaje_click'].mean(), 3),
                  'one': round(respuestas_por_usuario['porcentaje_one'].mean(), 3),
                  'texto': round(respuestas_por_usuario['porcentaje_texto'].mean(), 3),
                  'nada': round(respuestas_por_usuario['porcentaje_nada'].mean(), 3),
                  'letra': round(respuestas_por_usuario['porcentaje_letra'].mean(), 3),
                  'ne': round(respuestas_por_usuario['porcentaje_ne'].mean(), 3)
}



# In[19]:


promedios1


# In[20]:


# Definimos la funcion que identifica las distintas categorías

def categoria(m, t, r):
    # Esta función categoriza mensajes basándose en el contenido del mensaje (m), el tipo de mensaje (t), y el nombre de la regla (r).

    try:
        # Verifica si el tipo de mensaje es 'Button-click' y si el mensaje contiene 'Cambiar de tema'.
        if t == 'Button-click' and 'Cambiar de tema' in m:
            return 'cambiar'

        # Verifica si el tipo de mensaje es 'Button-click' y si la regla es 'Menú show buttons'.
        elif t == 'Button-click' and r == 'Menú show buttons':
            return 'otros'

        # Verifica si el tipo de mensaje es 'Button-click' y si el mensaje contiene 'No era nada de eso'.
        elif t == 'Button-click' and 'No era nada de eso' in m:
            return 'x'

        # Verifica si el tipo de mensaje es 'Button-click'.
        elif t == 'Button-click':
            return 'boton'

        # Verifica si el mensaje es 'a', 'b', 'c', o 'd' (ignorando mayúsculas y minúsculas) y si la regla es 'Infracciones * Apertura'.
        elif re.match(r'^a$|^b$|^c$|^d$', m, re.IGNORECASE) and r == 'Infracciones * Apertura':
            return 'boton'

        # Verifica si el mensaje es 'a', 'b', 'c', o 'd' (ignorando mayúsculas y minúsculas) y si la regla es 'Busca donde está permitido estacionar'.
        elif re.match(r'^a$|^b$|^c$|^d$', m, re.IGNORECASE) and r == 'Busca donde está permitido estacionar':
            return 'boton'

        # elif m == '__image__' and r == 'Denuncia Vial - Validación Vehículo':
        #     return 'boton'
        # elif re.match(r'[0-9]{7,8}', m) and r == 'Licencia prorroga  > Consultar':
        #     return 'boton'

        # Verifica si el mensaje es 'x' (ignorando mayúsculas y minúsculas) o 'x buscaba otra cosa'.
        elif re.match(r'(^x$)|(x?\.? ?buscaba otra cosa)', m, re.IGNORECASE):
            return 'x'

        # Si no coincide con ninguna de las condiciones anteriores, categoriza como 'texto'.
        else:
            return 'texto'

    except:
        # Maneja excepciones y retorna 'otros' en caso de error.
        return 'otros'


# In[21]:


# Análisis de interacciones del usuario en el DataFrame 'mm1':

# Copia el DataFrame 'mm1' a 'mm'.
mm = mm1.copy()

# Reinicia los índices de 'mm', descartando los índices anteriores y aplicando los cambios en el lugar.
mm.reset_index(inplace=True, drop=True)

# Filtra las filas donde 'msg_from' es 'user'.
mmu = mm[mm.msg_from == 'user']

# Reinicia los índices de 'mmu', descartando los índices anteriores y aplicando los cambios en el lugar.
mmu.reset_index(inplace=True, drop=True)

# Filtra las filas originales del usuario que están en 'searchcl.message_id'.
original = mmu[mmu.id.isin(searchcl.message_id.values)] 

# Obtiene las filas siguientes (botones) y respuestas subsiguientes.
boton = mmu.loc[original.index + 1]
respuesta = mmu.loc[original.index + 2]

# Crea un DataFrame 'conv_cl' con información de la conversación, como la sesión, la hora de creación y mensajes originales.
# También incluye información sobre el intent, el primer botón, respuestas intermedias y finales.
conv_cl = pd.DataFrame(data={'session_id': original.session_id.values, 'creation_time': original.creation_time.values, 'original': original.message.values, 
                             'intent': mm.loc[mm[mm.id.isin(boton.id.values)].index + 1].rule_name.values,
                             'bot1_id': [m if v else None for m, v in zip(mm.loc[mm[mm.id.isin(boton.id.values)].index + 1].id.values, original.session_id.values==mm.loc[mm[mm.id.isin(boton.id.values)].index + 1].session_id.values)],
                             'respuesta_intermedia': [m if v else None for m, v in zip(boton.message.values, original.session_id.values==boton.session_id.values)], 
                             'respuesta': [m if v else None for m, v in zip(respuesta.message.values, original.session_id.values==respuesta.session_id.values)],
                             'respuesta_type': [m if v else None for m, v in zip(respuesta.message_type.values, original.session_id.values==respuesta.session_id.values)],
                             'respuesta_rule': [m if v else None for m, v in zip(mm.loc[mm[mm.id.isin(respuesta.id.values)].index + 1].rule_name.values, original.session_id.values==mm.loc[mm[mm.id.isin(respuesta.id.values)].index + 1].session_id.values)]})

mm = mm1.copy()
mm.reset_index(inplace=True, drop=True)
mmu = mm[mm.msg_from == 'user']
mmu.reset_index(inplace=True, drop=True)

# Filtra las filas originales del usuario que están en 'os.message_id'.
original = mmu[mmu.id.isin(os.message_id.values)]


print("Empieza codigo de Debug...")

# Obtiene la respuesta subsiguiente.
#respuesta = mmu.loc[original.index + 1]

next_index = original.index + 1
if next_index.isin(mmu.index).all():
    respuesta = mmu.loc[next_index]
else:
    next_index_exists = next_index[next_index.isin(mmu.index)]  # Filtro los índices siguientes que existen en mmu
    respuesta = mmu.loc[next_index_exists]



print("Paso el problema del Index que nos daba el viernes...")

# Verifico si 'respuesta.message.values' es una serie iterable
if hasattr(respuesta, 'message') and hasattr(respuesta.message, 'values'):
    # Calculo las longitudes de 'original.session_id.values' y 'respuesta.session_id.values'
    len_original = len(original.session_id.values)
    len_respuesta = len(respuesta.session_id.values)
    
    print(f"Longitud de original.session_id.values: {len_original}")
    print(f"Longitud de respuesta.session_id.values: {len_respuesta}")
    
    # las comparo a ver que pasa
    if len_original == len_respuesta:
        print("Las longitudes son iguales.")
        
        # Comparo todas las sesiones
        sessions_match = original.session_id.values == respuesta.session_id.values
        
        # Mando por pantalla las comparaciones
        print("Comparación de sesiones:")
        for i, match in enumerate(sessions_match):
            print(f"Sesión {i+1}: {'Coincide' if match else 'No coincide'}")
        
        # Crea el DataFrame 'conv' en caso que las comparaciones me hayan dado posta
        conv = pd.DataFrame(data={'session_id': original.session_id.values, 
                                  'creation_time': original.creation_time.values, 
                                  'original': original.message.values, 
                                  'intent': mm.loc[mm[mm.id.isin(original.id.values)].index + 1].rule_name.values,
                                  'bot1_id': [m if v else None for m, v in zip(mm.loc[mm[mm.id.isin(original.id.values)].index + 1].id.values, original.session_id.values==mm.loc[mm[mm.id.isin(original.id.values)].index + 1].session_id.values)],
                                  #'respuesta': [m if v else None for m, v in zip(respuesta.message.values, original.session_id.values==respuesta.session_id.values)],
                                  #'respuesta_type': [m if v else None for m, v in zip(respuesta.message_type.values, original.session_id.values==respuesta.session_id.values)],
                                  #'respuesta_rule': [m if v else None for m, v in zip(mm.loc[mm[mm.id.isin(respuesta.id.values)].index + 1].rule_name.values, original.session_id.values==mm.loc[mm[mm.id.isin(respuesta.id.values)].index + 1].session_id.values)]
                                  })
    else:
        print("La longitud de original.session_id.values y respuesta.session_id.values no coincide.")
else:
    print("'respuesta.message.values' no es una serie iterable.")


print("Fin del codigo de debug")


# # Obtener las listas de datos
# session_id_values = original.session_id.values
# creation_time_values = original.creation_time.values
# message_values = original.message.values
# intent_values = mm.loc[mm[mm.id.isin(original.id.values)].index + 1].rule_name.values
# bot1_id_values = [m if v else None for m, v in zip(mm.loc[mm[mm.id.isin(original.id.values)].index + 1].id.values, original.session_id.values==mm.loc[mm[mm.id.isin(original.id.values)].index + 1].session_id.values)]
# respuesta_message_values = respuesta.message.values
# respuesta_message_type_values = respuesta.message_type.values

# # Crear un diccionario de listas con sus nombres
# listas = {
#     'session_id_values': session_id_values,
#     'creation_time_values': creation_time_values,
#     'message_values': message_values,
#     'intent_values': intent_values,
#     'bot1_id_values': bot1_id_values,
#     'respuesta_message_values': respuesta_message_values,
#     'respuesta_message_type_values': respuesta_message_type_values
# }

# # Verificar la longitud de cada lista e imprimir las longitudes distintas
# longitudes_distintas = False
# for nombre_lista, lista in listas.items():
#     longitud = len(lista)
#     print(f"Longitud de {nombre_lista}: {longitud}")
#     if longitud != len(session_id_values):
#         longitudes_distintas = True

# # Si todas las listas tienen la misma longitud, crear el DataFrame
# if not longitudes_distintas:
#     conv = pd.DataFrame(data={
#         'session_id': session_id_values,
#         'creation_time': creation_time_values,
#         'original': message_values,
#         'intent': intent_values,
#         'bot1_id': bot1_id_values,
#         'respuesta': respuesta_message_values,
#         'respuesta_type': respuesta_message_type_values
#     })
#     print("Se ha creado el DataFrame 'conv' correctamente.")
# else:
#     print("¡Error! Las listas tienen diferentes longitudes, no se pudo crear el DataFrame.")


# print("HASTA ACA LLEGUE ok 2")
# import sys
# sys.exit()

# Crea una nueva columna 'categoria' en 'conv' utilizando la función 'categoria'.
conv['categoria'] = [categoria(m, t, r) if m is not None else 'abandono' for m, t, r in zip(conv.respuesta, conv.respuesta_type, conv.intent)]

# Agrupa por 'categoria' y cuenta la cantidad de 'bot1_id' para cada categoría.
per = conv.groupby('categoria', as_index=False).count()[['categoria', 'bot1_id']]

# Calcula el porcentaje de cada categoría respecto al total.
per['per'] = per.bot1_id / per.bot1_id.sum()



# Concatena 'conv_cl' y 'conv' en un nuevo DataFrame 'usuario1', y agrega columnas adicionales.
usuario1 = pd.concat([conv_cl[['session_id', 'creation_time', 'original', 'intent', 'bot1_id', 'respuesta', 'respuesta_type', 'respuesta_rule']], conv])

# Crea una nueva columna 'categoria' en 'usuario1' utilizando la función 'categoria'.
usuario1['categoria'] = [categoria(m, t, r) if m is not None else 'abandono' for m, t, r in zip(usuario1.respuesta, usuario1.respuesta_type, usuario1.intent)]

# Crea una nueva columna 'usuario' en 'usuario1' extrayendo los primeros 20 caracteres de 'session_id'.
usuario1['usuario'] = usuario1.session_id.str[:20]

# Crea una nueva columna 'id' en 'usuario1' copiando los valores de 'bot1_id'.
usuario1['id'] = usuario1.bot1_id



# #### Resultados

# In[22]:


# Análisis de resultados por usuario:

resultados=[]
promedios=[]

# Itera sobre el DataFrame 'usuario1'.
for usuario in [usuario1]:

    # Agrupa por 'usuario' y 'categoria', y cuenta la cantidad de 'id' para cada categoría.
    respuestas_por_usuario=usuario.groupby(['usuario','categoria'], as_index=False).count()[['usuario','categoria', 'id']].pivot_table('id', ['usuario'], 'categoria')
    respuestas_por_usuario.fillna(0, inplace=True)

    # Reordena las columnas del DataFrame 'respuestas_por_usuario'.
    respuestas_por_usuario=respuestas_por_usuario.reset_index(drop=False).reindex(['usuario', 'abandono', 'boton', 'otros', 'texto', 'x', 'cambiar'], axis=1)

    # Calcula los porcentajes para cada categoría.
    respuestas_por_usuario['porcentaje_abandono']=[respuestas_por_usuario.loc[i].abandono / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]
    respuestas_por_usuario['porcentaje_boton']=[respuestas_por_usuario.loc[i].boton / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]
    respuestas_por_usuario['porcentaje_otros']=[respuestas_por_usuario.loc[i].otros / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]
    respuestas_por_usuario['porcentaje_texto']=[respuestas_por_usuario.loc[i].texto / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]
    respuestas_por_usuario['porcentaje_x']=[respuestas_por_usuario.loc[i].x / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]
    respuestas_por_usuario['porcentaje_cambiar']=[respuestas_por_usuario.loc[i].cambiar / respuestas_por_usuario.loc[i][['abandono', 'boton', 'otros', 'texto', 'x',  'cambiar']].sum() for i in respuestas_por_usuario.index]

    # Agrega el DataFrame 'respuestas_por_usuario' a la lista 'resultados'.
    resultados.append(respuestas_por_usuario)

    # Calcula los promedios de porcentajes para cada categoría y agrega a la lista 'promedios'.
    promedios.append({'abandonos': round(respuestas_por_usuario['porcentaje_abandono'].mean(), 3),     
                      'botones': round(respuestas_por_usuario['porcentaje_boton'].mean(), 3),
                      'otros': round(respuestas_por_usuario['porcentaje_otros'].mean(), 3),
                      'texto': round(respuestas_por_usuario['porcentaje_texto'].mean(), 3),
                      'x': round(respuestas_por_usuario['porcentaje_x'].mean(), 3),
                      'cambiar de tema': round(respuestas_por_usuario['porcentaje_cambiar'].mean(), 3)})



# In[23]:


pd.DataFrame(promedios, index=['nuevo-con-oss', 'nuevo-sin-oss'])[['abandonos', 'botones', 'texto', 'x', 'cambiar de tema', 'otros']]


# In[24]:


# Crea un nuevo diccionario 'con_oss1' multiplicando cada valor en 'promedios1' por 100.
con_oss1 = {k: v * 100 for k, v in promedios1.items()}

# Crea un nuevo diccionario 'con_oss2' multiplicando los valores correspondientes en 'promedios1' por las sumas ponderadas de 'click' y 'one' en 'promedios'.
con_oss2 = {k: (promedios1['click'] + promedios1['one']) * v * 100 for k, v in promedios[0].items()}


# In[25]:


con_oss1


# In[26]:


con_oss2


# In[ ]:




