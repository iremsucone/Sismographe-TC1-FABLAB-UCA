import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import time
import csv
import os.path
from os import path
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import ssl
import random
import string
import getpass

# Configuration du port série
SERIAL_PORT = 'COM3'  # Remplacez par votre port série
BAUD_RATE = 9600      # Remplacez par votre baud rate

# Initialisation de la liste pour stocker les données
data = []
Amp = 50
Offset = 32400
Amax = 60000

# === MQTT Configuration ===
urlMqtt = "mqtt.univ-cotedazur.fr"
portMqtt = 443
protocol = "websockets"  # WebSocket Secure
mqtt_topic = "FABLAB_21_22/irem/sismo"

Username = "fablab2122"  
pwd = "2122"
auth = {
    'username':Username,
    'password':pwd
}

# === Serial Port Configuration ===
baudRate = 9600
portSerie = "COM3"

# === MQTT Client Configuration ===
tls = {
    'tls_version': ssl.PROTOCOL_TLSv1_2
}

def randomword(length):
    lettresEtChiffres = string.ascii_letters + string.digits
    chaineAleatoire = ''.join((random.choice(lettresEtChiffres) for i in range(length)))
    return chaineAleatoire

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.connected_flag = True
        print("connexion MQTT effectuée.\n")
        client.subscribe(mqtt_topic + "/in/")
    else:
        print("Problème de connexion, code : " + str(rc))
        client.connected_flag = False

def on_message(client, userdata, msg):
    data = str(msg.payload.decode("utf-8"))
    print("Réception MQTT : " + mqtt_topic + "/in/ " + data)
    ser.write((data + "\n").encode())

# === Serial Data Reading and Plotting ===
def read_serial():
    global data
    i = 0
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        while True:
            line = ser.readline()  # Lire une ligne du port série
            if line:
                try:
                    value = float(line.decode('utf-8').strip())  # Convertir en float
                    data.append((value - Offset) * Amp)  # Ajouter à la liste des données
                    i += 1
                    if not path.exists("donnees.csv"):
                        with open('donnees.csv', 'w', newline='') as file:
                            writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                            writer.writerow(["temps", "Amplitude"])
                    with open('donnees.csv', 'a', newline='') as file:
                        writer = csv.writer(file, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
                        writer.writerow([i, value])

                    # Send data to MQTT
                    if client.connected_flag:
                        client.publish(mqtt_topic + "/out/", payload=str(value), qos=0)
                except ValueError:
                    pass  # Ignorer les lignes qui ne peuvent pas être converties

def update_graph(frame):
    plt.clf()  # Effacer le graphique précédent
    plt.plot(data, label='Données du port série')
    plt.xlabel('Index')
    plt.ylabel('Valeur')
    plt.title('Données en temps réel')
    plt.ylim(-Amax, Amax)
    plt.legend()
    plt.grid()

# MQTT client setup
client = mqtt.Client(
    client_id=randomword(8),
    clean_session=True,
    protocol=mqtt.MQTTv311,
    transport=protocol
)
client.connected_flag = False
client.username_pw_set(username=auth["username"], password=auth["password"])
client.tls_set(tls_version=tls["tls_version"])
client.on_connect = on_connect
client.on_message = on_message
client.connect(urlMqtt, portMqtt, 60)

# Start the serial reading thread
serial_thread = threading.Thread(target=read_serial, daemon=True)
serial_thread.start()

# Start the MQTT client loop
mqtt_thread = threading.Thread(target=client.loop_forever, daemon=True)
mqtt_thread.start()

# Plot configuration
fig = plt.figure(num=1, figsize=(10, 6), dpi=120, facecolor='w', edgecolor='k')
ani = animation.FuncAnimation(fig, update_graph, interval=1000)  # Mettre à jour toutes les 1000ms
plt.show()
