    ## Importación de bibliotecas ##
import random
import numpy


    ## Declaración de variables ##
t_simulacion = 0 #tiempo general de la simulación
#variables de configuración de red
posibles_numeros_nodos = [5, 10, 15, 20]
numero_nodos = posibles_numeros_nodos[0] #N 5 3
numero_grados = 7 #I 7 
tamanio_buffer = 15 #k 15 
num_miniranuras = 16 #W 16 
ranuras_sleep = 18 
ciclos_a_evaluar = 300000
#paquetes para el envío-recepción
DIFS = 10
SIFS = 5
durRTS = 11
durCTS = 11
durACK = 11
durDATA = 43
sigma = 1
t_slot = durDATA+durRTS+durCTS+DIFS+durACK+sigma*num_miniranuras+3*SIFS
#variables para calcular t_arribo
posibles_lambas = [0.0005, 0.005, 0.03]
lambda1 = posibles_lambas[0]
lambda2 = lambda1*numero_nodos*numero_grados
multiplier = 1000000
u = (multiplier*random.random())/(multiplier)
nuevo_t = -1*(1/lambda2)*numpy.log(1-u)
t_arribo = 0
    # Variables de registro y para gráficas #
registro_nodos = {} 
registro_paquetes = {}
id_paquete = 0 #irá aumentando para darle un id a cada paquete que se genere y tambien es la cantidad total de paquetes generados
paquetes_perdidos = [] #numero de paquetes perdidos por cualquier causa, comenzando en 1 
paquetes_sink = 0 #contiene la cantidad de paquetes que llegaron al nodo sink
retardos_promedio = [] #almacena los retardos promedio por grado empezando en 1
throughput = []
retardos_promedio_multiples = [] #almacena las listas de retardos promedio de cada simulacion
paquetes_perdidos_multiples = [] #almacena las listas de paquetes perdidos de cada simulacion




    ## Declaración de funciones ##
    
    #función que registra los nodos en el diccionario que lleva el control de los nodos y sus buffers# 
def creacion_nodos():
    for grado in range(1, numero_grados+1):
        for nodo in range(1, numero_nodos+1):
            clave = str(grado) + '-' + str(nodo) #agrega el id según el nodo y grado en el que se encuentre
            registro_nodos[clave] = {}
            registro_nodos[clave]['buffer'] = [] #agrega al nodo un buffer de transmisión vacio     
            registro_nodos[clave]['grado'] = grado #agrega al nodo su grado     


    #función que genera un paquete y lo registra en su diccionario además de agregarlo al buffer de su nodo asignado#
def sensado():
    global id_paquete
    global t_arribo
    
    grado_select = random.randint(1, numero_grados)
    nodo_select = random.randint(1, numero_nodos) #genera aleatoriamente a qué nodo se asigna 
    clave = str(grado_select) + '-' + str(nodo_select) #para agregarlo a esa clave en el diccionario de nodos
    
    #registro general del paquete sin importar si se pierde o no
    id_paquete = id_paquete + 1 #genera el id del paquete
    registro_paquetes[id_paquete] = {} #se registra en el diccionario de paquetes
    registro_paquetes[id_paquete]['grado asignado'] = grado_select
    registro_paquetes[id_paquete]['nodo asignado'] = nodo_select
    registro_paquetes[id_paquete]['tiempo de generacion'] = t_simulacion
    registro_paquetes[id_paquete]['llegado'] = 'no'
    
    if len(registro_nodos[clave]['buffer']) >= tamanio_buffer: #si no hay espacio en el buffer
        registro_paquetes[id_paquete]['perdido'] = True 
        #paquetes_perdidos[grado_select-1] = paquetes_perdidos[grado_select-1] + 1 #se pierde en grado con nodo con buffer lleno 
    else: #si hay espacio en el buffer
        registro_nodos[clave]['buffer'].insert(0, id_paquete) #se agrega al buffer del nodo seleccionado
        registro_paquetes[id_paquete]['grados recorridos'] = 1
        if grado_select == 1: #si se generó en el grado 1
            registro_paquetes[id_paquete]['proximo nodo'] = 'sink'
        else:
            registro_paquetes[id_paquete]['proximo nodo'] = str(registro_paquetes[id_paquete]['grado asignado'] - registro_paquetes[id_paquete]['grados recorridos']) + '-' + str(nodo_select)
    
    nuevo_t = -1*(1/lambda2)*numpy.log(1-u)
    #t_arribo = t_simulacion + nuevo_t
    t_arribo = ((t_arribo + 2*t_simulacion)/3) + nuevo_t

    #función que hace el proceso de competencia para transmitir entre los nodos de un grado, si existe mas de un ganador registra los paquetes correspondientes como colisiones y si solo gana uno, retorna el paquete que está en la última posición del buffer del nodo ganador#
        #parámetros: grado_analizado - el grado en el que se llevará a cabo el proceso
        #retorno: id_paquete_transmitir - en caso de un único ganador envía el id del último paquete en el buffer, de otra forma se retorna -1
