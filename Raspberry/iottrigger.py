from sense_hat import SenseHat
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from datetime import datetime
import logging
import time
import argparse
import json
import requests
import time
import math
import urllib2

red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
white = (255,255,255)
nothing = (0,0,0)
yellow = (255,255,0)

AllowedActions = ['both', 'publish', 'subscribe']
geo_data = None
cpuserial = "0000000000000000"
sense_data = []
sense = SenseHat()
sense.low_light = True
acc_flag=[0,False]

def start():
    W = white
    G = green
    logo = [
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, W, W,
    W, W, W, W, W, W, G, W,
    W, G, W, W, W, G, G, W,
    W, G, G, W, G, G, W, W,
    W, W, G, G, G, W, W, W,
    W, W, W, G, W, W, W, W,
    W, W, W, W, W, W, W, W,
    ]
    return logo

def stop():
    R = red
    Y = yellow
    logo = [
    R, R, R, R, R, R, R, R,
    R, Y, Y, R, R, Y, Y, R,
    R, Y, Y, Y, Y, Y, Y, R,
    R, R, Y, Y, Y, Y, R, R,
    R, R, Y, Y, Y, Y, R, R,
    R, Y, Y, Y, Y, Y, Y, R,
    R, Y, Y, R, R, Y, Y, R,
    R, R, R, R, R, R, R, R,
    ]
    return logo

def internet():
    N = nothing
    B = blue
    logo = [
    N, N, N, N, N, N, N, N,
    N, N, N, N, N, N, N, N,
    N, B, B, B, B, B, B, N,
    N, N, N, N, N, N, N, N,
    N, N, B, B, B, B, N, N,
    N, N, N, N, N, N, N, N,
    N, N, N, B, B, N, N, N,
    N, N, N, N, N, N, N, N,
    ]
    return logo

#get lattitude and logitude 
def display_ip():
    """  Function To Print GeoIP Latitude & Longitude """
    ip_request = requests.get('https://get.geojs.io/v1/ip.json')
    my_ip = ip_request.json()['ip']
    geo_request = requests.get('https://get.geojs.io/v1/ip/geo/' +my_ip + '.json')
    display_ip.geo_data = geo_request.json()
  
# Extract serial from cpuinfo file
def getserial():
    try:
      f = open('/proc/cpuinfo','r')
      for line in f:
        if line[0:6]=='Serial':
          getserial.cpuserial = line[10:26]
      f.close()
    except:
      getserial.cpuserial = "ERROR000000000"

    return cpuserial

# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")
    
#function to get sensehat data  
def getsensordata():
    ordata =sense.get_orientation_radians()
    roll_in_degree=math.degrees(ordata["roll"])
    acc=sense.get_accelerometer_raw()
    if (roll_in_degree > 90 or roll_in_degree < -90):
        #or (ordata["pitch"] > 90 or ordata["pitch"] < 270 )):
      acc_flag[0]=(acc["z"])
      acc_flag[1]=True
      return  acc_flag  

def wait_for_internet_connection():
    while True:
        try:
            response = urllib2.urlopen('http://google.com',timeout=1)
            return
        except urllib2.URLError:
            pass

    
# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", required=True, dest="host", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", required=True, dest="rootCAPath", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", help="Private key file path")
#parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
#parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False,help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="basicPubSub",
                    help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="sdk/test/Python", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="both",
                    help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Hello World!",
                    help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = 8883
#useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

"""if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883"""

sense.set_pixels(internet())
# wait for internet
wait_for_internet_connection()
sense.set_pixels(start())
# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
"""if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)"""

myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
myAWSIoTMQTTClient.configureEndpoint(host, port)
myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
if args.mode == 'both' or args.mode == 'publish' :
    display_ip()
    getserial()
    message = {}
    message['deviceId'] = getserial.cpuserial
    message['latitude'] = display_ip.geo_data['latitude']
    message['longitude'] = display_ip.geo_data['longitude']
    message['country'] = display_ip.geo_data['country']
    
    while True:  
        #uncomment the getsensordata when sensehat module is functioning 
        getsensordata()
        #comment the following 2 lines when sensehat module is functioning 
        #acc_flag[1] = True
        #acc_flag[0] = 16
        if acc_flag[1]:
            print("accident happened", abs(acc_flag[0]))
            now = datetime.now()
            current_time = now.strftime("%d/%m/%Y %H:%M:%S")
            incidentNo = "INC"+getserial.cpuserial+now.strftime("%d%m%Y%H%M%S")
            if abs(acc_flag[0])*100 > 150:
                speed = abs(acc_flag[0]*10)
            else :
                speed = abs(acc_flag[0]*100)
            message['speed'] = speed
            message['timestamp'] =current_time
            message['incidentId'] = incidentNo
            messageJson = json.dumps(message,sort_keys=True)
            myAWSIoTMQTTClient.publish(topic, messageJson, 0)
            sense.set_pixels(stop())
            break
        
    if args.mode == 'publish':
        print('Published topic %s: %s\n' % (topic, messageJson))
while 1:
    time.sleep(10)
