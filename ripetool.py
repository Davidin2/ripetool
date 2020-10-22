import telnetlib
import ipaddress

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

HOST = "whois.ripe.net"
COMANDO="-T route -xr --sources RIPE "
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
    if (ruta!="")&(origen!=""):
        print ("El rango " + rango + " tiene objeto route:")
        print (ruta)
        print (origen)
    else:
        print ("El rango " + rango + " NO tiene objeto route:")