def ventana(grado_analizado):
    nodos_ganadores = []
    miniranura_menor = 500 #lleva cual es el numero de backoff mas chico que ha salido
    #cuando encuentra un nodo con algo que transmitir escoge un número de backoff, el más chico (o sus empates) se guardan en nodos_ganadores
    for key, nodo in registro_nodos.items():
        if nodo['grado'] == grado_analizado and len(nodo['buffer']) > 0:
            numero_backoff = random.uniform(1, num_miniranuras)
            numero_backoff = round(numero_backoff, 0)
            if numero_backoff == miniranura_menor:
                nodos_ganadores.append(key)  
            elif numero_backoff < miniranura_menor:
                nodos_ganadores = []
                nodos_ganadores.append(key)
                miniranura_menor = numero_backoff
                
    #cuando hay mas de un ganador entonces sí lo elimina de los buffers de tx pero en el registro de paquetes quedan como colisionados y nunca se agregan a su destino
    if len(nodos_ganadores) > 1: 
        for clave_nodo in nodos_ganadores:
            id_paquete_colision = registro_nodos[clave_nodo]['buffer'].pop()
            registro_paquetes[id_paquete_colision]['perdido'] = True
            #paquetes_perdidos[grado_analizado-1] = paquetes_perdidos[grado_analizado-1] + 1 #perdidos en grado con nodos con colisiones
            return -1
    elif len(nodos_ganadores) == 1: #si solo hay un ganador, lo retorna
        nodo_ganador = nodos_ganadores.pop()
        id_paquete_transmitir = registro_nodos[nodo_ganador]['buffer'].pop() #se saca del buffer del emisor y comenzar tx
        return id_paquete_transmitir
    else:
        return -1


    #función que transmite el paquete del nodo ganador a un nodo receptor no sink, si el buffer del nodo receptor está vacio, se registra como perdido. En caso contrario, se agrega al buffer del receptor. Aumenta el t_simulacion en un slot#
        #parámetros: id_paquete_transmitir - paquete por transmitir del único ganador de la ventana
                    #nodo_receptor - nodo al que se enviará el paquete a transmitir
def transmision(id_paquete_transmitir, nodo_receptor):
    global t_simulacion
    
    #revisa que el nodo receptor tenga espacio en su buffer
    if len(registro_nodos[nodo_receptor]['buffer']) >= tamanio_buffer: #si no hay espacio en el buffer se registra como perdido en tx
        registro_paquetes[id_paquete_transmitir]['perdido'] = True
        grado_receptor = registro_nodos[nodo_receptor]['grado']
        #paquetes_perdidos[grado_receptor-1] = paquetes_perdidos[grado_receptor-1] + 1
    else: #si hay espacio, se transmite
        registro_nodos[nodo_receptor]['buffer'].insert(0, id_paquete_transmitir) #se agrega al buffer del receptor
        #modifica todo lo necesario en el diccionario de paquetes del paquete transmitido    
        registro_paquetes[id_paquete_transmitir]['grados recorridos'] = registro_paquetes[id_paquete_transmitir]['grados recorridos'] + 1
        if registro_paquetes[id_paquete_transmitir]['proximo nodo'][:1] == '1':
            registro_paquetes[id_paquete_transmitir]['proximo nodo'] = 'sink'
        else:
            registro_paquetes[id_paquete_transmitir]['proximo nodo'] = str(registro_paquetes[id_paquete_transmitir]['grado asignado'] - registro_paquetes[id_paquete_transmitir]['grados recorridos']) + '-' + str(registro_paquetes[id_paquete_transmitir]['nodo asignado']) #si es 1 debe ser sink
    
    t_simulacion = t_simulacion + t_slot #se aumenta porque ya ha pasado un slot de tx
    
    #función que registra el paquete como recibido en el nodo sink. Aumenta el t_simulacion en un slot#
        #parámetros: id_paquete_transmitir - id del paquete que se transmite del grado 1 al nodo sink
def transmision_a_sink(id_paquete_transmitir):
    global t_simulacion
    global paquetes_sink
    
    #no tiene que agregarse a ningun buffer, solo se agregan/modifican datos en el diccionario de paquetes
    registro_paquetes[id_paquete_transmitir]['grados recorridos'] = registro_paquetes[id_paquete_transmitir]['grados recorridos'] + 1 #8
    registro_paquetes[id_paquete_transmitir]['proximo nodo'] = '-'
    t_simulacion = t_simulacion + t_slot #se aumenta porque ya ha pasado un slot de tx
    registro_paquetes[id_paquete_transmitir]['tiempo hasta sink'] = t_simulacion - registro_paquetes[id_paquete_transmitir]['tiempo de generacion']
    paquetes_sink = paquetes_sink + 1
    registro_paquetes[id_paquete_transmitir]['llegado'] = 'si'
    

    ##Funciones complementarias##
    
    #función que calcula los retardos promedios de los nodos por grado
