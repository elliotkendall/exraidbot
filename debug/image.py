#!/usr/bin/python
import cv2
import sys
import json
import argparse

from os.path import dirname
sys.path.append(dirname(dirname(__file__)))

from cv2utils import cv2utils
from pokeocr import pokeocr

parser = argparse.ArgumentParser(description='Parse an EX raid image (high level)')
parser.add_argument('-f', dest='configfile', default='config/exraid.json')
parser.add_argument('-o', dest='outfile')
parser.add_argument('image')
args = parser.parse_args()

f = open(args.configfile)
config = json.load(f)
f.close()

topleft = cv2.imread(config['top_left_image'])
bottom = cv2.imread(config['bottom_image'])
image = cv2.imread(args.image)

ocr = pokeocr(config['location_regular_expression'])

image = ocr.cropExRaidImage(image, topleft, bottom, True)

if args.outfile:
  cv2.imwrite(args.outfile, image)
else:
  cv2.imshow("Image", image)
  cv2.waitKey(0)
