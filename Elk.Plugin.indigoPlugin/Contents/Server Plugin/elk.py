import telnetlib, time

class Elk:

	def __init__(self, host, port, timeout):
		self.host = host
		self.port = int(port)
		self.timeout = int(timeout)

	def __del__(self):
		self.conn.close()

	# Connect to alarm panel
	def connect(self):
		self.conn = telnetlib.Telnet(self.host, self.port)

	# Disconnect from alarm panel
	def disconnect(self):
		self.conn.close()

	# Read data from alarm panel
	def readData(self):
		self.elkMsg = self.conn.read_until("\n", self.timeout)
		return self.elkMsg

	# Send command to alarm panel
	def sendCmd(self, cmd):
		fullCmd = cmd + self.checksum(cmd) + "\n"
#		print "Sending: %s" % fullCmd.rstrip()
		self.conn.write(fullCmd)

	# Handle arming status (AS) message
	def armStat(self, msg):
		sarr = msg[4:12]
		uarr = msg[12:20]
		aarr = msg[20:28]

		# Arming state
		if sarr == '00000000':
			arst = "Disarmed"
		elif sarr == '10000000':
			arst = "Armed_Away"
		elif sarr == '20000000':
			arst = "Armed_Stay"
		elif sarr == '30000000':
			arst = "Armed_Stay_Instant"
		elif sarr == '40000000':
			arst = "Armed_Night"
		elif sarr == '50000000':
			arst = "Armed_Night_Instant"
		elif sarr == '60000000':
			arst = "Armed_Vacation"
		else:
			arst = "Unknown"

		# Arming readiness
		if uarr == '01111111':
			armrd = "Not_Ready"
		elif uarr == '11111111':
			armrd = "Ready"
		else:
			armrd = "Armed"

		# Alarmed state?
			# try, except for non integer values
			# TODO - handle all different alarm states
		try:
			zonealm = int(aarr[0:1])
		except:
			zonealm = 0

		if zonealm == 0:
			almst = "No_Alarm"
		elif zonealm == 1:
			almst = "Entry_Delay"
		else:
			almst = "Alarm_Tripped"

		return arst, armrd, almst

	# Handle enter exit delay state (EE) message
	def eeStat(self, msg):
		eeType = msg[5:6]

		if eeType == '0':
			eeMsg = "Exit"
		elif eeType == '1':
			eeMsg = "Entry"
		else:
			eeMsg = "No Delay"

		return eeMsg

	# Handle string data (SD) message
	def stringData(self, msg):
		if msg[4:6] == '00':
			dtype = "z"
#			dtype = "Zone"
		elif msg[4:6] == '01':
			dtype = "a"
#			dtype = "Area"
		elif msg[4:6] == '11':
			dtype = "t"
#			dtype = "Thermostat"
		else:
			dtype = "o"
