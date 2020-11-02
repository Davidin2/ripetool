import telnetlib
import ipaddress
from datetime import datetime
from datetime import date
import smtplib
import configparser

AS=["AS1","AS2","AS3"]          #Lista de AS, tienen que ser 3
ID=""                           #Para diferenciar si tienes varias instancias corriendo
MAILS=["tu@email1","tu@email2"] #Direcciones de envío de mail

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
""" % (remitente, destinatario, asunto, mensaje)
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
log=""
fallo=0
hora = datetime.now()
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
hora_fin = datetime.now()
texto2="</table><BR>-------------End Date: " + str(hora_fin)
log=log + texto2

if (fallo>0):
    envia_correo(str(fallo)+ " RANGES WITH PROBLEMS in RIPE",log)
if hora.hour==0:
    envia_correo("Daily report",log)
print(log)

