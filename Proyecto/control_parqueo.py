#proyecto_prototipo control parqueadero

#importamos todas las librerias necesarias
import network
import urequests as requests
from machine import Pin, SoftI2C, PWM
import ssd1306
import time
from random import randrange
import sys
# credenciales de red y la plataforma
wifi_ssid = "Dark"
wifi_password = "3i19-o1ru-abnr"
aio_key = "aio_ZxXp83YqJGcef74dWfKvW8KAGSYM"
username = "alejoproyectos"
feed_name = "controlparking"
# tupla con los numeros que se van a mostrar en el display y en la plataforma
tuplaNombres =("1","2","3","4","5","6","7","8","9","10","11","12","13","14","15", \
"16","17","18","19","20","21","22","23","24","25","26","27","28","29","30")
listaEstado = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]  # lista para actualizar el estado de las posiciones
sensorIngreso = Pin(34, Pin.IN)  # pin configurado como entrada digital
sensorSalida = Pin(35, Pin.IN)  # pin configurado como entrada digital
contador = 0  # variable para contar los espacios disponibles
dato = 0

p4 = Pin(14)            #definimos el pin para el pwm del servo.
servo = PWM(p4,freq=50) #generamos el objeto servo, donde definimos el pin y la freq de trabajo.
# ESP32 Pin assignment
i2c = SoftI2C(scl=Pin(22), sda=Pin(21)) #configuramos el software de comunicacion i2c
oled_width = 128  #definimos el tamaño de la pantalla
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)  #creamos un objeto con la configuracion de los pines para la pantalla
########################################################################################
########################################################################################
#creamos una funcion con las instrucciones para la conexion WIFI
def connect_wifi():
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.disconnect()
    wifi.connect(wifi_ssid,wifi_password)
    if not wifi.isconnected():
        print('connecting..')
        timeout = 0
        while (not wifi.isconnected() and timeout < 10):
            print(20 - timeout)
            timeout = timeout + 1
            time.sleep(1) 
    if(wifi.isconnected()):
        print('connected')
        print('Configuración de red (IP/netmask/gw/DNS):', wifi.ifconfig())
    else:
        print('not connected')
        sys.exit()        
########################################################################################
########################################################################################
#funcion para manejar el control cuando el parking se llena
# en esta fucion se mantiene el programa bloqueando el sensor de entrada y el acceso de mas vehiculos
# solo verificando el estado del sensor de salida para que se desocupe al menos un espacio
def parking_lleno():
    print("parkin lleno")
    oled.fill(0)
    oled.text('PARKING', 40, 20)
    oled.text(' NO DISPONIBLE', 5, 40)
    oled.show()
    while(True):
        estadoSalida = sensorSalida.value()  # leemos el estado del sensor de salida.
        if estadoSalida == 0:
            time.sleep_ms(100)
            estadoSalida = sensorSalida.value() # leemos el estado del sensor de salida.
            if estadoSalida == 0:
                while(True):
                    dato = randrange(30)
                    if listaEstado[dato] == 1:
                        listaEstado[dato] = 0
                        global contador
                        contador -= 1
                        oled.fill(0)
                        oled.text('PARKING', 40, 0)
                        oled.text('SALIENDO DE LA', 10, 20)
                        oled.text('POSICION', 35, 35)
                        oled.text(tuplaNombres[dato],58,54)
                        oled.show()
                        servo.duty(32)
                        time.sleep(5)
                        servo.duty(82)
                        oled.fill(0)
                        oled.text('PARKING', 40, 20)
                        oled.text('DISPONIBLE', 30, 40)
                        oled.show()
                        print(contador)
                        print("espacio disponible")
                        url = 'https://io.adafruit.com/api/v2/' + username + '/feeds/' + feed_name + '/data'
                        body = {'value': "OUT-"+ tuplaNombres[dato]}
                        headers = {'X-AIO-Key': aio_key, 'Content-Type': 'application/json'}
                        try:
                            r = requests.post(url, json=body, headers=headers)
                            print(r.text)
                        except Exception as e:
                            print(e)
                        break
                break
