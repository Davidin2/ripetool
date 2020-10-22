# Programmed by David Hernandez david.hernandezc@gmail.com year 2020
# https://github.com/Davidin2/dapings


import subprocess
import pickle
import ipaddress
import re
from random import randrange
from datetime import datetime
from datetime import date
import smtplib
import configparser

TESTEOS=0               #posicion en a lista en dic_rangos_contador
EXITOSOS=1              #posicion en a lista en dic_rangos_contador
EXITOSOS_SEGUIDOS=2     #posicion en a lista en dic_rangos_contador
FALLIDOS=3              #posicion en a lista en dic_rangos_contador
FALLIDOS_SEGUIDOS=4     #posicion en a lista en dic_rangos_contador
TESTEOS_24=5            #posicion en a lista en dic_rangos_contador
EXITOSOS_24=6           #posicion en a lista en dic_rangos_contador
EXITOSOS_SEGUIDOS_24=7  #posicion en a lista en dic_rangos_contador
FALLIDOS_24=8           #posicion en a lista en dic_rangos_contador
FALLIDOS_SEGUIDOS_24=9  #posicion en a lista en dic_rangos_contador
LOG_CADA=1              #Cada cuando escupimos log al fichero log.txt
BUSCA_IP_CADA=1         #Si un rango no tiene ips cada cuanto buscamos
GUARDA_DIC_CADA=1       #Cada cuando salvamos el diccionario de rangos ppal
MAIL_SI_FALLO=1         #Correo si falla un rango x veces seguidas
MAIL_SI_RECUPERA=1      #Correo cuando recupera un rango x veces seguidas
BUSCAIPS_SI_MENOS=10    #Busca IPs de nuevo si tiene menos de x
MAXIMAS_IP_POR_RANGO=50 #Cuantas IPs guarda de cada rango como máximo
MAXIMA_RED=21           #Si es más grande de X partimos la red en trozos como X
TRUNC_IPS=50            #Recorta las IPs a  (solo aplica si hay más de x al incio al cargar el diccionario). Nunca inferior a 6
ID=""                   #Para diferenciar si tienes varias instancias corriendo
MAILS=["tu@email1","tu@email2"] #Direcciones de envío de mail

def envia_correo(asunto, mensaje):
    remitente = "david.hernandezc@gmail.com"
    destinatario = MAILS
    asunto="DAPING: " + ID + " "+ asunto
    print("EMAIL with subject-->", asunto)
    email = """From: %s
To: %s
MIME-Version: 1.0
Content-type: text/html
Subject: %s
    
%s
""" % (remitente, destinatario, asunto, mensaje)
    try:
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(remitente, MAILS, email)
        print ("Email sent succesfully")
    except:
        print ("Error: we canot send the email")


def carga_rangos(fichero):
    try:
        with open(fichero, "r") as f:
            lista_rangos=[]
            print ("---------------Load ranges from",fichero,"---------------")
            for linea in f:
                try:
                    ip = ipaddress.IPv4Network(linea[:-1]) # para quitar el retorno de carro
                    print(ip, "it is a correct network")
                    lista_rangos.append(linea[:-1]) 
                except ValueError:
                    print(linea, "it is a incorrect network. Not loaded")
            print ("---------------Loaded Ranges---------------")
            print(lista_rangos)
            return lista_rangos
    except (OSError, IOError) as e:
        print ("---------------No ranges to load---------------")
        return list()   

def guarda_diccionario(dic,nombre_fichero):
    with open(nombre_fichero, "wb") as f:
        pickle.dump(dic, f)
    print("---------------Dicc saved---------------")
    #print (dic)

def carga_diccionario(nombre_fichero):
    global TRUNC_IPS
    try:
        with open(nombre_fichero, "rb") as f:
            dic_cargado=pickle.load(f)
            print ("---------------Loaded Dicc---------------")
            for rango in dic_cargado.keys(): #truncamos ips
                if TRUNC_IPS<10:
                    TRUNC_IPS=10 # como minimo debería ser 10 para no cargarnos el diccionario de contadores
                if len(dic_cargado[rango])>TRUNC_IPS:
                    dic_cargado[rango]=dic_cargado[rango][0:TRUNC_IPS]
            #print(dic_cargado)
            return dic_cargado
    except (OSError, IOError) as e:
        print ("---------------No Dicc to load---------------")
        return dict()

