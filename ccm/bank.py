
import os, sys
import errno
from ccexception import CCException
from raida import RAIDA
from cc import CloudCoin

import ccm
import signal
import json

import time

import traceback

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
		self.signalRaised = False
		signal.signal(signal.SIGUSR1, self.sigIntHandler)
	
	def output(self, info):
		print info

	def getTotalCoins(self):
		iter =  self.inventory.iteritems()

		return reduce(lambda sum, value: sum + len(value[1]), iter, 0)
		

	def getTotal(self):
		iter =  self.inventory.iteritems()

		return reduce(lambda sum, value: sum + len(value[1]) * value[0], iter, 0)

	def getTotalDenomination(self, denomination):
		return len(self.inventory[denomination]) * denomination

	def setInventory(self, coinStacks):
		for coinName in coinStacks:
			coinStack = coinStacks[coinName]
			for coin in coinStack:
				cc = CloudCoin(coin, coinName)
				try:
					self.inventory[cc.denomination].append(cc)
				except KeyError:
					raise CCException("Invalid coin " + coinName + " Denomination " + str(cc.denomination))	

		

	def sigIntHandler(self, signal, frame):
		if (self.signalRaised):
			sys.exit(1)

		self.signalRaised = True
		
	def showOff(self):
		print "Bank Inventory"
		for denomination in sorted(self.inventory.iterkeys()):
			coins =  self.inventory[denomination]
			totalDenomination = len(coins)

			denStr = str(denomination) + "s"	
			denTotal =  self.getTotalDenomination(denomination)

			print "{:>10}: {:>10}, coins: {}".format(denStr, denTotal, str(totalDenomination))

		print "{:>10}: {:>10}, coins: {}".format("Total", str(self.getTotal()), str(self.getTotalCoins()))

	def initRAIDA(self):
		self.raida.initialize()
		if (not self.raida.isRAIDAOK()):
			raise CCException("ERROR: RAIDA is not healthy. Giving up")

	def ifCoinExists(self, cc, folder):
		fullName = cc.getFullName()
		return os.path.exists(os.path.join(folder, fullName))

	def backupCoin(self, cc, srcFolder, dstFolder):

		fullName = cc.getFullName()
		srcpath = os.path.join(srcFolder, fullName)
		dstpath = os.path.join(dstFolder, fullName)
		
		os.rename(srcpath, dstpath)

	def saveCoins(self, coins, folder):
		stackCoins = []
		for cc in coins:
			jhash = cc()
			stackCoins.append(jhash['cloudcoin'][0])

		total = len(stackCoins)

		ts = str(int(time.time()))

		fullName = ".".join([str(total), "CloudCoins", ts, "stack"])
		path = os.path.join(folder, fullName)

		ccm.CCM.log("Saving " + path)
		if (os.path.exists(path)):
			raise CCException("File " + path + " already exist")

		stackCoins = {
			'cloudcoin' : stackCoins
		}	

		hash = json.dumps(stackCoins)


		with open(path, "w") as fd:
			fd.write(hash)



	def saveCoin(self, cc, folder):

		hash = json.dumps(cc())

		fullName = cc.getFullName()
		path = os.path.join(folder, fullName)
		
		ccm.CCM.log("Saving " + path)
		if (os.path.exists(path)):
			raise CCException("File " + path + " already exist")

		with open(path, "w") as fd:
			fd.write(hash)

	def printStats(self, stats):
		total = str(self.getTotalCoins())

		print "Total Analyzed: " + str(self.getTotal()) + " from " + total + " coins"
		if (CloudCoin.COIN_STATUS_OK in stats):
			print "{:<16} {:>8}" .format("Valid:", stats[CloudCoin.COIN_STATUS_OK])

		if (CloudCoin.COIN_STATUS_FRACKED in stats):
			print "{:<16} {:>8}" .format("Fracked:", stats[CloudCoin.COIN_STATUS_FRACKED])

		if (CloudCoin.COIN_STATUS_COUNTERFEIT in stats):
			print "{:<16} {:>8}" .format("Counterfeit:", stats[CloudCoin.COIN_STATUS_COUNTERFEIT])

		if (CloudCoin.COIN_STATUS_SUSPECT in stats):
			print "{:>32} {:>8}" .format("Suspect:", stats[CloudCoin.COIN_STATUS_SUSPECT])


	def importCoins(self):
		self.initRAIDA()		

		for denomination in self.inventory:
			coins = self.inventory[denomination]
			for cc in coins:
				fullName = cc.getFullName()
				path = os.path.join(self.bankDir, fullName)
				if (os.path.isfile(path)):
					raise CCException("Error: " + path + " already exists. Will not import anything")

		self.verifyCoins(True)
				

	def verifyCoins(self, needPown=False):
		self.initRAIDA()		

		i, total = 1, self.getTotalCoins()
		stats = {}

		ccm.CCM.log("POWN " + str(needPown))

		for denomination in sorted(self.inventory.iterkeys()):
			coins =  self.inventory[denomination]
			denStr = str(denomination) + "s"
			totalDenomination = len(coins)
			if (totalDenomination == 0):
				continue

			multiAtOnce = 5
			chunks = totalDenomination / multiAtOnce 
			if (totalDenomination % multiAtOnce):
				chunks += 1
			ist, ifi = 0, 0

			for j in xrange(0, chunks):
				ist = j * multiAtOnce
				ifi = ist + multiAtOnce
				clen = multiAtOnce
				if (ifi >= totalDenomination):
					ifi = totalDenomination + 1
					clen = ifi - totalDenomination + 1

				coinsChunk = coins[ist:ifi]
				sys.stdout.write("Chunk {:>6}/{} \n".format(j + 1, chunks))
				ccm.CCM.log("Multiverify chunk " + str(j + 1) + " of " + str(chunks)) 
				for idx, cc in enumerate(coinsChunk):
					ccname = cc.name[:48]
					ccm.CCM.log("Multiverify: " + cc.name + " " + str(cc.sn) + " " + denStr)

					if (needPown):
						cc.generatePans()

				ccm.CCM.log("Before")
				for cc in coinsChunk:
					ccm.CCM.log(cc.pastStatuses)

				self.raida.multiDetectCoins(coinsChunk)

				ccm.CCM.log("After")
				for cc in coinsChunk:
					ccm.CCM.log(cc.pastStatuses)

				fracked = 0
				counterfeit = 0
				valid = 0
				error = 0
				messages = []

				for idx, cc in enumerate(coinsChunk):
					cc.sync()

					if (not cc.status in stats):
						stats[cc.status] = 0
	
					stats[cc.status] += 1

					if (cc.status == CloudCoin.COIN_STATUS_OK):
						valid += 1
					elif (cc.status == CloudCoin.COIN_STATUS_COUNTERFEIT):
						counterfeit += 1
					elif (cc.status == CloudCoin.COIN_STATUS_FRACKED):
						fracked += 1
					else:
						error += 1
				
					messages.append({
						'sn' : cc.sn,
						'status' : cc.showStatus()
					})

					ccname = cc.name[:48]
					sys.stdout.write("{}/{}{:>48}/{:<8} {:>4}:  ".format(idx + 1, clen, ccname, cc.sn, denStr))
					sys.stdout.write(cc.showStatus())
					sys.stdout.write("\n")
					ccm.CCM.log("Multiveried: " + cc.name + " " + str(cc.sn) + " " + denStr)

					if (needPown):
						if (cc.status == CloudCoin.COIN_STATUS_OK or cc.status == CloudCoin.COIN_STATUS_FRACKED):
							try:
								self.saveCoin(cc, self.bankDir)
							except OSError as e:
								ccm.CCM.log("Failed to save coin: " + e.strerror)
								raise CCException("Failed to save coin, OS Error: " + e.strerror)
							except ValueError:
								ccm.CCM.log("Failed to save coin: JSON")
								raise CCException("Failed to create JSON from the coin")
							except IOError:
								ccm.CCM.log("Failed to save coin: " + e.strerror)
								raise CCException("Failed to save coin on disk: " + e.strerror)
							except CCException:
								raise
							except:
								trace = str(traceback.format_exception(*sys.exc_info()))
								ccm.CCM.log("Failed to save coin: " + trace)
								raise CCException("Generic error")

				print "Result (ok/fracked/counterfeit/error): " + str(valid) + "/" + str(fracked) + "/" + str(counterfeit) + "/" + str(error) + "\n"
				ccm.CCM.log("Result (ok/fracked/counterfeit/error): " + str(valid) + "/" + str(fracked) + "/" + str(counterfeit) + "/" + str(error))
				ccm.CCM.log("Result: " + str(messages))

					

		
		self.printStats(stats)

	def fixCoins(self):
		self.initRAIDA()		

		i, total = 1, self.getTotalCoins()

		print "Searching for fracked coins"
		for denomination in sorted(self.inventory.iterkeys()):
			coins =  self.inventory[denomination]
			denStr = str(denomination) + "s"	

			totalDenomination = len(coins)
			for idx, cc in enumerate(coins, 1):
				try:
					if (self.signalRaised):
						self.signalRaised = False

					ccname = cc.name[:48]
					sys.stdout.write("{:>6}/{} : ".format(i, total))

					i += 1
					self.raida.detectCoin(cc)
					cc.sync()

					if (cc.status == CloudCoin.COIN_STATUS_FRACKED):
						ccm.CCM.log("Fixing was requested " + cc.name + "." + str(cc.sn))
						print "Fixing coin. It is fracked: " + cc.name + " sn:" + str(cc.sn)	
						self.raida.fixCoin(cc)
						cc.sync()
						print "RESULT OF FIXING: " + cc.showStatus()
					else:
						print "SKIP"


				except KeyboardInterrupt:
					raise CCException("Interrputed")
	

	def exportCoins(self, exportData, isStack, folder, backupFolder):
		self.initRAIDA()		

		toExport = []
		for denomination in exportData:
			count = exportData[denomination]
			denStr = str(denomination) + "s"	
			coins =  self.inventory[denomination]
			if (count > len(coins)):
				raise CCException("Not enough coins of denomination " + denStr)

			exported = 0
			for idx, cc in enumerate(coins, 1):
				if (self.ifCoinExists(cc, folder)):
					raise CCException("Coin " + cc.getFullName() + " already exists in Export Dir")

				if (self.ifCoinExists(cc, backupFolder)):
					raise CCException("Coin " + cc.getFullName() + " already exists in Backup Dir")

				ccname = cc.name[:48]

				ccm.CCM.log("Coin " + ccname + "/" + cc.sn + " " + denStr);
				print "{:>6}/{} {:>48}/{:<8} {:>4}".format(idx, count, ccname, cc.sn, denStr)

			#	self.raida.detectCoin(cc)
			#	cc.sync()

			#	if (cc.status != CloudCoin.COIN_STATUS_OK and cc.status != CloudCoin.COIN_STATUS_FRACKED):
			#		raise CCException("Coin " + cc.getFullName() + " is not valid: " + cc.showStatus())

				cc.aoid = []
				toExport.append(cc)
				exported += 1

				if (exported >= count):
					break

		ccm.CCM.log("Exporting " + str(count) + "cc denomination " + denStr + " stack: " + str(isStack))
		print "Exporting " + str(count) + "cc denomination " + denStr + " stack: " + str(isStack)

		if (isStack):
			try:
				self.saveCoins(toExport, folder)
				for cc in toExport:
					self.backupCoin(cc, self.bankDir, backupFolder)
			except OSError as e:
				ccm.CCM.log("Failed to save coins: " + e.strerror)
				raise CCException("Failed to save coins, OS Error: " + e.strerror)
			except ValueError:
				ccm.CCM.log("Failed to save coin: JSON")
				raise CCException("Failed to create JSON from the coins")
			except IOError:
				ccm.CCM.log("Failed to save coins: " + e.strerror)
				raise CCException("Failed to save coins on disk: " + e.strerror)
			except CCException:
				raise 
			except:
				trace = str(traceback.format_exception(*sys.exc_info()))
				ccm.CCM.log("Failed to save coins: " + trace)
				raise CCException("Generic error")

			return

		for cc in toExport:
			try:
				self.saveCoin(cc, folder)
				self.backupCoin(cc, self.bankDir, backupFolder)
			except OSError as e:
				ccm.CCM.log("Failed to save coin: " + e.strerror)
				raise CCException("Failed to save coin, OS Error: " + e.strerror)
			except ValueError:
				ccm.CCM.log("Failed to save coin: JSON")
				raise CCException("Failed to create JSON from the coin")
			except IOError:
				ccm.CCM.log("Failed to save coin: " + e.strerror)
				raise CCException("Failed to save coin on disk: " + e.strerror)
			except CCException:
				raise 
			except:
				trace = str(traceback.format_exception(*sys.exc_info()))
				ccm.CCM.log("Failed to save coin: " + trace)
				raise CCException("Generic error")
			

				


