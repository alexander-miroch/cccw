
import os
import raida
import time
import datetime


class CloudCoin():

	DEN_1 = 1
	DEN_5 = 5
	DEN_25 = 25
	DEN_100 = 100
	DEN_250 = 250

	STATUS_PASS = 1
	STATUS_COUNTERFEIT = 2
	STATUS_ERROR = 3
	STATUS_UNKNOWN = 4


	COIN_STATUS_OK = 1
	COIN_STATUS_COUNTERFEIT = 2
	COIN_STATUS_FRACKED = 3
	COIN_STATUS_SUSPECT = 4

	def __init__(self, coin, name):
		self.name = name
		self.ed = coin['ed']
		self.ans = coin['an']
		self.sn = coin['sn']
		self.nn = coin['nn']

		self.aoid = self.pown = []
		if ('pown' in coin):
			self.pown = coin['pown']

		if ('aoid' in coin):
			self.aoid = coin['aoid']

		self.denomination = self.getDenomination()
		self.setPansToAns()

		self.chainLen =  raida.RAIDA.RAIDA_CNT
		self.status = self.COIN_STATUS_SUSPECT
		self.pastStatuses = [ self.STATUS_UNKNOWN for idx in range(0, self.chainLen) ]

		self.resetStats()
		self.statusCounts[self.STATUS_UNKNOWN] = self.chainLen

		self.type = "stack"

	def setExpirationDate(self):
		self.ed = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%Y')

	def setAOID(self):
		self.aoid = []
		self.aoid.append("-".join(map(lambda x: str(x), self.pastStatuses)))
		self.aoid.append(str(self.status))

	def getFullName(self):
		return ".".join([str(self.denomination), "CloudCoin", str(self.nn), str(self.sn), self.type])

	def resetStats(self):
		self.statusCounts = {
			self.STATUS_PASS : 0,
			self.STATUS_COUNTERFEIT : 0,
			self.STATUS_ERROR : 0,
			self.STATUS_UNKNOWN : 0
		}

	def showStatus(self):
		statuses = {
			self.COIN_STATUS_OK : 'OK',
			self.COIN_STATUS_COUNTERFEIT : 'Counterfeit',
			self.COIN_STATUS_FRACKED : 'Fracked',
			self.COIN_STATUS_SUSPECT : 'Suspect',
		}


		return statuses[self.status]
	
	def setPansToAns(self):
		self.pans = self.ans[:]
	

	def sync(self):
		self.resetStats()
		for i in range(0, self.chainLen):
			pastStatus = self.pastStatuses[i]
			self.statusCounts[pastStatus] += 1

			if (pastStatus == self.STATUS_PASS):
				self.ans[i] = self.pans[i]
		
		self.setExpirationDate()

		if (self.statusCounts[self.STATUS_UNKNOWN] > self.chainLen / 2):
			self.status = self.COIN_STATUS_SUSPECT
		elif (self.statusCounts[self.STATUS_COUNTERFEIT] > self.statusCounts[self.STATUS_PASS]):
			self.status = self.COIN_STATUS_COUNTERFEIT
		elif (self.statusCounts[self.STATUS_COUNTERFEIT] > 0 or self.statusCounts[self.STATUS_ERROR] > 0):
			self.status = self.COIN_STATUS_FRACKED
		else:
			self.status = self.COIN_STATUS_OK
			
		self.setAOID()
	
	def generatePans(self):
		self.pans = [ str(os.urandom(16).encode('hex')) for x in range(0, self.chainLen) ]
	
	def getDenomination(self):
		sn = int(self.sn)
		if (sn < 1):
			return 0

		if (sn < 2097153):
			return self.DEN_1

		if (sn < 4194305):
			return self.DEN_5

		if (sn < 6291457):
			return self.DEN_25

		if (sn < 14680065):
			return self.DEN_100

		if (sn < 16777217):
			return self.DEN_250

		return 0

	def __call__(self):
		ccSerialized = {
			'cloudcoin' : [{
				'sn' : self.sn,
				'nn' : self.nn,
				'ed' : self.ed,	
				'an' : self.ans,
				'aoid' : self.aoid
			}]
		}

		if (len(self.pown) > 0):
			ccSerialized['cloudcoin']['pown'] = self.pown

		return ccSerialized

