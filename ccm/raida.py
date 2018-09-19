
import os, sys
import errno
from ccexception import CCException
from cc import CloudCoin

import re

from urlparse import urlparse
from threading import Thread
import httplib, sys
from Queue import Queue

#try:
#	from urllib.request import urlopen, Request, URLError, HTTPError
#except ImportError:
from urllib2 import urlopen, Request, URLError, HTTPError

import urllib
import urllib2

import ssl

import json
import ccm
import time

from fixhelper import FixHelper


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

	def fixCoin(self, cc, triad, tickets, raidaIdx):
		self.debug("Fixing " + cc.sn + " " + str(cc.denomination) + "s")

		an = cc.ans[raidaIdx]
		
		self.debug("an " + an)

		params = []
		for i in range(0, 3):
			params.append("fromserver" + str(i + 1) + "=" + str(triad[i]))
			params.append("message" + str(i + 1) + "=" + tickets[i])

		# No error. PAN (no AN)
		params.append("pan=" + an)
		params = "&".join(params)
		data = self.doRequest("fix?" + params)
		if (data == None):
			return None

		try:
			status = data['status']
			if (status == "success"):
				return True
			
			return False
		except KeyError:
			self.error("Failed to read response. Invalid index: " + str(data))

		return False

	def detectCoins(self, coinsChunk):
		self.debug("Detecting " + str(len(coinsChunk)) + " coins")

		nns = []
		ans = []
		pans = []
		denomination = []
		sns = []

		results = []
		for cc in coinsChunk:
			nns.append("nns[]=1")
			sns.append("sns[]=" + str(cc.sn))
			ans.append("ans[]=" + str(cc.ans[self.idx]))
			pans.append("pans[]=" + str(cc.pans[self.idx]))
			denomination.append("denomination[]=" + str(cc.denomination))

			results.append(CloudCoin.STATUS_ERROR)

		data = []
		data.append("&".join(nns))
		data.append("&".join(sns))
		data.append("&".join(ans))
		data.append("&".join(pans))
		data.append("&".join(denomination))

		data = "&".join(data)

		rv = self.doPost('multi_detect', data)
		if (rv is None):
			self.error("None response from doPost")
			return results

		if (len(rv) != len(coinsChunk)):
			self.error("Invalid response: " + str(len(rv)) + " vs our " + str(len(coinsChunk)))
			return results

		for idx, res in enumerate(rv):
			if not "status" in res:
				self.error("No status field for coin idx: " + str(idx))
				continue

			rstatus = res['status']
			
			if (rstatus == CloudCoin.STATUS_PASS):
				rsn = res['sn']
				if (coinsChunk[idx].sn != rsn):
					self.error("SN mismatch for idx " + str(idx) + ": " + str(coinsChunk[idx].sn) + " vs " + rsn)
					continue

			if (rstatus == "pass"):
				results[idx] = CloudCoin.STATUS_PASS
			elif (rstatus == "fail"):
				results[idx] = CloudCoin.STATUS_COUNTERFEIT

		return results

	def detectCoin(self, cc):
		self.debug("Detecting " + cc.sn + " " + str(cc.denomination) + "s")

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
			self.error("Failed to read response. Invalid index: " + str(data))

		return CloudCoin.STATUS_ERROR
	

	def getTicket(self, cc, an):
		self.debug("Obtaining ticket " + cc.sn + " " + str(cc.denomination) + "s ans " + an)

		# an and pan are equal
		denomination = str(cc.denomination)

		params = "&".join(["nn=" + cc.nn, "sn=" + cc.sn, "an=" + an, "pan=" + an, "denomination=" + denomination])

		data = self.doRequest("get_ticket?" + params)
		if (data == None):
			return None
		
		try:
			status = data['status']
			if (status != 'ticket'):
				self.error("Failed to read response. Invalid status: " + str(status))
				return None
			
			ticket = data['message']

			return ticket
		except KeyError:
			self.error("Failed to read response. Invalid index: " + str(data))

		return None

	def doPost(self, url, data):
		handler = urllib2.HTTPHandler()
		opener = urllib2.build_opener(handler)
		
		path = "/".join([self.url, url])

		request = urllib2.Request(path, data=data)
		request.add_header('Content-Type', 'application/x-www-form-urlencoded')
		request.add_header('User-Agent', 'Mozilla/5.0')

		self.debug("Request " + path + " " + data)

		try:
			connection = opener.open(request)
			if (connection.code != 200):
				self.error("Invalid code " + str(connection.code))
				return None

			data = connection.read()
			self.debug(data)
			data = json.loads(data)
		except urllib2.HTTPError,e:
			self.error("Error " + str(e))
			return None
		except URLError as e:
			self.error("Failed to contact: " + str(e.reason))
			return None
		except HTTPError as e:
			self.error("Failed contact. HTTP error: " + str(e.reason))
			return None
		except ValueError:
			self.error("Failed to parse response: " + data)
			return None
		except ssl.SSLError as e:
			self.error("Failed contact. HTTP SSL error: " + e.args[0])
			return None
		except:
			raise CCException("Interrupted")

		return data

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
			self.error("Failed to contact: " + str(e.reason))
			return None
		except HTTPError as e:
			self.error("Failed contact. HTTP error: " + str(e.reason))
			return None
		except ValueError:
			self.error("Failed to parse response: " + dataResponse)
			return None
		except ssl.SSLError as e:
			self.error("Failed contact. HTTP SSL error: " + e.args[0])
			return None
		except:
			raise CCException("Interrupted")

		return data


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

		nowTs = int(time.time())

		try:
			mtime = os.path.getmtime(self.cacheFile)
		except OSError as e:
			if (e.errno != errno.ENOENT):
				raise CCException("Failed to fetch RAIDA list " + str(e))
		
			mtime = nowTs
			self.fetchRAIDA()
		except:
			raise CCException("Failed to fetch RAIDA list")
		
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


	def multiDetectCoins(self, coinsChunk):
		self.runThreadPool(self._multiDetectCoins, coinsChunk)

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
			ccm.CCM.log("RAIDA thread error. Invalid index: " + idx + " " + str(cc.pastStatuses) + " " + str(self.raida))
		except:
			ccm.CCM.log("RAIDA thread error. Generic: " + idx + " " + str(cc.pastStatuses) + " " + str(self.raida))
			self.queue.task_done()
		else:
			self.queue.task_done()

	def _multiDetectCoins(self, coinsChunk):
		try:
			idx = str(self.queue.get())
			detectionAgent = self.raida[idx]['agent']

			results = detectionAgent.detectCoins(coinsChunk)
			intIdx = int(idx)
			for idx, rstatus in enumerate(results):
				coinsChunk[idx].pastStatuses[intIdx] = rstatus

		#	cc.pastStatuses[intIdx] = status
		except KeyError:
			self.queue.task_done()
			ccm.CCM.log("RAIDA thread error. Invalid index: " + idx + " " + str(self.raida))