def busca_ips_en_rango(rango):

    print ("---------------Searching IPs in range", rango)
    network=ipaddress.ip_network(rango)
    mascara=network.prefixlen
    if mascara > MAXIMA_RED-1:
        result = subprocess.run(["fping", "-gaq", str(rango)], capture_output=True, text=True)
    else:  #Si el rango es <max_red seleccionamos uno de los max_red dentro de el
        lista_subredes=list(network.subnets(new_prefix=MAXIMA_RED)) #Spliteamos en max_red
        seleccionada=randrange(len(lista_subredes)) #Selecciona entre 0 y len-1
        print ("---------------Select to ping", seleccionada, "of",len(lista_subredes), str(lista_subredes[seleccionada]))
        result = subprocess.run(["fping", "-gaq", str(lista_subredes[seleccionada])], capture_output=True, text=True)
    lista_salida=result.stdout.splitlines() #result.stdout.splitlines es una lista de lineas con la salida del fping. Intentar limitar a 50 pings maximo, no tiene sentido tener mas.
    print("---------------Range", rango, "processed, ", len(lista_salida), "ips answer ping")
    if len(lista_salida) > MAXIMAS_IP_POR_RANGO:
        lista_salida=lista_salida[0:MAXIMAS_IP_POR_RANGO]
    return (lista_salida)

def carga_config():
    global LOG_CADA
    global BUSCA_IP_CADA
    global GUARDA_DIC_CADA
    global MAIL_SI_FALLO
    global MAIL_SI_RECUPERA
    global BUSCAIPS_SI_MENOS
    global MAXIMAS_IP_POR_RANGO
    global MAXIMA_RED
    global TRUNC_IPS
    global ID
    global MAILS
   
    config = configparser.ConfigParser()
    try:
        with open ('daping.ini') as f:  #Falta gestionar si un id no existe en el fichero
            config.read_file(f)
            if 'LOG_CADA' in config['default']:
                LOG_CADA=int(config['default']['LOG_CADA'])
            if 'BUSCA_IP_CADA' in config['default']:
                BUSCA_IP_CADA=int(config['default']['BUSCA_IP_CADA'])
            if 'GUARDA_DIC_CADA' in config['default']:
                GUARDA_DIC_CADA=int(config['default']['GUARDA_DIC_CADA'])
            if 'MAIL_SI_FALLO' in config['default']:
                MAIL_SI_FALLO=int(config['default']['MAIL_SI_FALLO'])
            if 'MAIL_SI_RECUPERA' in config['default']:
                MAIL_SI_RECUPERA=int(config['default']['MAIL_SI_RECUPERA'])
            if 'BUSCAIPS_SI_MENOS' in config['default']:
                BUSCAIPS_SI_MENOS=int(config['default']['BUSCAIPS_SI_MENOS'])
            if 'MAXIMAS_IP_POR_RANGO' in config['default']:
                MAXIMAS_IP_POR_RANGO=int(config['default']['MAXIMAS_IP_POR_RANGO'])
            if 'MAXIMA_RED' in config['default']:
                MAXIMA_RED=int(config['default']['MAXIMA_RED'])
            if 'TRUNC_IPS' in config['default']:
                TRUNC_IPS=int(config['default']['TRUNC_IPS'])
            if 'ID' in config['default']:
                ID=config['default']['ID']
            if 'MAILS' in config['default']:
                MAILS=config['default']['MAILS'].split(sep=',')
            print("Configuration loaded")
    except (OSError, IOError) as e:
        print ("No configuration file")

