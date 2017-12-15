#
#
# Extra stuff for the ELK plugin
#
#

import indigo

# create ELK M1 folder and return folderId
def createFolder(pluginFolder):
    try:
        folderId = indigo.devices.folders["ELK M1"].id
    except KeyError, e:
        if e.message == "key name ELK M1 not found in database":
            if pluginFolder:
                indigo.devices.folder.create("ELK M1")
                folderId = indigo.devices.folders["ELK M1"].id
            else:
                folderId = 0
    return folderId

# create Alarm Panel device and return panelId
def createPanel(autoPanel, ip_addr, ip_port, folderId):
    try:
        panelId = indigo.devices["Alarm Panel"].id
    except KeyError, e:
        if e.message == "key name Alarm Panel not found in database":
            if autoPanel:
                addr = "%s:%s" % (ip_addr, ip_port)
                pDev = indigo.device.create(protocol=indigo.kProtocol.Plugin,
                                            address=addr,
                                            name="Alarm Panel",
                                            description="ELK M1 Alarm Panel",
                                            pluginId="me.billchurch.indigoplugin.elkm1g",
                                            deviceTypeId="alarmPanel",
                                            props={
                                                "address": addr, "ip_address": ip_addr, "ip_port": ip_port},
                                            folder=folderId)
                panelId = pDev.id
            else:
                panelId = 0

    return panelId

# process 'AS' response to set arming status
def setArmingStatus(arst, armrd, almst, panelId):
    indigo.devices[panelId].updateStateOnServer("arm_state", arst)
    indigo.devices[panelId].updateStateOnServer("arm_ready", armrd)
    indigo.devices[panelId].updateStateOnServer("alarm_state", almst)

# process 'PC" response and set status of the corresponding device
def setDeviceLight(zone, lightmsg):
    for device in indigo.devices:

        if device.address == zone:
            if lightmsg == "00":
                indigo.device.turnOff(device)
            elif lightmsg == "01":
                indigo.device.turnOn(device)

# process 'SD' response and set description of indigo device
def setDeviceDesc(eaddr, eid, ename, autoNames):
    if autoNames:
        if eaddr == 'z':
            etype = "Zone"
        elif eaddr == 'a':
            etype = "Area"
        elif eaddr == 't':
            etype = "Thermostat"
        else:
            etype = "Other"

        devAddr = "%s%s" % (eaddr, eid)

        for device in indigo.devices:
            if device.address == devAddr:
                device.name = ename
                device.replaceOnServer()

# process 'TR' response for thermostats
def setThermoInfo(tnum, mode, hold, tfan, temp, heat, cool, folderId):
    tdevNm = "Thermostat %s" % str(tnum)
    addr = "t%03d" % tnum
    existaddrs = []
    existdevs = []
    for device in indigo.devices:
        if device.deviceTypeId == 'alarmTstat':
            existaddrs.append(device.address)
            existdevs.append(device)
    if addr in existaddrs:
        for device in existdevs:
            if addr == device.address:
                device.updateStateOnServer("mode", mode)
                device.updateStateOnServer("temp_hold", hold)
                device.updateStateOnServer("fan_mode", tfan)
                device.updateStateOnServer("curr_temp", temp)
                device.updateStateOnServer("heat_setpoint", heat)
                device.updateStateOnServer("cool_setpoint", cool)
    else:
        updateDev = indigo.device.create(protocol=indigo.kProtocol.Plugin,
                                         address="",
                                         name=tdevNm,
                                         description="",
                                         pluginId="me.billchurch.indigoplugin.elkm1g",
                                         deviceTypeId="alarmTstat",
                                         props={"address": addr},
                                         folder=folderId)
        updateDev.updateStateOnServer("mode", mode)
        updateDev.updateStateOnServer("temp_hold", hold)
        updateDev.updateStateOnServer("fan_mode", tfan)
        updateDev.updateStateOnServer("curr_temp", temp)
        updateDev.updateStateOnServer("heat_setpoint", heat)
        updateDev.updateStateOnServer("cool_setpoint", cool)

# process 'ZD' response to request for zone data
def setupZones(zoneD, folderId, autoNames):
    existaddrs = []
    existdevs = []
    for device in indigo.devices:
        if device.deviceTypeId == 'alarmZone':
            existaddrs.append(device.address)
            existdevs.append(device)
    for zone in zoneD:
        zdAddr = "z%03d" % zone[0]
        zdName = "Zone %s" % zone[0]
        if zdAddr in existaddrs:
            for device in existdevs:
                if zdAddr == device.address:
                    indigo.server.log(
                        "Updating existing device %s, %s" % (device.name, zone[1]))
                    device.replacePluginPropsOnServer(
                        {"address": zdAddr, "type": zone[1]})
                    if autoNames:
                        device.description = zone[1]
                        device.replaceOnServer()
        else:
            try:
                indigo.device.create(protocol=indigo.kProtocol.Plugin,
                                     address="",
                                     name=zdName,
                                     description="",
                                     pluginId="me.billchurch.indigoplugin.elkm1g",
                                     deviceTypeId="alarmZone",
                                     props={"address": zdAddr,
                                            "type": zone[1]},
                                     folder=folderId)
                indigo.server.log(
                    "Creating device - Name: %s, Zone #: %s" % (zdName, zdAddr))
            except ValueError:
                # don't create device that already exists
                pass

# process 'ZC' or 'ZS' responses to set zone status
def setZoneStatus(zoneS):
    for zone in zoneS:
        devAddr = "z%03d" % zone[0]
        for device in indigo.devices:
            if device.address == devAddr:
                device.updateStateOnServer("status", zone[1])
