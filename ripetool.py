import telnetlib
import ipaddress
from datetime import datetime
from datetime import date
import smtplib
import configparser

AS=["AS1","AS2","AS3"]          #Lista de AS, tienen que ser 3
ID=""                           #Para diferenciar si tienes varias instancias corriendo
MAILS=["tu@email1","tu@email2"] #Direcciones de envío de mail
PREFIX_DIFF=20            #diferencia de prefijos para mandar mail en valor absoluto

def carga_config():
    global MAILS
    global ID
    global AS
    config = configparser.ConfigParser()
    try:
        with open ('ripetool.ini') as f:  #Falta gestionar si un id no existe en el fichero
            config.read_file(f)
            if 'ID' in config['default']:
                ID=config['default']['ID']
            if 'MAILS' in config['default']:
                MAILS=config['default']['MAILS'].split(sep=',')
            if 'AS' in config['default']:
                AS=config['default']['AS'].split(sep=',')
            if 'PREFIX_DIFF' in config['default']:
                PREFIX_DIFF=config['default']['PREFIX_DIFF']


    except (OSError, IOError) as e:
        print ("No configuration file")

def print_config():
    config="\r\nCurrent configuration:\r\n<BR>"
    config=config + "ID: " + ID + "\r\n<BR>"
    config=config + "EMAILS: " + ",".join(MAILS) + "\r\n<BR>"
    return (config)


def envia_correo(asunto, mensaje):
    remitente = "david.hernandezc@gmail.com"
    destinatario = MAILS
    asunto="RIPETOOL: " + ID + " " + asunto
    #print("EMAIL with subject-->", asunto)
    email = """From: %s
To: %s
MIME-Version: 1.0
Content-type: text/html
Subject: %s
    
%s
""" % (remitente, ",".join(destinatario), asunto, mensaje)
    try:
        smtp = smtplib.SMTP('localhost')
        smtp.sendmail(remitente, MAILS, email)
        #print ("Email sent succesfully")
    except:
        print ("Error: we canot send the email<BR>")


def carga_rangos(fichero):
    try:
        with open(fichero, "r") as f:
            lista_rangos=[]
            #print ("---------------Load ranges from",fichero,"---------------")
            for linea in f:
                try:
                    ip = ipaddress.IPv4Network(linea[:-1]) # para quitar el retorno de carro
                    #print(ip, "it is a correct network")
                    lista_rangos.append(linea[:-1]) 
                except ValueError:
                    print(linea, "it is a incorrect network. Not loaded")
            #print ("---------------Loaded Ranges---------------")
            return lista_rangos
    except (OSError, IOError) as e:
        print ("---------------No ranges to load---------------")
        return list()   

carga_config()
HOST = "whois.ripe.net"
COMANDO="-T route -xr --sources RIPE "
COMANDO2="-i origin -T route -r --sources RIPE as"
log=""
fallo=0
hora = datetime.now().replace(microsecond=0)
rangos=carga_rangos("rangos.txt")
log="-------------Start Date: " + str(hora) + "-------------<BR>RIPETOOL " + ID + " " + str(len(rangos)) + " Rangos<BR>\n"
texto=log
texto2="""<TABLE BORDER="1"> <TR><TH>RANGE</TH><TH>STATUS</TH><TH>OBJECT IN RIPE</TH></TR>"""
log=log+texto2
texto2=""
for rango in rangos:
    ruta=""
    origen=""
    tn = telnetlib.Telnet(HOST,43)
    comando=COMANDO+rango
    tn.write(comando.encode('ascii')+ b"\n")
    result=tn.read_all().decode('ascii', 'ignore')
    lista_result=result.splitlines()
    for line in lista_result:
        if line.find("route:")>-1:
            ruta=line
        if line.find("origin:")>-1:
            origen=line
    ruta=ruta.replace(" ", "")
    origen=origen.replace(" ", "")


    if (ruta!="")&(origen!=""):
        if ((origen.find(AS[0])==-1)and(origen.find(AS[1])==-1)and(origen.find(AS[2])==-1)):
            texto="Range " + rango + " have route object "+ ruta +" "+ origen + " ALERT, It is not our AS"
            texto2="""<TR bgcolor="red"><TD>"""  + rango + "</TD><TD>Have route object but not our AS</TD><TD>"+ ruta +" "+ origen + "</TD></TR>"
            #envia_correo(texto, texto2)
            fallo+=1
        else:
            texto2="<TR><TD>" + rango + "</TD><TD>Have route object</TD><TD>" + ruta +" "+ origen + "</TD></TR>"
        #print (texto)
    else:
        texto= "Range " + rango + " DOES NOT have route object"
        texto2="""<TR bgcolor="red"><TD>""" + rango + "</TD><TD>DOES NOT have route object</TD><TD></TD></TR>"
        #print (texto)
        #envia_correo(texto, texto2)
        fallo+=1
    log=log+texto2 