def print_config():
    config="\r\nCurrent configuration:\r\n<BR>"
    config=config + "Log to file every x pass: " + str(LOG_CADA) + "\r\n<BR>"
    config=config + "Search IPs every x pass: " + str(BUSCA_IP_CADA) + "\r\n<BR>"
    config=config + "Save dicc every x pass: " + str(GUARDA_DIC_CADA) + "\r\n<BR>"
    config=config + "EMAIL if range fail: " + str(MAIL_SI_FALLO) + "\r\n<BR>"
    config=config + "EMAIL if range recover: " + str(MAIL_SI_RECUPERA) + "\r\n<BR>"
    config=config + "Search IP if less than: " + str(BUSCAIPS_SI_MENOS) + "\r\n<BR>"
    config=config + "MAX IP to search in a range: " + str(MAXIMAS_IP_POR_RANGO) + "\r\n<BR>"
    config=config + "MAX prefix network to search IP: " + str(MAXIMA_RED) + "\r\n<BR>"
    config=config + "Lmit IPs in range to: " + str(TRUNC_IPS) + "\r\n<BR>"
    config=config + "ID: " + ID + "\r\n<BR>"
    config=config + "EMAILS: " + ",".join(MAILS) + "\r\n<BR>"
    return (config)

def limpia_html(value):
    return re.sub(r'<[^>]*?>', '', value)      

