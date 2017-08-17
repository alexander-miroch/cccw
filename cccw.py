#!/usr/bin/env python


import argparse

from ccm.config import *
from ccm.ccm import CCM



parser = argparse.ArgumentParser(prog='cccw', description='CloudCoin Colsole Wallet')
parser.add_argument('action', metavar='ACTION', type=str, help='Action to perform: bank, export, import, verify')
parser.add_argument('--wdir', metavar='<dirname>', default="~/.cccw", type=str, help='Path to the wallet directory')

args = parser.parse_args()
args = vars(args)

ccm = CCM(args)
ccm.process()

