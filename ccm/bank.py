
import os, sys
import errno
from ccexception import CCException
from raida import RAIDA
from cc import CloudCoin


class Bank():

	def __init__(self, bankDir):
		self.bankDir = bankDir
		self.inventory = {
			CloudCoin.DEN_1 : [],
			CloudCoin.DEN_5 : [],
			CloudCoin.DEN_25 : [],
			CloudCoin.DEN_100 : [],
			CloudCoin.DEN_250 : []
		}

		self.raida = RAIDA()
	
	def debug(self, info):
		print info

	def getTotal(self):
		iter =  self.inventory.iteritems()

		return reduce(lambda sum, value: sum + len(value[1]) * value[0], iter, 0)

	def getTotalDenomination(self, denomination):
		return len(self.inventory[denomination]) * denomination

	def setInventory(self, coinStacks):
		
		self.raida.initialize()

		if (not self.raida.isRAIDAOK()):
			print "ERROR: RAIDA is not healthy. Giving up"
			sys.exit(1)
			
		for coinName in coinStacks:
			coinStack = coinStacks[coinName]
			for coin in coinStack:
				cc = CloudCoin(coin, coinName)
				try:
					self.inventory[cc.denomination].append(coin)
					self.raida.detectCoin(cc)

					cc.pastStatuses = [2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
					cc.pastStatuses = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

					cc.sync()

					print cc.pastStatuses
					sys.exit(1)
				except KeyError:
					raise CCException("Invalid coin " + coinName + " Denomination " + str(cc.denomination))	

		#		self.inventory[cc.denomination]

		#print self.getTotal()		

