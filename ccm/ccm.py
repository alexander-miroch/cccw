

import os, sys
import errno
import fileinput
from bank import Bank
from ccexception import CCException
import json

import logging

class CCM():

	TMPDIR = "/tmp"
	logger = None

	def __init__(self, args):
		self.args = args
		self.walletHome = os.path.expanduser(self.args['wdir'])
		self.bankDir = os.path.join(self.walletHome, "Bank")
		self.importDir = os.path.join(self.walletHome, "Import")
		self.exportDir = os.path.join(self.walletHome, "Export")
		self.trashDir = os.path.join(self.walletHome, "Trash")
		self.backupDir = os.path.join(self.walletHome, "Backup")
		self.tmpDir = os.path.join(self.walletHome, "tmp")

		CCM.TMPDIR = self.tmpDir

		self.bank = Bank(self.bankDir)

	def initLogger(self):
		CCM.logger = logging.getLogger("CloudCoin")
		CCM.logger.setLevel(logging.INFO)

		handler = logging.FileHandler(os.path.join(self.tmpDir, 'hello.log'))
		handler.setLevel(logging.INFO)

		# create a logging format
		formatter = logging.Formatter('%(asctime)s %(levelname)s : %(message)s')
		handler.setFormatter(formatter)

		CCM.logger.addHandler(handler)

	@staticmethod
	def log(msg):
		CCM.logger.info(msg)

	def error(self, error):
		print "ERROR: " + error
		sys.exit(1)

	def process(self):
		action = self.args['action']

		try:
			self.verifyWallet()
			self.initLogger()

			actionName = "_doAction" + action[0].upper() + action[1:]
			if (not hasattr(self, actionName)):
				self.error("Invalid action: " + action)

			actionCallable = getattr(self, actionName)
			if (not callable(actionCallable)):
				self.error("Invalid action: " + action)

			actionCallable()
		except CCException as e:
			self.error(e.getMessage())
	#	except:
	#		self.error("Failed to perform action")

	def confirm(self, message):
		input = raw_input(message)

		if (input == 'Y' or input == 'y'):
			return 

		raise CCException("Abort")

	def verifyWallet(self):
		
		if (not os.path.isdir(self.walletHome)):
			self.confirm("Wallet Directory " + self.walletHome + " does not exist. Init it? (y/n)")
			try:
				for dirItem in [self.walletHome, self.bankDir, self.importDir, self.exportDir, self.trashDir, self.tmpDir, self.backupDir]:
					os.mkdir(dirItem)
			except OSError as e:
				if (e.errno != errno.EEXIST):
					raise CCException("Failed to init Wallet Directory " + self.walletHome)

		if (not os.access(self.bankDir, os.W_OK)):
			raise CCException("BANK folder is not writeable")

		if (not os.access(self.importDir, os.W_OK)):
			raise CCException("IMPORT folder is not readable")

		if (not os.access(self.exportDir, os.W_OK)):
			raise CCException("EXPORT folder is not writable")

		if (not os.access(self.trashDir, os.W_OK)):
			raise CCException("TRASH folder is not writable")

		if (not os.access(self.tmpDir, os.W_OK)):
			raise CCException("TMP folder is not writable")

		if (not os.access(self.backupDir, os.W_OK)):
			raise CCException("BACKUP folder is not writable")


	def readCoin(self, filePath):
		try:
			with open(filePath) as fd:
				data = json.load(fd)
				return  data['cloudcoin']
		except OSError:
			raise CCException("Failed to read file " + filePath)
		except ValueError:
			raise CCException("JSON parse error: " + filePath)
		except KeyError:
			raise CCException("Invalid coin: " + filePath)

		raise CCException("Corrupted file " + fileParh)	


	def readCoinsFromDir(self, dirName):
		inventory = {}
		try:
			filePath = ""
			files = [ f for f in os.listdir(dirName) if os.path.isfile(os.path.join(dirName, f)) ]

			for f in files:
				filePath = os.path.join(dirName, f)
				with open(filePath) as fd:
					data = json.load(fd)
					inventory[f] = data['cloudcoin']
		except OSError:
			raise CCException("Failed to read files from BANK")
		except ValueError:
			raise CCException("JSON parse error: " + filePath)
		except KeyError:
			raise CCException("Invalid coin: " + filePath)

		return inventory


	def _doActionBank(self):
		coinStacks = self.readCoinsFromDir(self.bankDir)
		self.bank.setInventory(coinStacks)
		self.bank.showOff()
		
	def _doActionVerify(self):
		coinStacks = self.readCoinsFromDir(self.bankDir)
		self.bank.setInventory(coinStacks)
		self.bank.verifyCoins()


	def _doActionImport(self):
		if (not 'path' in self.args or self.args['path'] is None):
			paths = [ self.importDir ]
		else:
			paths = self.args['path']

		inventory = {}
		for path in paths:
			thash = {}
			if (os.path.isdir(path)):
				thash = self.readCoinsFromDir(path)
				for fileName in thash:
					if (fileName in inventory):
						raise CCException("Duplicate filename: " + fileName)

					inventory[fileName] = thash[fileName]
			elif (os.path.isfile(path)):
				fileName = os.path.basename(path)
				if (fileName in inventory):
					raise CCException("Duplicate filename: " + fileName)

				fileData = self.readCoin(path)
				inventory[fileName] = fileData
			else:
				raise CCException("Invalid path '" + path + "' or it does not exist")

		self.bank.setInventory(inventory)
		self.bank.importCoins()

	def _doActionFixfracked(self):
		coinStacks = self.readCoinsFromDir(self.bankDir)
		self.bank.setInventory(coinStacks)
		self.bank.fixCoins()

	def _doActionExport(self):
	
		if (not 'coins' in self.args or self.args['coins'] is None):
			raise CCException("No coins specified")

		coins = self.args['coins']
		if (len(coins) > 5 or len(coins) == 0):
			raise CCException("Invalid number of denominations")


		exportData = {}
		for item in coins:
			try:
				denomination, count = map(int, item.split(":"))
			except ValueError as e:
				raise CCException("Invalid coins format. Specify <denomination:count>, eg. 250:10")


			if (not denomination in self.bank.inventory):
				raise CCException("Unknown denomination: " + str(denomination))

			exportData[denomination] = count

		coinStacks = self.readCoinsFromDir(self.bankDir)
		self.bank.setInventory(coinStacks)
		self.bank.exportCoins(exportData, self.args['stack'], self.exportDir, self.backupDir)

	def __call__(self, value):
		print "NOT ALLOWED";
		sys.exit(1)
		