def main():
    carga_config()
    fecha_inicio = date.today()
    dic_rangos_contador={}
    dic_rangos={} #Diccionario con rango (key) y lista de ips que responden (value)
    dic_rangos=carga_diccionario("dic_rangos.dat")
    dic_rangos_contador=carga_diccionario("dic_rangos_cont.dat")
    if dic_rangos_contador =={}: # si no hay fichero de contador lo inicializamos
        for rango in dic_rangos.keys():
            dic_rangos_contador[rango]=[0,0,0,0,0,0,0,0,0,0]  # testeos, exitosos, fallidos, ver constantes

    rangos=carga_rangos("nuevos_rangos.txt")
        #Buscar IPs en Rangos y rellenamos diccionario:
    for rango in rangos:      #En cada rango de la lista
        if rango not in dic_rangos: # Añadimos rango si no existe
            dic_rangos[rango]=busca_ips_en_rango(rango)  #Añadimos al diccionario las ips que responden       
            dic_rangos_contador[rango]=[0,0,0,0,0,0,0,0,0,0]
            print(rango, "loaded ")
        else:
            print(rango, "not loaded, already in tool")
        #Borramos rangos desde fichero
    rangos_a_borrar=carga_rangos("borrar_rangos.txt")
    for rango in rangos_a_borrar:      #En cada rango de la lista
        if rango in dic_rangos:
            #lo borramos
            del (dic_rangos[rango])
            del (dic_rangos_contador[rango])
            print(rango, "deleted ")
        else:
            print(rango, "not deleted, range not in tool")
    #Pendiente imprimir al log el dic y count  
    print ("---------------Going in control mode---------------------")
    #print(dic_rangos)
    # Ver si las IPs de un diccionario de rangos siguen respondiendo. Si una IP no responde la elimina de la lista
    testeo=0
    
    while True:
        testeo+=1
        num_ips=0
        num_rangos=0
        num_ips_ping=0
        for rango in dic_rangos.keys():
            network=ipaddress.ip_network(rango)
            num_ips+=network.num_addresses  
            num_rangos+=1
            num_ips_ping+=len(dic_rangos[rango])
        logfile=open("ultimo.log", "w") 
        print ("------------------Start time",datetime.now(),"------------------------<BR>", file=logfile)
        print ("Checking", num_rangos, "ranges and",num_ips,"ips. Ping to",num_ips_ping,"""ips.<BR><BR><BR><TABLE BORDER="1">""", file=logfile)
        print ("<TR><TH>RANGE</TH><TH>IP ALIVE</TH><TH>[Tests OK CONSECUTIVE_OK FAIL CONSECUTIVE_FAIL]</TH><TH>Last 24h</TH></TR>", file=logfile)
        fecha_actual=date.today() #Para mandar un correo una vez solo cuando cambiamos de día
        print("------------------------","Testing number", testeo, "-----------------------")
        print ("Checking", num_rangos, "ranges and",num_ips,"ips. Ping to",num_ips_ping,"ips.")
        print ("[Tests OK CONSECUTIVE_OK FAIL CONSECUTIVE_FAIL]")
        for rango in dic_rangos.keys():     # Por cada rango en el diccionario
            if len(dic_rangos[rango])>0:    # Si tiene al menos una ip que responde
                comando= ["fping", "-aq"]
                comando+=dic_rangos[rango]      # Generamos el comando fping a cada ip
                result = subprocess.run(comando, capture_output=True, text=True)
                posicion=0  # Itero la lista de ips que responden del rango
                while posicion<len(dic_rangos[rango]):
                    if result.stdout.find(dic_rangos[rango][posicion]+"\n")>-1: # devuelve -1 si no la encuentra. Añadimos \n para no confundir las ip 1.1.1.1 con 1.1.1.11
                        #print("La IP",dic_rangos[rango][posicion] , "ha respondido")
                        posicion+=1
                    else:
                        #print("La IP", dic_rangos[rango][posicion] , "No ha respondido y la eliminamos de la lista")
                        dic_rangos[rango].pop(posicion) # Borro la ip que no responde. No incremento la posicion pq al borrarla ese numero es la siguiente posicion
                if len(dic_rangos[rango])<BUSCAIPS_SI_MENOS: # si tiene menos del limite 
                    if testeo % BUSCA_IP_CADA == 0: #Y además toca buscar
                        print ("Range",rango ,"with only",len(dic_rangos[rango]),"ip, searching more ips)")
                        dic_rangos[rango]+=busca_ips_en_rango(rango)
                        #podríamos quitar ips duplicadas, aunque puede ser interesante no hacerlo para que si no encuentra más no se quede siempre buscando
                
                if  len(dic_rangos[rango])>0:
                    dic_rangos_contador[rango][EXITOSOS]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS]=0
                    dic_rangos_contador[rango][EXITOSOS_24]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS_24]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS_24]=0
                    dic_rangos_contador[rango][TESTEOS]+=1
                    dic_rangos_contador[rango][TESTEOS_24]+=1
                    print(rango, len(dic_rangos[rango]),"IPs answer ping.", dic_rangos_contador[rango][0:5],"Last 24h:", dic_rangos_contador[rango][5:10])
                    print("<TR><TD>", rango,"</TD><TD>", len(dic_rangos[rango]),"</TD><TD>", dic_rangos_contador[rango][0:5],"</TD><TD>", dic_rangos_contador[rango][5:10], "</TD></TR>", file=logfile)
                else:
                    dic_rangos_contador[rango][FALLIDOS]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS]=0
                    dic_rangos_contador[rango][FALLIDOS_24]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS_24]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS_24]=0
                    dic_rangos_contador[rango][TESTEOS]+=1
                    dic_rangos_contador[rango][TESTEOS_24]+=1
                    print ("**********ALERT", rango, "WITHOUT IP.", dic_rangos_contador[rango][0:5],"Last 24h:", dic_rangos_contador[rango][5:10])
                    print ("""<TR bgcolor= "red"><TD>**ALERT**""", rango, "</TD><TD>0</TD><TD>", dic_rangos_contador[rango][0:5],"</TD><TD>", dic_rangos_contador[rango][5:10],"</TD></TR>", file=logfile)
            else:
                if testeo % BUSCA_IP_CADA == 0: #Testeamos rangos con 0
                    dic_rangos[rango]=busca_ips_en_rango(rango)
                if len(dic_rangos[rango])==0: #buscamos y no hemos encontrado
                    dic_rangos_contador[rango][FALLIDOS]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS]=0
                    dic_rangos_contador[rango][TESTEOS]+=1
                    dic_rangos_contador[rango][FALLIDOS_24]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS_24]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS_24]=0
                    dic_rangos_contador[rango][TESTEOS_24]+=1
                    print ("**********ALERT", rango, "WITHOUT IP.", dic_rangos_contador[rango][0:5],"Last 24h:", dic_rangos_contador[rango][5:10])
                    print ("""<TR bgcolor= "red"><TD>**ALERT**""", rango, "</TD><TD>0</TD><TD>", dic_rangos_contador[rango][0:5],"</TD><TD>", dic_rangos_contador[rango][5:10],"</TD></TR>", file=logfile)
                else: #Hemos encontrado despues de buscar
                    dic_rangos_contador[rango][EXITOSOS]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS]=0
                    dic_rangos_contador[rango][EXITOSOS_24]+=1
                    dic_rangos_contador[rango][EXITOSOS_SEGUIDOS_24]+=1
                    dic_rangos_contador[rango][FALLIDOS_SEGUIDOS_24]=0
                    dic_rangos_contador[rango][TESTEOS]+=1
                    dic_rangos_contador[rango][TESTEOS_24]+=1
                    print(rango, len(dic_rangos[rango]),"IPs answer ping.", dic_rangos_contador[rango][0:5],"Last 24h:", dic_rangos_contador[rango][5:10])
                    print("<TR><TD>", rango,"</TD><TD>", len(dic_rangos[rango]),"</TD><TD>", dic_rangos_contador[rango][0:5],"</TD><TD>", dic_rangos_contador[rango][5:10], "</TD></TR>", file=logfile)
            if dic_rangos_contador[rango][FALLIDOS_SEGUIDOS] == MAIL_SI_FALLO:
                texto="FAIL in range " + rango + ". [Tests TOTAL_OK CONSECUTIVE_OK FAIL CONSECUTIVE_FAIL] " + str(dic_rangos_contador[rango][0:5]) + " Last 24h: "+ str(dic_rangos_contador[rango][5:10])
                print (texto)
                envia_correo(texto, texto)
            if dic_rangos_contador[rango][EXITOSOS_SEGUIDOS] == MAIL_SI_RECUPERA: 
                if dic_rangos_contador[rango][EXITOSOS_SEGUIDOS] != dic_rangos_contador[rango][TESTEOS]: # controlamos que no sea al arranque
                    texto="Recover range " + rango + ". [Tests TOTAL_OK CONSECUTIVE_OK FAIL CONSECUTIVE_FAIL] " + str(dic_rangos_contador[rango][0:5])+" Last 24h: "+ str(dic_rangos_contador[rango][5:10])
                    print (texto)
                    envia_correo(texto, texto)
        print ("</TABLE>------------------END TIME",datetime.now(),"------------------------<BR><BR><BR><BR>", file=logfile)
        logfile.close()
        logfile2=open("ultimo.log", "r")
        logfile3=open("ultimo.txt", "w") # lo copiamos a .txt pq el .log al estar abierto siempre no tiene toda la info
        for linea in logfile2:
            print (linea[:-1], file=logfile3)
        logfile2.close()
        print (print_config(), file=logfile3)
        logfile3.close()
        if fecha_inicio.day != fecha_actual.day:   #Si hay que mandar mail
            mailfile=open("ultimo.txt", "r")
            texto=""
            for linea_log in mailfile:
                texto=texto+linea_log
            envia_correo("Daily Ping Report", texto)
            fecha_inicio=date.today()
            mailfile.close()
            for rango in dic_rangos.keys(): #reseteamos contadores diarios tras mandar el mail
                dic_rangos_contador[rango][FALLIDOS_24]=0
                dic_rangos_contador[rango][FALLIDOS_SEGUIDOS_24]=0
                dic_rangos_contador[rango][EXITOSOS_SEGUIDOS_24]=0
                dic_rangos_contador[rango][EXITOSOS_24]=0
                dic_rangos_contador[rango][TESTEOS_24]=0
        if testeo % LOG_CADA ==0:      #lo añadimos al log general
            logfile4=open("daping.log","a+")
            logfile5=open("ultimo.log", "r")      
            for linea_log in logfile5:
                linea_log=limpia_html(linea_log)
                print (linea_log[:-1], file=logfile4)
            logfile4.close()
            logfile5.close()
        if testeo % GUARDA_DIC_CADA == 0: #Guardamos diccionario
            guarda_diccionario(dic_rangos,"dic_rangos.dat")
            guarda_diccionario(dic_rangos_contador,"dic_rangos_cont.dat")
        
if __name__ == '__main__':
    main()

#Mejoras a futuro: 
    #1 proceso hace pings buscando ips mientras otro testea las existentes en paralelo