def calculo_retardos_promedio(): 
    contador_paquetes = 0
    retardo_promedio = 0
    grado_analizado = 1
    
    while grado_analizado <= numero_grados: #recorrera buscando paquetes de un grado específico en el diccionario 
        for paquete in registro_paquetes.values():
            if paquete['grado asignado'] == grado_analizado and 'tiempo hasta sink' in paquete: #cuando haga match uno y ese paquete haya llegado a sink, agrega su retardo a la suma total y aumenta el contador
                retardo_promedio = retardo_promedio + paquete['tiempo hasta sink']
                contador_paquetes = contador_paquetes + 1
        if contador_paquetes != 0:
            retardo_promedio = retardo_promedio / contador_paquetes #saca el promedio y lo agrega a la lista de retardos
        else:
            retardo_promedio = 0
        retardos_promedio.append(retardo_promedio)
        contador_paquetes = 0
        retardo_promedio = 0
        grado_analizado = grado_analizado + 1

    #función que calcula los paquetes perdidos agrupados por su nodo de origen    
def calculo_paquetes_perdidos():
    
    grado_analizado = 1
    contador_paquetes_perdidos = 0
    
    while grado_analizado <= numero_grados:
        for paquete in registro_paquetes.values():
            if paquete['grado asignado'] == grado_analizado and 'perdido' in paquete:
                contador_paquetes_perdidos = contador_paquetes_perdidos + 1
        paquetes_perdidos.append(contador_paquetes_perdidos)
        contador_paquetes_perdidos = 0
        grado_analizado = grado_analizado + 1
                
                
                
def imprimir_nodos(): #imprime diccionario de nodos de mejor manera
    for key, value in registro_nodos.items():
        print(str(key)+" "+str(value))    

def imprimir_paquetes(): #imprime diccionario de paquetes de mejor manera
    for key, value in registro_paquetes.items():
        print(str(key)+" "+str(value))
        

    ##Función General##
def simulacion():
    global t_simulacion
    global t_arribo
    global registro_nodos
    global registro_paquetes
    global id_paquete
    global paquetes_perdidos
    global paquetes_sink
    global retardos_promedio
    
    creacion_nodos() #creación de la red
    t_arribo = t_simulacion + nuevo_t    
    while(t_simulacion < ciclos_a_evaluar*t_slot): #condición general
        while(t_arribo <= t_simulacion): #condición para generación de paquete
            sensado() #generación de paquete
        grado_analizado = numero_grados #si no se cumple lo de antes, se dejan de generar paquetes y se procede a la operación de la red
        while grado_analizado > 0: #loop que recorre todos los grados para transmitir del mas alejado al 1
            id_paquete_transmitir = ventana(grado_analizado) #competencia por transmisión
            if id_paquete_transmitir != -1: #si hubo ganador
                nodo_receptor = registro_paquetes[id_paquete_transmitir]['proximo nodo']
                if nodo_receptor == 'sink': #transmite a sink si es el proximo de ese paquete
                    transmision_a_sink(id_paquete_transmitir)
                else: #si no, transmite al siguiente
                    transmision(id_paquete_transmitir, nodo_receptor)
            grado_analizado = grado_analizado - 1 #se acerca un grado hacia el sink
        t_simulacion = t_simulacion + t_slot*(ranuras_sleep+2-numero_grados) #despues de recorrer todos, aumenta un ciclo
    calculo_retardos_promedio() #calcula el retardo promedio de paquetes generados en cada grado
    calculo_paquetes_perdidos() #calcula los retardos perdidos por el grado en el que se generaron
    retardos_promedio_multiples.append(retardos_promedio) #agrega esos promedios al registro general
    paquetes_perdidos_multiples.append(paquetes_perdidos) #agrega los registros de paquetes perdidos al registro general
    throughput.append(paquetes_sink / 20*t_slot) 
    
    t_simulacion = 0
    t_arribo = 0
    registro_nodos = {} 
    registro_paquetes = {}
    id_paquete = 0 
    paquetes_perdidos = [] 
    paquetes_sink = 0 
    retardos_promedio = []    
    


    ## Flujo principal de la aplicación ## 
for cantidad_nodos in posibles_numeros_nodos:
    numero_nodos = cantidad_nodos   
    simulacion() 
numero_nodos = posibles_numeros_nodos[0]

for th in range(len(throughput)):
    throughput[th]=(throughput[th]*1e-5)

print('-----------Resultados variando el número de nodos-----------')
print('throughput normalizado')
print(throughput)
print('retardos promedio')
print(retardos_promedio_multiples)
print('paquetes perdidos')
print(paquetes_perdidos_multiples)

for lambda_en_curso in posibles_lambas:
    lambda1 = lambda_en_curso
    lambda2 = lambda1*numero_nodos*numero_grados
    nuevo_t = -1*(1/lambda2)*numpy.log(1-u)
    simulacion()

print('-----------Resultados variando lambda-----------')
print('throughput normalizado')
print(throughput)
print('retardos promedio')
print(retardos_promedio_multiples)
print('paquetes perdidos')
print(paquetes_perdidos_multiples)

