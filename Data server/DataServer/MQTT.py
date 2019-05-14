#!/usr/bin/python3
import paho.mqtt.client as mqtt
import DataProxy
import threading
import logging
import time
import re

# This class handle connection with MQTT broker. This is an indipendent thread.
# When is connected the main loop listen for incoming messages and handle them
# using __messageCallback that is, as the name suggest, asynchronusly called.
# For detailed information about each method see documentation.
class MQTTclient(threading.Thread):
    def __init__(self, brokerAddress, username, password, syncEvents, dataProxy, loggingFile):
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
        self.dataProxyLock = threading.Lock()
        self.__logger = logging.getLogger(name = "MQTT")
        logging.basicConfig(filename = loggingFile, level = logging.INFO)
        threading.Thread.__init__(self, name = "MQTT Thread", daemon = True)

    def run(self):
        self.client.connect(self.brokerAddress)
        self.client.loop_start()
        try:
            self.subscribeResult = self.client.subscribe("/#")
        except Exception:
            self.__logger.critical("Errors occurr while subscribing to channel")
            self.syncEvents[1].set()
            return
            
        if self.subscribeResult == False:
            self.syncEvents[1].set()
            return
            
        self.syncEvents[0].set()

        while self.keepListening == True:
            time.sleep(0.1)
        
        try:
            self.client.loop_stop(force = True)
            self.client.disconnect()
        except Exception as reason:
            self.__logger.error("Error occured while stopping MQTT sub-Thread")
            self.__logger.info("Reason: " + str(reason))

        self.__logger.info("MQTT connection terminated")

        return

    def stop(self):
        self.keepListening = False


    def __messageCallback(self, client, userdata, message):
        try:
            match = re.match(pattern = r"\/[a-z]*\-([0-9][0-9])\/([a-z]*)", string = str(message.topic))
        except Exception as reason:
            self.__logger.warning("Regex error occurred")
            self.__logger.info("Reason : " + str(reason))

        if match == None:
            self.__logger.warning("Regex could not match message contenent")
        else:
            sensorNumber = str(match.group(1))
            dataType = str(match.group(2))
            dataValue = str(message.payload.decode("utf-8"))
            result = self.dataProxy.lastDataUpdate(sensorNumber = int(sensorNumber), dataType = dataType, dataValue = dataValue)
            if result[0] == True:
                return
            else:
                if result[1] == 1:
                    self.__logger.warning("Received data for sensor " + str(sensorNumber) + " that do not exist.")
                elif result[1] == 2:
                    self.__logger.warning("Received data of type " + str(dataType) + " for sensor " + str(sensorNumber) + ". This sensor has not this data type")
                elif result[1] == 3:
                    self.__logger.warning("Unknown SQL error occured")

                self.__logger.warning("This data are lost forever")
                return
        

    def __subscribeCallback(self, client, userdata, mid, granted_qos):
        if self.subscribeResult[1] == mid:
            self.subscribeResult = True
        else:
            self.subscribeResult = False

if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()
