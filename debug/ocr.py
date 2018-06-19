#!/usr/bin/python
import cv2
import sys
import json

from os.path import dirname
sys.path.append(dirname(dirname(__file__)))

from cv2utils import cv2utils
from pokeocr import pokeocr
from pokediscord import pokediscord

f = open('config/exraid.json')
config = json.load(f)
f.close()

top = cv2.imread(config['top_image'])
bottom = cv2.imread(config['bottom_image'])
image = cv2.imread(sys.argv[1])

ocr = pokeocr(config['location_regular_expression'])

raidInfo = ocr.scanExRaidImage(image, top, bottom)

print raidInfo.__dict__
print pokediscord.generateChannelName(raidInfo)