#		except:
#			ccm.CCM.log("RAIDA thread error. Generic: " + idx + " " + str(self.raida))
#			self.queue.task_done()
		else:
			self.queue.task_done()

		
	def fixCoin(self, cc):
		cc.setPansToAns()

		raidaIsInvalidData = [ False for i in range(0, self.RAIDA_CNT) ]

		for i, status in enumerate(cc.pastStatuses):
			if (raidaIsInvalidData[i] or status != CloudCoin.STATUS_COUNTERFEIT):
				continue
		
			fixer = FixHelper(i)
			corner = 1

			ccm.CCM.log("Iteration: " + str(i) + " fixer " + str(fixer.currentTriad))
			print "Interation for RAIDA" + str(i)

			while not fixer.finished:
				trustedServerAns = [ 
					cc.ans[fixer.currentTriad[0]],
					cc.ans[fixer.currentTriad[1]],
					cc.ans[fixer.currentTriad[2]]
				]
	
				ccm.CCM.log(" ans: " + str(trustedServerAns))
		
				tickets = []
				for ti in range(0, 3):
					agentIdx = str(fixer.currentTriad[ti])
					detectionAgent = self.raida[agentIdx]['agent']
	
					sys.stdout.write('Requesting ticket RAIDA' + agentIdx + ': ')
					ccm.CCM.log('Requesting ticket RAIDA' + agentIdx + ': ')
					tickets.append(detectionAgent.getTicket(cc, trustedServerAns[ti]))

					ccm.CCM.log(str(tickets[ti]))
					print str(str(tickets[ti]))

				if (None in tickets):
					corner += 1

					ccm.CCM.log("Corner " + str(corner))
					fixer.setCornerToCheck(corner);
	
					if (fixer.finished):
						ccm.CCM.log("Setting RAIDA" + str(i) + " invalid")
						raidaIsInvalidData[i] = True	
				else:
					agentIdx = str(i)
					detectionAgent = self.raida[agentIdx]['agent']
					sys.stdout.write('Requesting fix from RAIDA' + agentIdx + ': ')
					ccm.CCM.log('Requesting fix from RAIDA' + agentIdx + ': ')

					result = detectionAgent.fixCoin(cc, fixer.currentTriad, tickets, i)
					if (result):
						ccm.CCM.log("success")
						print "success"
						cc.pastStatuses[i] = CloudCoin.STATUS_PASS
						fixer.finished = True

					else:
						ccm.CCM.log("failed")
						print "failed"
		
						corner += 1
						ccm.CCM.log("Corner " + str(corner))
						fixer.setCornerToCheck(corner);
	
						if (fixer.finished):
							ccm.CCM.log("Setting RAIDA" + str(i) + " invalid")
							raidaIsInvalidData[i] = True
	
		ccm.CCM.log("Fixing done")		

