import telnetlib
import ipaddress
from datetime import datetime
from datetime import date
import smtplib

#MAILS=["tu@email1","tu@email2"]
MAILS=["david.hernandezc@gmail.com"]

def envia_correo(asunto, mensaje):
    remitente = "david.hernandezc@gmail.com"
    destinatario = MAILS
    asunto="RIPETOOL: " + "ESPANA" + " "+ asunto
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
rangos=carga_rangos("rangos.txt")
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
            if ((line.find("12430")==-1)&(line.find("6739")==-1)):
                print("A borrar", ruta, origen)
    ruta=ruta.replace(" ", "")
    origen=origen.replace(" ", "")
    if (ruta!="")&(origen!=""):
        texto="El rango " + rango + " tiene objeto "+ ruta +" "+ origen
        #print (texto)
        log=log+texto+"<br>\n" 
    else:
        texto= "El rango " + rango + " NO tiene objeto route"
        texto2="""<p style="color:#FF0000";>El rango """ + rango + """ NO tiene objeto route</p>"""
        #print (texto)
        log=log+texto2+"<br>\n" 
        envia_correo(texto, texto2)
if hora.hour==0:
    envia_correo("Resumen diario",log)
print(log)