log= log + "</table>"


num_prefijos_antes=-1
lista_prefijos_antes=[]
try:
    with open("num_prefijos.txt", "r") as fichero_prefijos:
        for linea in fichero_prefijos:
            lista_prefijos_antes.append(linea[:-1])
        num_prefijos_antes=lista_prefijos_antes[0]
except(OSError, IOError) as e:
        print ("There is no files with last prefix sample")


lista_prefijos_ahora=[]

for ass in AS:

    tn = telnetlib.Telnet(HOST,43)
    comando=COMANDO2+ass
    tn.write(comando.encode('ascii')+ b"\n")
    result=tn.read_all().decode('ascii', 'ignore')
    lista_result=result.splitlines()
    for line in lista_result:
        if line.find("route:")>-1:
            ruta=line
            ruta=ruta.replace(" ", "")
            ruta=ruta.replace("route:", "")
            ruta=ruta+" AS"+ ass
            lista_prefijos_ahora.append(ruta)




num_prefijos_ahora=len(lista_prefijos_ahora)
diferencia_de_rutas=num_prefijos_ahora-int(num_prefijos_antes)
texto="<br><br>Route objects: " + str(num_prefijos_ahora)
log=log+texto
texto="<br><br>Last sample Route objects: " + str(num_prefijos_antes)
log=log+texto

with open("num_prefijos.txt", "w") as fichero_prefijos:
    fichero_prefijos.write(str(num_prefijos_ahora)+"\n")
    for prefijo in lista_prefijos_ahora:
        fichero_prefijos.write(str(prefijo)+"\n")
no_esta_ahora=[]
no_estaba_antes=[]

for prefijo_antes in lista_prefijos_antes:
    if "/" in str(prefijo_antes):
        if prefijo_antes not in lista_prefijos_ahora:
            no_esta_ahora.append(prefijo_antes)
for prefijo_ahora in lista_prefijos_ahora:
    if "/" in str(prefijo_ahora):
        if prefijo_ahora not in lista_prefijos_antes:
            no_estaba_antes.append(prefijo_ahora)


texto="<br><br>These prefixes were before and now they are not: " + str(no_esta_ahora)
log=log+texto
texto="<br><br>These prefixes are now and they were not before: " + str(no_estaba_antes)
log=log+texto

hora_fin = datetime.now().replace(microsecond=0)
texto2="<BR>-------------End Date: " + str(hora_fin)
log=log + texto2

if (fallo>0):
    envia_correo(str(fallo)+ " RANGES WITH PROBLEMS in RIPE",log)
if ((diferencia_de_rutas>int(PREFIX_DIFF)) or (diferencia_de_rutas<-int(PREFIX_DIFF))):
    envia_correo("Sudden change of  " + str(diferencia_de_rutas) + " route objects in RIPE from the previous sample",log)
if hora.hour==0:
    envia_correo("Daily report",log)
print(log)

logfile=open("lista_cambios.txt", "a")
for prefijo in no_esta_ahora:
    print(str(hora_fin)+" - "+ str(prefijo), file=logfile)
for prefijo in no_estaba_antes:
    print(str(hora_fin)+" + "+ str(prefijo), file=logfile)

logfile.close()
