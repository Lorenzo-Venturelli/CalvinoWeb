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
class MQTTclient(threading.Thread):
    def __init__(self, brokerAddress, username, password, syncEvents, dataProxy, loggingFile):
        self.__brokerAddress = brokerAddress
        self.__username = username
        self.__password = password
        self.__client = mqtt.Client(client_id = "MQTT-Modena", clean_session = True)
        self.__client.on_subscribe = self.__subscribeCallback
        self.__client.on_message = self.__messageCallback
        self.__client.username_pw_set(username = self.__username, password = self.__password)
        self.__keepListening = True
        self.__syncEvents = syncEvents
        self.__subscribeResult = None
        self.__dataProxy = dataProxy
        self.__dataProxyLock = threading.Lock()
        self.__logger = logging.getLogger(name = "MQTT")
        logging.basicConfig(filename = loggingFile, level = logging.INFO)
        threading.Thread.__init__(self, name = "MQTT Thread", daemon = True)

    def run(self):
        self.__client.connect(self.__brokerAddress)
        self.__client.loop_start()
        try:
            self.__subscribeResult = self.__client.subscribe("/#")
        except Exception:
            self.__logger.critical("Errors occurr while subscribing to channel")
            self.__syncEvents[1].set()
            return
            
        if self.__subscribeResult == False:
            self.__syncEvents[1].set()
            return
            
        self.__syncEvents[0].set()

        while self.__keepListening == True:
            time.sleep(0.1)
        
        try:
            self.__client.loop_stop(force = True)
            self.__client.disconnect()
        except Exception as reason:
            self.__logger.error("Error occured while stopping MQTT sub-Thread")
            self.__logger.info("Reason: " + str(reason))

        self.__logger.info("MQTT connection terminated")

        return

    def stop(self):
        self.__keepListening = False


    def __messageCallback(self, client, userdata, message):
        try:
            match = re.match(pattern = r"\/[a-z]*\-([0-9][0-9])\/([a-z]*)", string = str(message.topic))
        except Exception as reason:
            self.__logger.warning("Regex error occurred")
            self.__logger.info("Reason : " + str(reason))

        if match == None:
            self.__logger.warning("Regex could not match message contenent")
        else:
            try:
                sensorNumber = str(match.group(1))
                dataType = str(match.group(2))
                dataValue = str(message.payload.decode("utf-8"))
                result = self.__dataProxy.lastDataUpdate(sensorNumber = int(sensorNumber), dataType = dataType, dataValue = dataValue)
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
            except Exception as reason:
                self.__logger.warning("Error occurred while handeling an incoming message")
        

    def __subscribeCallback(self, client, userdata, mid, granted_qos):
        if self.__subscribeResult[1] == mid:
            self.__subscribeResult = True
        else:
            self.__subscribeResult = False

if __name__ == "__main__":
    print("Error: This program must be used as a module")
    quit()
