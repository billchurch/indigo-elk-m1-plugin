#!/usr/bin/env python

####################
# Original work by Jeremy Carey All rights reserved.
# http://www.jeremycarey.net/elkplug
# Modified by Mark Lyons in accordance with permission granted to the Indigo Community June 14, 2013
# by Jeremy Cary.
# ELK alarm panel plugin for Indigo 7
# 11/2/13 Added support for Elk-M1 bi-directional lighting control.  When devices in indigo are setup as universal receiver modules, they will send status changes to the M1.
# 12/15/2017 Project seems abandoned by Mark Lyons / Jeremy Cary, now being maintained by Bill Church
# https://github.com/billchurch/indigo-elk-m1-plugin

import os
import sys
import time
import socket
import elkextra
import pprint
from telnetlib import select
from elk import Elk

##########################################################################


class Plugin(indigo.PluginBase):
    ########################################

    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(
            self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

    def __del__(self):
        indigo.PluginBase.__del__(self)
    ########################################

    def startup(self):
        try:
            if self.pluginPrefs["configDone"]:
                self.elkstartup()
                self.startup = False
            else:
                self.errorLog(
                    "Plugin not configured. Delaying startup until configuration is saved")
        except KeyError:
            self.errorLog(
                "Plugin not configured. Delaying startup until configuration is saved")

    def shutdown(self):
        self.debugLog("Getting ready to exit plugin.")
        self.debugLog("Closing connection to alarm panel.")
        self.ePanel.disconnect()
        indigo.devices[self.panelId].updateStateOnServer("conn_state", "Off")

    def runConcurrentThread(self):
        try:
            while True:
                self.sleep(.1)
                try:
                    if self.startup:
                        self.elkstartup()
                        self.startup = False
                    if "On" in str(indigo.devices[self.panelId].states["conn_state"]):
                        self.dispatchMsg(self.ePanel.readData())
                    else:
                        pass
                except EOFError, e:
                    self.errorLog("EOFError: %s" % e.message)
                    self.sleep(5)
                    self.elkstartup()
                except AttributeError, e:
                    pprint.pprint(e)
                    self.debugLog("AttributeError: %s" % e.message)
                    if "conn" in e.message:
                        self.debugLog(
                            "Connection issue detected, sleeping for 5 sec and restarting: %s" % e.message)
                        self.sleep(5)
                        self.elkstartup()
                except select.error, e:
                    self.debugLog(
                        "Disconnected while listening: %s" % e.message)
        except self.StopThread:
            pass

    # elk startup method, main startup checks for configured flag
    def elkstartup(self):
        try:
            self.debug = self.pluginPrefs["debug"]
            self.debugLog("Debug logging enabled.")
            self.debugLog("Getting 'ELK M1' folder id.")
            self.folderId = elkextra.createFolder(
                self.pluginPrefs["deviceFolder"])
            self.debugLog("Getting 'Alarm Panel' device id.")
            self.panelId = elkextra.createPanel(self.pluginPrefs["autoPanel"], self.pluginPrefs[
                                                "ip_address"], self.pluginPrefs["ip_port"], self.folderId)
            self.debugLog("Folder id: %s, Alarm Panel id: %s" %
                          (self.folderId, self.panelId))
        except KeyError:
            self.errorLog("Plugin not yet configured.\nPlease save the configuration then reload the plugin.\nThis should only happen the first time you run the plugin\nor if you delete the preferences file.")
            return
        if self.panelId > 0:
            self.debugLog("Creating instance of class Elk.")
            try:
                host = indigo.devices[self.panelId].pluginProps["ip_address"]
                port = indigo.devices[self.panelId].pluginProps["ip_port"]
            except KeyError:
                host = self.pluginPrefs["ip_address"]
                port = self.pluginPrefs["ip_port"]
            self.ePanel = Elk(host, port, 1)
            self.debugLog("Elk class instance %s created." % repr(self.ePanel))
            self.debugLog("Initiating connection to alarm panel.")
            try:
                self.ePanel.connect()
                indigo.devices[self.panelId].updateStateOnServer(
                    "conn_state", "On")
                self.debugLog(
                    "Connected to panel, sending arming state request.")
                self.ePanel.sendCmd("06as00")
                self.debugLog("Processing arming state request.")
                self.dispatchMsg(self.ePanel.readData())
            except socket.error, e:
                self.errorLog(
                    "Unable to connect to alarm panel. %s" % e.message)
                indigo.devices[self.panelId].updateStateOnServer(
                    "conn_state", "Off")

        self.debugLog("Checking for temp sensor devices.")
        reqTempData = False
        for device in indigo.devices:
            if indigo.devices[self.panelId].deviceTypeId == 'alarmTemp':
                reqTempData = True
                break
        if (self.pluginPrefs["tempsensors"] or reqTempData) and self.pluginPrefs["startupValidate"]:
            self.debugLog("Startup validation enabled, checking temp sensors.")
            self.sendTempCmds()
        else:
            self.debugLog(
                "Startup validation disabled, not checking temp sensors.")

        self.debugLog("Checking for zone devices.")
        reqZoneData = False
        for device in indigo.devices:
            if indigo.devices[self.panelId].deviceTypeId == 'alarmZone':
                reqZoneData = True
                break
        if (self.pluginPrefs["alarmZones"] or reqZoneData) and self.pluginPrefs["startupValidate"]:
            self.debugLog("Startup validation enabled, checking zones.")
            self.sendZoneCmds()
        else:
            self.debugLog("Startup validation disabled, not checking zones.")

        self.debugLog("Checking for thermostat devices.")
        reqThermoData = False
        for device in indigo.devices:
            if indigo.devices[self.panelId].deviceTypeId == 'alarmTstat':
                reqThermoData = True
                break
        if (self.pluginPrefs["thermostats"] or reqThermoData) and self.pluginPrefs["startupValidate"]:
            self.debugLog("Startup validation enabled, checking thermostats.")
            self.sendThermoCmds()
        else:
            self.debugLog(
                "Startup validation disabled, not checking thermostats.")
        if self.pluginPrefs["subscribe"]:
            self.debugLog("Startup validation enabled, starting subscription.")
            indigo.devices.subscribeToChanges()
        else:
            self.debugLog(
                "Startup validation disabled, subscription disabled.")
        self.HoldFeedback = False

    # take return messages from alarm panel and send to methods to process them
    def dispatchMsg(self, msg):
        if len(msg) > 0:
            if 'XK' in msg:
                # logging "tick" messages from M1XEP

                self.debugLog("Tick: %s" % msg.rstrip())
            elif 'AS' in msg:
                self.debugLog(msg.rstrip())
                arst, armrd, almst = self.ePanel.armStat(msg)
                elkextra.setArmingStatus(arst, armrd, almst, self.panelId)
# 			elif 'EE' in msg:
# 				self.debugLog(msg.rstrip())
# 				eeState = ePanel.eeStat(msg)
# 				print "Enter Exit state is %s" % eeState
            elif 'PC' in msg:
                if self.HoldFeedback <> True:
                    zone, lightmsg = self.ePanel.lights(msg)
                    self.debugLog(lightmsg)
                    self.debugLog(zone)
                    elkextra.setDeviceLight(zone, lightmsg)
                self.HoldFeedback = False
            elif 'RP' in msg:
                self.debugLog('Remote Programming')
                self.debugLog(msg.rstrip())
                rpState = self.ePanel.rpStat(msg)
                self.debugLog('Remote Programming message: ' + rpState)
            elif 'SD' in msg:
                self.debugLog(msg.rstrip())
                daddr, id, name = self.ePanel.stringData(msg)
                elkextra.setDeviceDesc(
                    daddr, id, name, self.pluginPrefs["autoNames"])
            elif 'ST' in msg:
                self.debugLog(msg.rstrip())
                group, tnum, temp = self.ePanel.tempRpt(msg);
                self.debugLog('Temperature Status ' + group + ' ' + str(tnum) + ' ' + str(temp))
                if int(temp) != 0:
                    elkextra.setTempInfo(tnum, temp, self.folderId)
            elif 'TR' in msg:
                self.debugLog(msg.rstrip())
                tnum, mode, hold, tfan, temp, heat, cool = self.ePanel.thermoRpt(
                    msg)
                if int(temp) != 0:
                    elkextra.setThermoInfo(
                        tnum, mode, hold, tfan, temp, heat, cool, self.folderId)
#			elif 'VN' in msg:
#				indigo.server.log("Version info message")
#				indigo.server.log(msg.rstrip())
            elif 'ZC' in msg:
                self.debugLog(msg.rstrip())
                zoneS = self.ePanel.zoneChange(msg)
                self.debugLog(str(zoneS))
                elkextra.setZoneStatus(zoneS)
            elif 'ZD' in msg:
                self.debugLog(msg.rstrip())
                zoneD = self.ePanel.zoneData(msg)
                self.debugLog(str(zoneD))
                elkextra.setupZones(zoneD, self.folderId,
                                    self.pluginPrefs["autoNames"])
            elif 'ZS' in msg:
                self.debugLog(msg.rstrip())
                zoneS = self.ePanel.zoneStat(msg)
                self.debugLog(str(zoneS))
                elkextra.setZoneStatus(zoneS)
            elif 'EOFError' in msg:
                self.debugLog("COMMUNICATION WITH PANEL " + msg)
                self.debugLog("RESTARTING")
                self.elkstartup()
            else:
                self.debugLog(msg.rstrip())

    def sendZoneCmds(self):
        self.debugLog("Sending zone data request")
        self.ePanel.sendCmd("06zd00")
        self.debugLog("Processing zone data request.")
        self.dispatchMsg(self.ePanel.readData())
        self.debugLog("Sending zone status request")
        self.ePanel.sendCmd("06zs00")
        self.debugLog("Processing zone status request.")
        self.dispatchMsg(self.ePanel.readData())

        self.debugLog("Updating zone descriptions.")
        for device in indigo.devices:
            if device.deviceTypeId == 'alarmZone':
                self.readDeviceDesc(device)

    # sent thermostat data request commands
    def sendTempCmds(self):
        self.debugLog("Sending temp request for 16 temp sensors")
        for lctr in range(1, 17):
            self.ePanel.sendCmd("09st0%02d00" % lctr)
            self.debugLog("09st0%02d00" % lctr)
            self.dispatchMsg(self.ePanel.readData())

        self.debugLog("Updating temp descriptions.")
        for device in indigo.devices:
            if "Temp Sensor" in device.name:
                self.readDeviceDesc(device)

    # sent thermostat data request commands
    def sendThermoCmds(self):
        self.debugLog("Sending thermostat request for 16 thermostats")
        for lctr in range(1, 17):
            self.ePanel.sendCmd("08tr%02d00" % lctr)
            self.debugLog("08tr%02d00" % lctr)
            self.dispatchMsg(self.ePanel.readData())

        self.debugLog("Updating thermostat descriptions.")
        for device in indigo.devices:
            if "Thermostat" in device.name:
                self.readDeviceDesc(device)

    # send 'sd' request and get name of elk device
    def readDeviceDesc(self, device):
        if device.address != "":
            self.debugLog("Processing string data request for %s." %
                          device.name)
            cmdPrefix = "0Bsd"
            if "Alarm Zone" in device.model and 'z' in device.address:
                reqType = "00"
            elif "Area" in device.name:
                reqType = "01"
            elif "Elk Thermostat" in device.model and 't' in device.address:
                reqType = "11"
            else:
                reqType = "00"

            try:
                if len(device.address) == 4:
                    devNr = device.address[1:]
                elif len(device.address) == 3:
                    devNr = "%03d" % int(device.address)
                else:
                    devNr = "208"
            except ValueError:
                self.debugLog(
                    "ValueError trapped. This was probably caused by incorrectly specifying a device address. Setting devNr to 208.")
                devNr = "208"

            cmd = "%s%s%s00" % (cmdPrefix, reqType, devNr)
            self.debugLog("Getting ready to send %s" % cmd)
            self.ePanel.sendCmd(str(cmd))
            self.dispatchMsg(self.ePanel.readData())
        else:
            self.errorLog(
                "Attempt was made to request name of undefined device %s." % device.name)

    # open network connection to alarm panel
    def connPanel(self):
        indigo.server.log("Connecting to Alarm Panel")
        self.ePanel.connect()
        indigo.devices[self.panelId].updateStateOnServer("conn_state", "On")

    # close network connection to alarm panel
    def disconnPanel(self):
        indigo.server.log("Disconnecting from Alarm Panel")
        indigo.devices[self.panelId].updateStateOnServer("conn_state", "Off")
        self.ePanel.disconnect()

    # send 'ts' request to set thermostat data
    def setThermo(self, pluginAction):
        stem = "0Bts"
        thermAddr = indigo.devices[pluginAction.deviceId].address[2:]
        self.debugLog(str(pluginAction))
        if pluginAction.pluginTypeId == "changeMode":
            self.debugLog("Changing thermostat mode")
            elem = "0"
            if pluginAction.props["modeChoice"] == "off":
                value = "00"
            elif pluginAction.props["modeChoice"] == "heat":
                value = "01"
            elif pluginAction.props["modeChoice"] == "cool":
                value = "02"
            elif pluginAction.props["modeChoice"] == "auto":
                value = "03"
        elif pluginAction.pluginTypeId == "changeHold":
            self.debugLog("Changing temperature hold mode")
            elem = "1"
            if pluginAction.props["holdMode"] == "off":
                value = "00"
            else:
                value = "01"
        elif pluginAction.pluginTypeId == "changeFan":
            self.debugLog("Changing fan mode")
            elem = "2"
            if pluginAction.props["fanMode"] == "auto":
                value = "00"
            else:
                value = "01"
        elif pluginAction.pluginTypeId == "changeCool":
            self.debugLog("Changing cooling setpoint")
            elem = "4"
            value = pluginAction.props["coolTemp"]
        elif pluginAction.pluginTypeId == "changeHeat":
            self.debugLog("Changing heating setpoint")
            elem = "5"
            value = pluginAction.props["heatTemp"]

        fullCmd = stem + thermAddr + value + elem + "00"
        self.debugLog("Preparing to send %s to alarm." % fullCmd)
        self.ePanel.sendCmd(str(fullCmd))
        self.dispatchMsg(self.ePanel.readData())

    # send 'a#' request to arm or disarm the alarm
    def setArming(self, pluginAction):
        cmdLen = '0D'
        if pluginAction.pluginTypeId == "arm":
            self.debugLog("Building arm state message")
        else:
            indigo.server.log("Something strange happened")
        self.debugLog(str(pluginAction))
        if pluginAction.props["armType"] == "disarm":
            stem = 'a0'
            self.debugLog("Arming state is disarm (a0)")
        elif pluginAction.props["armType"] == "armAway":
            stem = 'a1'
            self.debugLog("Arming state is arm away (a1)")
        elif pluginAction.props["armType"] == "armStay":
            stem = 'a2'
            self.debugLog("Arming state is arm stay (a2)")
        elif pluginAction.props["armType"] == "armStayInstant":
            stem = 'a3'
            self.debugLog("Arming state is arm stay instant (a3)")
        elif pluginAction.props["armType"] == "armNight":
            stem = 'a4'
            self.debugLog("Arming state is arm night (a4)")
        elif pluginAction.props["armType"] == "armNightInstant":
            stem = 'a5'
            self.debugLog("Arming state is arm night instant (a5)")
        elif pluginAction.props["armType"] == "armVacation":
            stem = 'a6'
            self.debugLog("Arming state is arm vacation (a6)")
        if self.pluginPrefs["saveCode"]:
            code = "%06d" % int(self.pluginPrefs["alarmCode"])
            self.debugLog("Setting code to saved value")
        else:
            code = "%06d" % int(pluginAction.props["armCode"])
            self.debugLog("Setting code to passed value")
        fullCmd = cmdLen + stem + "1" + code + "00"
        self.debugLog("Preparing to send %s to alarm." % fullCmd)
        self.ePanel.sendCmd(str(fullCmd))
        self.dispatchMsg(self.ePanel.readData())

    # device parameter validation
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        badAddr = "Please use either an IP address (i.e. 1.2.3.4) or a fully qualified host name (i.e. elk.domain.com)"
        badPort = "This value must be numeric. The default port 2101 should be used unless you've reconfigured your M1XEP."
        newaddr = str("%s:%s" %
                      (valuesDict["ip_address"], valuesDict["ip_port"]))
        errDict = indigo.Dict()
        if typeId == 'alarmPanel':
            if valuesDict["ip_address"].count('.') >= 2:
                ipOK = True
            else:
                ipOK = False

            if valuesDict["ip_port"].isdigit():
                portOK = True
            else:
                portOK = False

            if ipOK and portOK:
                if self.panelId > 0:
                    device = indigo.devices[self.panelId]
                    device.replacePluginPropsOnServer({"address": newaddr, "ip_address": valuesDict[
                                                      "ip_address"], "ip_port": valuesDict["ip_port"]})
                rtn = True
            elif ipOK and not portOK:
                errDict["ip_port"] = badPort
                rtn = (False, valuesDict, errDict)
            elif not ipOK and portOK:
                errDict["ip_address"] = badAddr
                rtn = (False, valuesDict, errDict)
            elif not ipOK and not portOK:
                errDict["ip_address"] = badAddr
                errDict["ip_port"] = badPort
                rtn = (False, valuesDict, errDict)
        else:
            rtn = True
        return rtn
    # plugin configuration validation

    def validatePrefsConfigUi(self, valuesDict):
        errDict = indigo.Dict()
        badAddr = "Please use either an IP address (i.e. 1.2.3.4) or a fully qualified host name (i.e. elk.domain.com)"
        badPort = "This value must be numeric. The default port 2101 should be used unless you've reconfigured your M1XEP."
        badCode = "Alarm code saving is enabled. This value must be numeric and either 4 or 6 digits depending on how your alarm is configured."
        newaddr = str("%s:%s" %
                      (valuesDict["ip_address"], valuesDict["ip_port"]))
        if valuesDict["debug"]:
            self.debug = True
        else:
            self.debug = False
        if valuesDict["autoPanel"]:
            if valuesDict["ip_address"].count('.') >= 2:
                ipOK = True
            else:
                ipOK = False
            if valuesDict["ip_port"].isdigit():
                portOK = True
            else:
                portOK = False
            try:
                if ipOK and portOK:
                    if self.panelId > 0:
                        device = indigo.devices[self.panelId]
                        device.replacePluginPropsOnServer({"address": newaddr, "ip_address": valuesDict[
                                                          "ip_address"], "ip_port": valuesDict["ip_port"]})
                    rtn = True
                elif ipOK and not portOK:
                    errDict["ip_port"] = badPort
                    rtn = (False, valuesDict, errDict)
                elif not ipOK and portOK:
                    errDict["ip_address"] = badAddr
                    rtn = (False, valuesDict, errDict)
                elif not ipOK and not portOK:
                    errDict["ip_address"] = badAddr
                    errDict["ip_port"] = badPort
                    rtn = (False, valuesDict, errDict)
            except AttributeError:
                rtn = (True, valuesDict)
        else:
            ipOK = False
            portOK = False
            rtn = (True, valuesDict)
        if valuesDict["saveCode"]:
            # check for alarmCode
            self.debugLog("Alarm code saving enabled")
        else:
            # no need to check code
            self.debugLog("Alarm code saving disabled")
        try:
            if valuesDict["configDone"]:
                self.startup = False
            else:
                if ipOK and portOK and rtn:
                    self.debugLog("Setting configDone to True")
                    valuesDict["configDone"] = True
                    self.debugLog("Setting flag to run self.elkstartup")
                    self.startup = True
        except KeyError:
            if ipOK and portOK and rtn:
                self.debugLog("Setting configDone to True")
                valuesDict["configDone"] = True
                self.debugLog("Setting flag to run self.elkstartup")
                self.startup = True

        self.debugLog("%s, %s, %s" % (str(rtn), str(ipOK), str(portOK)))
        return rtn

    def deviceUpdated(self, origDev, newDev):
        # Device changes are sent here from Indigo.
        if (origDev.model == "Universal Module Receiver"):
            # Received an On command for a device labeled as a Universal Module
            # Receiver
            devAddres = str(newDev.address)[1:]
            devCmd = str(newDev.address)[0:1] + devAddres.zfill(2)
            if newDev.onState == True:
                devCmd = "09pn" + devCmd + "00"
                self.debugLog(u"Sending command to Elk-M1: " + str(devCmd))
                self.HoldFeedback = True
                self.ePanel.sendCmd(str(devCmd))
            # Received an Off command for a device labeled as a Universal
            # Module Receiver
            elif newDev.onState == False:
                devCmd = "09pf" + devCmd + "00"
                self.debugLog(u"Sending command to Elk-M1: " + str(devCmd))
                self.HoldFeedback = True
                self.ePanel.sendCmd(str(devCmd))
