#!/usr/bin/python
import cv2
import sys
import json
import argparse
import os

from os.path import dirname
sys.path.append(dirname(dirname(__file__)))

from cv2utils import cv2utils
from pokeocr import pokeocr
from pokediscord import pokediscord

parser = argparse.ArgumentParser(description='Parse an EX raid image (low level)')
parser.add_argument('-f', dest='configfile', default='config/exraid.json')
parser.add_argument('-l', dest='language')
parser.add_argument('image')
args = parser.parse_args()

f = open(args.configfile)
config = json.load(f)
f.close()

top = cv2.imread(config['top_image'])
bottom = cv2.imread(config['bottom_image'])
image = cv2.imread(args.image)

if args.language:
  os.environ['TESSDATA_PREFIX'] = '.'
  ocr = pokeocr(config['location_regular_expression'], args.language)
else:
  ocr = pokeocr(config['location_regular_expression'])

print ocr.scanExRaidImage(image, top, bottom, debug=True)
