import telnetlib
import ipaddress
from datetime import datetime
from datetime import date
import smtplib
import configparser

ID=""                   #Para diferenciar si tienes varias instancias corriendo
MAILS=["tu@email1","tu@email2"] #Direcciones de envío de mail

def carga_config():
    global MAILS
    config = configparser.ConfigParser()
    try:
        with open ('ripetool.ini') as f:  #Falta gestionar si un id no existe en el fichero
            config.read_file(f)
            if 'MAILS' in config['default']:
                MAILS=config['default']['MAILS'].split(sep=',')
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

HOST = "whois.ripe.net"
COMANDO="-T route -xr --sources RIPE "
log=""
hora = datetime.now()
log="Fecha actual: " + str(hora) + "<BR>\n"
texto=log
texto2=""
#rangos=carga_rangos("/home/ubuntu/ripe_espana/rangos.txt")
rangos=carga_rangos("rangos.txt")
carga_config()
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
        if ((origen.find("12430")==-1)&(origen.find("6739")==-1)):
            texto="El rango " + rango + " tiene objeto "+ ruta +" "+ origen + " Ojo,no es nuestro"
            texto2="""<p style="color:#FF0000";>El rango """  + rango + " tiene objeto "+ ruta +" "+ origen + " Ojo,no es nuestro</p>"
            envia_correo(texto, texto2)
        else:
            texto2="El rango " + rango + " tiene objeto "+ ruta +" "+ origen
        #print (texto)
        log=log+texto2+"<br>\n" 
    else:
        texto= "El rango " + rango + " NO tiene objeto route"
        texto2="""<p style="color:#FF0000";>El rango """ + rango + """ NO tiene objeto route</p>"""
        #print (texto)
        log=log+texto2+"<br>\n" 
        envia_correo(texto, texto2)
if hora.hour==0:
    envia_correo("Resumen diario",log)
print(log)