#			dtype = "Other"

		id = msg[6:9]
		name = msg[9:25]

		return dtype, id, name

	# Handle lighting (PC) message
	def lights(self, msg):


		zone = msg[4:7]
		status = msg[7:9]

		return zone, status
	# Handle thermostat report (TR) message
	def thermoRpt(self, msg):
		tnum = int(msg[4:6])
		temp = msg[9:11]
		heat = msg[11:13]
		cool = msg[13:15]

		if 	msg[6:7] == '0':
			mode = "Off"
		elif msg[6:7] == '1':
			mode = "Heat"
		elif msg[6:7] == '2':
			mode = "Cool"
		elif msg[6:7] == '3':
			mode = "Auto"
		elif msg[6:7] == '4':
			mode = "Emer-Heat"
		else:
			mode = "Unknown"

		if msg[7:8] == '0':
			hold = "False"
		else:
			hold = "True"

		if msg[8:9] == '0':
			tfan = "Auto"
		else:
			tfan = "On"

		return tnum, mode, hold, tfan, temp, heat, cool

	# Handle zone change (ZC) message
	def zoneChange(self, msg):
		zone = int(msg[4:7])
		stat = int(msg[7:8], 16)
		zoneS = []

		if 0 < stat < 4:
			status = "Normal"
		elif 4 < stat < 8:
			status = "Trouble"
		elif 8 < stat < 12:
			status = "Violated"
		else:
			status = "Unknown"

		zoneS.append((zone, status))
		return zoneS

	# Handle zone data (ZD) message
	def zoneData(self, msg):
		allZones = msg[4:-4]
		useZones = []
		for lctr in range(0,len(allZones)):
			if allZones[lctr] != '0':
				if allZones[lctr] == '1':
					zoneType = "Burglar Entry/Exit 1"
				elif allZones[lctr] == '2':
					zoneType = "Burglar Entry/Exit 2"
				elif allZones[lctr] == '3':
					zoneType = "Burglar Perimeter Instant"
				elif allZones[lctr] == '4':
					zoneType = "Burglar Interior"
				elif allZones[lctr] == '5':
					zoneType = "Burglar Interior Follower"
				elif allZones[lctr] == '6':
					zoneType = "Burglar Interior Night"
				elif allZones[lctr] == '7':
					zoneType = "Burglar Interior Night Delay"
				elif allZones[lctr] == '8':
					zoneType = "Burglar 24 Hour"
				elif allZones[lctr] == '9':
					zoneType = "Burglar Box Tamper"
				elif allZones[lctr] == ':':
					zoneType = "Fire Alarm"
				elif allZones[lctr] == ';':
					zoneType = "Fire Verified"
				elif allZones[lctr] == '<':
					zoneType = "Fire Supervisory"
				elif allZones[lctr] == '=':
					zoneType = "Aux Alarm 1"
				elif allZones[lctr] == '>':
					zoneType = "Aux Alarm 2"
				elif allZones[lctr] == '?':
					zoneType = "Keyfob"
				elif allZones[lctr] == '@':
					zoneType = "Non Alarm"
				elif allZones[lctr] == 'A':
					zoneType = "Carbon Monoxide"
				elif allZones[lctr] == 'B':
					zoneType = "Emergency Alarm"
				elif allZones[lctr] == 'C':
					zoneType = "Freeze Alarm"
				elif allZones[lctr] == 'D':
					zoneType = "Gas Alarm"
				elif allZones[lctr] == 'E':
					zoneType = "Heat Alarm"
				elif allZones[lctr] == 'F':
					zoneType = "Medical Alarm"
				elif allZones[lctr] == 'G':
					zoneType = "Police Alarm"
				elif allZones[lctr] == 'H':
					zoneType = "Police No Indication"
				elif allZones[lctr] == 'I':
					zoneType = "Water Alarm"
				elif allZones[lctr] == 'J':
					zoneType = "Key Momentary Arm / Disarm"
				elif allZones[lctr] == 'K':
					zoneType = "Key Momentary Arm Away"
				elif allZones[lctr] == 'L':
					zoneType = "Key Momentary Arm Stay"
				elif allZones[lctr] == 'M':
					zoneType = "Key Momentary Disarm"
				elif allZones[lctr] == 'N':
					zoneType = "Key On / Off"
				elif allZones[lctr] == 'O':
					zoneType = "Mute Audibles"
				elif allZones[lctr] == 'P':
					zoneType = "Power Supervisory"
				elif allZones[lctr] == 'Q':
					zoneType = "Temperature"
				elif allZones[lctr] == 'R':
					zoneType = "Analog Zone"
				elif allZones[lctr] == 'S':
					zoneType = "Phone Key"
				elif allZones[lctr] == 'T':
					zoneType = "Intercom Key"

				useZones.append(((lctr + 1), zoneType))

		return useZones

	# Handle zone status (ZS) message
	def zoneStat(self, msg):
		allZones = msg[4:-4]
		useZones = []
		for lctr in range(0,len(allZones)):
			if int(allZones[lctr], 16) != 0:
				if 0 < int(allZones[lctr],16) < 4:
					status = "Normal"
				elif 4 < int(allZones[lctr],16) < 8:
					status = "Trouble"
				elif 8 < int(allZones[lctr],16) < 12:
					status = "Violated"
				else:
					status = "Unknown"

				useZones.append(((lctr + 1), status))

		return useZones

	# Calculate checksum of command
	def checksum(self, cmd):
		summ = 0
		for item in range(len(cmd)):
			summ += ord(cmd[item])
		chksum = "%02X\n" % (summ * -1 % 256)
		return chksum

