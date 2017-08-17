

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
			actionCallable = getattr(self, actionName)
			if (not (hasattr(self, actionName) and callable(actionCallable))):
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
				for dirItem in [self.walletHome, self.bankDir, self.importDir, self.exportDir, self.trashDir, self.tmpDir]:
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


#	def __getattr__(self, name):
#		def function():
#			print "xxxx " + name
#
#		return function


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
		print self.walletHome
		
	def _doActionVerify(self):
		coinStacks = self.readCoinsFromDir(self.bankDir)

		self.bank.setInventory(coinStacks)
	#	self.bank.readCoins()

		pass

	def __call__(self, value):
		print "NOT ALLOWED";
		sys.exit(1)
		
