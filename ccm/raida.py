
import os, sys
import errno
from ccexception import CCException
from cc import CloudCoin

import re

from urlparse import urlparse
from threading import Thread
import httplib, sys
from Queue import Queue

try:
	from urllib.request import urlopen, Request, URLError, HTTPError
except ImportError:
	from urllib2 import urlopen, Request, URLError, HTTPError

import json
import ccm
import time

class DetectionAgent():
	def __init__(self, idx, url):
		self.url = url + "/service"
		self.idx = int(idx)
		pass

	def debug(self, message):
		ccm.CCM.log("RAIDA" + str(self.idx) + ": " + message)

	def error(self, message):
		ccm.CCM.log("RAIDA" + str(self.idx) + " ERROR: " + message)

	def ping(self):
		data = self.doRequest("echo")
		try:
			status = data['status']
			if (status == "ready"):
				return True
		except:
			return False

		return False

	def detectCoin(self, cc):
		self.debug("Verifying " + cc.sn + " denomination " + str(cc.denomination))

		an = cc.ans[self.idx]
		pan = cc.pans[self.idx]
		denomination = str(cc.denomination)

		params = "&".join(["nn=" + cc.nn, "sn=" + cc.sn, "an=" + an, "pan=" + pan, "denomination=" + denomination])

		data = self.doRequest("detect?" + params)
		if (data == None):
			return CloudCoin.STATUS_ERROR

		try:
			status = data['status']
			if (status == "pass"):
				return CloudCoin.STATUS_PASS
			elif (status == "fail"):
				return CloudCoin.STATUS_COUNTERFEIT
		except KeyError:
			self.error("Failed to read response. Invalid index: " + data)

		return CloudCoin.STATUS_ERROR
	

	def doRequest(self, path):
		path = "/".join([self.url, path])

		self.debug("Request " + path)

		try:
			headers = { 'User-Agent' : 'Mozilla/5.0' }
			request = Request(path, None, headers)
			response = urlopen(request, timeout = RAIDA.RAIDA_TIMEOUT)
			dataResponse = str(response.read())

			self.debug(dataResponse)
			data = json.loads(dataResponse)

		except URLError as e:
			self.error("Failed to contact: " + e.reason)
			return None
		except HTTPError as e:
			self.error("Failed contact. HTTP error: " + e.reason)
			return None
		except ValueError:
			self.error("Failed to parse response: " + dataResponse)
			return None
		except:
			raise CCException("Interrupted")

		return data
#		response = urlopen(self.RAIDA_LIST_URL, timeout = self.RAIDA_TIMEOUT)

	



class RAIDA():

	RAIDA_CNT = 25
	RAIDA_LIST_URL = "https://www.cloudcoin.co/servers.html"
	RAIDA_LIST_FILE = "raida.json"

	RAIDA_CACHESECS = 86400
	RAIDA_TIMEOUT = 5

	# 80%
	RAIDA_MIN_ACTIVE = 0.8

	def __init__(self):
		self.raida = {}
		self.queue = Queue(self.RAIDA_CNT * 2)
		self.cacheFile =  os.path.join(ccm.CCM.TMPDIR, self.RAIDA_LIST_FILE)

	def fetchRAIDA(self):
		try:
			response = urlopen(self.RAIDA_LIST_URL, timeout = self.RAIDA_TIMEOUT)
			data = str(response.read())

			with open(self.cacheFile, 'w') as f:
				f.write(data)

		except URLError as e:
			raise CCException("Failed to fetch RAIDA list: " + e.reason)
		except HTTPError as e:
			raise CCException("Failed to fetch RAIDA list: " + e.reason + " code: " + str(e.code))
		except IOError:
			raise CCException("Failed to fecth RAIDA list: write to the cachefile failed")
		except:
			raise CCException("Failed to fetch RAIDA list")
		

	def initialize(self):
		rex = re.compile(r'^RAIDA(\d+)\..+')

		try:
			mtime = os.path.getmtime(self.cacheFile)
		except OSError as e:
			if (e.errno != errno.ENOENT):
				raise CCException("Failed to fetch RAIDA list " + str(e))
		
			self.fetchRAIDA()
		except:
			raise CCException("Failed to fetch RAIDA list")
		
		nowTs = int(time.time())
		mtime = int(mtime)
	
		if (nowTs - mtime > self.RAIDA_CACHESECS):
			self.fetchRAIDA()

		try:
			with open(self.cacheFile, 'r') as f:
				data = f.read()

			data = json.loads(data)
			data = data['server']

			for raidaServer in data:
				m = rex.match(raidaServer['url'])
				if (not m):
					raise CCException("Invalid RAIDA url " + raidaServer['url'])

				idx = m.group(1)
				url = "".join([raidaServer['protocol'], "://", raidaServer['url'], ":", raidaServer['port']])

				self.raida[idx] = {
					'url' : url,
					'lastresponse' : None
				}

				self.raida[idx]['agent'] = DetectionAgent(idx, url)

			if (len(self.raida) != self.RAIDA_CNT):
				raise CCException("Invalid RAIDA count: " + str(len(self.raida)))

		except ValueError:
			raise CCException("Failed to parse RAIDA list")
		except KeyError:
			raise CCException("Failed to parse RAIDA list. Invalid index")
		except IOError:
			raise CCException("Failed to parse RAIDA list: read from cachefile failed")
		except CCException as e:
			raise CCException("Failed to parse RAIDA list: " + e.msg)
		except:
			raise CCException("Failed to parse RAIDA list")

	def runThreadPool(self, task, *args):
		for i in range(0, self.RAIDA_CNT):
			thread = Thread(target=task, args=args)
			thread.daemon = True
			thread.start()
			
		try:
			for i in range(0, self.RAIDA_CNT):
				self.queue.put(i)

		except KeyboardInterrupt:
			print "INTERRUPTED"
			sys.exit(1)

		self.queue.join()


	def isRAIDAOK(self):
		self.runThreadPool(self._isRAIDAOK)

		responses = [ self.raida[idx]['lastresponse'] for idx in self.raida if self.raida[idx]['lastresponse'] == True ]
		quorum = len(responses)

		pct = float(quorum) / self.RAIDA_CNT
		ccm.CCM.log("RAIDA pct " + str(pct) + " quorum " + str(quorum))

		if (pct < self.RAIDA_MIN_ACTIVE):
			return False

		return True

	def _isRAIDAOK(self):
		try:
			idx = str(self.queue.get())
			detectionAgent = self.raida[idx]['agent']
			self.raida[idx]['lastresponse'] = detectionAgent.ping()
		except:
			ccm.CCM.log("Damn failed")
			self.queue.task_done()

		self.queue.task_done()


	def detectCoin(self, cc):
		self.runThreadPool(self._detectCoin, cc)

	def _detectCoin(self, cc):
			
		try:
			idx = str(self.queue.get())
			detectionAgent = self.raida[idx]['agent']

			status = detectionAgent.detectCoin(cc)
			intIdx = int(idx)
			cc.pastStatuses[intIdx] = status
		except KeyError:
			self.queue.task_done()
			raise CCException("Failed to set status. Invalid index")	
		except:
			self.queue.task_done()
			raise

		self.queue.task_done()






