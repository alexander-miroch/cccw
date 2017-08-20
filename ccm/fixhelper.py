
class FixHelper():

	def __init__(self, idx):
		self.data = {
			0: [19, 20, 21, 24,  1,  4,  5,  6],
			1: [20, 21, 22,  0,  2,  5,  6,  7],
			2: [21, 22, 23,  1,  3,  6,  7,  8],
			3: [22, 23, 24,  2,  4,  7,  8,  9],
			4: [23, 24,  0,  3,  5,  8,  9, 10],
			5: [24,  0,  1,  4,  6,  9, 10, 11],
			6: [0,  1,  2,  5,  7, 10, 11, 12],
			7: [1,  2,  3,  6,  8, 11, 12, 13],
			8: [2,  3,  4,  7,  9, 12, 13, 14],
			9: [3,  4,  5,  8, 10, 13, 14, 15],
			10: [4,  5,  6,  9, 11, 14, 15, 16],
			11: [5,  6,  7, 10, 12, 15, 16, 17],
			12: [6,  7,  8, 11, 13, 16, 17, 18],
			13: [7,  8,  9, 12, 14, 17, 18, 19],
			14: [8,  9, 10, 13, 15, 18, 19, 20],
			15: [9, 10, 11, 14, 16, 19, 20, 21],
			16: [10, 11, 12, 15, 17, 20, 21, 22],
			17: [11, 12, 13, 16, 18, 21, 22, 23],
			18: [12, 13, 14, 17, 19, 22, 23, 24],
			19: [13, 14, 15, 18, 20, 23, 24,  0],
			20: [14, 15, 16, 19, 21, 24,  0,  1],
			21: [15, 16, 17, 20, 22,  0,  1,  2],
			22: [16, 17, 18, 21, 23,  1,  2,  3],
			23: [17, 18, 19, 22, 24,  2,  3,  4],
			24: [18, 19, 20, 23,  0,  3,  4,  5]
		}

		self.trustedServers = self.data[idx]

		self.triads = {
			1: [self.trustedServers[0], self.trustedServers[1], self.trustedServers[3]],
			2: [self.trustedServers[1], self.trustedServers[2], self.trustedServers[4]],
			3: [self.trustedServers[3], self.trustedServers[5], self.trustedServers[6]],
			4: [self.trustedServers[4], self.trustedServers[6], self.trustedServers[7]]
		}

		self.currentTriad = self.triads[1]
		self.finished = False


	def setCornerToCheck(self, corner):
		if not corner in self.triads:
			self.finished = True
			return
	
		self.currentTriad = self.triads[corner]
