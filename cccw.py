#!/usr/bin/env python


import argparse

from ccm.config import *
from ccm.ccm import CCM


actionChoises = ['bank', 'verify', 'import', 'export', 'fixfracked']
actionChoisesStr = ", ".join(actionChoises)

parser = argparse.ArgumentParser(prog='cccw', description='CloudCoin Colsole Wallet')
parser.add_argument('action', metavar='ACTION', choices=actionChoises, type=str, help='Action to perform: ' + actionChoisesStr)
parser.add_argument('--wdir', metavar='<dirname>', default="~/.cccw", type=str, help='Path to the wallet directory')
parser.add_argument('--path', metavar='<dirname|filename>', type=str, help='Path to the files or directorie to import, separated by space', nargs='*')
parser.add_argument('--coins', metavar='<denomination:count>', type=str, help='Coins to export', nargs='*')

args = parser.parse_args()
args = vars(args)

ccm = CCM(args)
ccm.process()

