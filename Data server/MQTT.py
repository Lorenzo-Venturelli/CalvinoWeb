#! /usr/bin/python
import paho.mqtt.client as mqtt
import DataProxy
import threading
import time
import re

class MQTTclient(threading.Thread):
    def __init__(self, brokerAddress, username, password, syncEvents, dataProxy):
        self.brokerAddress = brokerAddress
        self.username = username
        self.password = password
        self.client = mqtt.Client(client_id = "MQTT-Modena", clean_session = True)
        self.client.on_subscribe = self.__subscribeCallback
        self.client.on_message = self.__messageCallback
        self.client.username_pw_set(username = self.username, password = self.password)
        self.keepListening = True
        self.syncEvents = syncEvents
        self.subscribeResult = None
        self.dataProxy = dataProxy
        threading.Thread.__init__(self, name = "MQTT Thread", daemon = False)

    def run(self):
        self.client.connect(self.brokerAddress)
        self.client.loop_start()
        try:
            self.subscribeResult = self.client.subscribe("/#")
        except Exception:
            print("Error: Errors occurr while subscribing to channel")
            self.syncEvents[1].set()
            return
            
        if self.subscribeResult == False:
            self.syncEvents[1].set()
            return
        else:
            self.syncEvents[0].set()

            while self.keepListening == True:
                time.sleep(0.1)

            self.client.loop_stop()
            self.client.disconnect()

    def stop(self):
        self.keepListening = False


    def __messageCallback(self, client, userdata, message):
        match = re.match(pattern = r"[a-z]*[\-]*([0-9][0-9])\/([a-z]*", string = str(message.topic))
        sensorNumber = str(match.group(1))
        dataType = str(match.group(2))
        dataValue = str(message.payload.decode("utf-8"))
        result = self.dataProxy.lastDataUpdate(sensorNumber = sensorNumber, dataType = dataType, dataValue = dataValue)
        if result[0] == True:
            return
        else:
            print("Error: The received data are not valid")
        

    def __subscribeCallback(self, client, userdata, mid, granted_qos):
        if self.subscribeResult[1] == mid:
            self.subscribeResult = True
        else:
            self.subscribeResult = False

if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()