########################################################################################
########################################################################################
connect_wifi() # LLamamos la funcion que nos conecta a la red wifi
oled.text('PARKING', 40, 20)  #Imprimimos el primer mensaje en la pantalla
oled.text('DISPONIBLE', 30, 40)
oled.show()
########################################################################################
########################################################################################
#bucle principal del programa
while True:
    estadoIngreso = sensorIngreso.value() # leemos el estado del sensor de entrada.
    if estadoIngreso == 0:
        time.sleep_ms(100)  #generamos un retardo para verificar el estado del pin.
        estadoIngreso = sensorIngreso.value() # leemos el estado del sensor de entrada.
        if estadoIngreso == 0:
            while(True):  #generamos un bucle en donde revisamos todos los espacios hasta encontrar uno vacio
                dato = randrange(30) #hacemos la busqueda de manera aleatoria
                if listaEstado[dato]== 0: # verificamos si el espacionesta vacio o no
                    listaEstado[dato] = 1  # si enconrtramos el espacio vacio cambiamos su estado a 1
                    contador += 1 # aunmentamos el contador de espacios
                    print(contador)  # mostramos datos en consola
                    break
            print(dato)
            print(listaEstado)
            print("ubiquese en la posicion " + tuplaNombres[dato])
            oled.fill(0)  #limpiamos la pantalla
            oled.text('PARKING', 40, 0) # mostramos mensajes en la pantalla oled
            oled.text('INGRESE A LA', 20, 20)
            oled.text('POSICION', 35, 35)
            oled.text(tuplaNombres[dato],58,54)
            oled.show()
            servo.duty(32)    # activamos el servo para dar paso al vehiculo
            time.sleep(5)       #retardo de la apertura del torniquete para el accerso del vehiculo
            servo.duty(82)  # activamos el servo para cerrar el paso
            oled.fill(0)
            oled.text('PARKING', 40, 20)
            oled.text('DISPONIBLE', 30, 40)
            oled.show()
  #configuramos la ruta y los datos para enviar al servidor
            url = 'https://io.adafruit.com/api/v2/' + username + '/feeds/' + feed_name + '/data'
            body = {'value': "IN-"+ tuplaNombres[dato]}
            headers = {'X-AIO-Key': aio_key, 'Content-Type': 'application/json'}
            try:
                r = requests.post(url, json=body, headers=headers) # enviamos la solicitud al servidor con los datos
                print(r.text)
            except Exception as e: # generamos una excepcion por si el envio falla
                print(e)
                
            if contador == 30: # verificamos si los espacios se ocuparon todos
                parking_lleno() # si esta lleno saltamos a la funcion que controla el parking lleno
                print("principal")
                time.sleep(2)
    estadoSalida = sensorSalida.value()  # leemos el estado del sensor de salida.
    if estadoSalida == 0:
        time.sleep_ms(100)  #generamos un retardo para verificar el estado del pin.
#en esta parte hacemos lo mismo que arriba solo que verificamos la salida y descontamos los datos en lugar de sumar
        estadoSalida = sensorSalida.value() # leemos el estado del sensor de salida.
        if estadoSalida == 0:
            if contador != 0:  #si todo esta vacio no permite que se descuente si se activa el sensor
                while(True):
                    dato = randrange(30)
                    if listaEstado[dato] == 1:
                        listaEstado[dato] = 0
                        contador -= 1
                        oled.fill(0)
                        oled.text('PARKING', 40, 0)
                        oled.text('SALIENDO DE LA', 10, 20)
                        oled.text('POSICION', 35, 35)
                        oled.text(tuplaNombres[dato],58,54)
                        oled.show()
                        servo.duty(32)
                        time.sleep(5)
                        servo.duty(82)
                        oled.fill(0)
                        oled.text('PARKING', 40, 20)
                        oled.text('DISPONIBLE', 30, 40)
                        oled.show()
                        print(contador)
                        url = 'https://io.adafruit.com/api/v2/' + username + '/feeds/' + feed_name + '/data'
                        body = {'value': "OUT-"+ tuplaNombres[dato]}
                        headers = {'X-AIO-Key': aio_key, 'Content-Type': 'application/json'}
                        try:
                            r = requests.post(url, json=body, headers=headers)
                            print(r.text)
                        except Exception as e:
                            print(e)
                        break
                time.sleep(2)

