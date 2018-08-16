#!/usr/bin/python
import cv2
import sys
import json
import argparse

from os.path import dirname
sys.path.append(dirname(dirname(__file__)))

from cv2utils import cv2utils

parser = argparse.ArgumentParser(description='Parse an EX raid image (high level)')
parser.add_argument('-f', dest='configfile', default='config/exraid.json')
parser.add_argument('-o', dest='outfile')
parser.add_argument('image')
args = parser.parse_args()

f = open(args.configfile)
config = json.load(f)
f.close()

top = cv2.imread(config['top_image'])
bottom = cv2.imread(config['bottom_image'])
image = cv2.imread(args.image)

((b_startX, b_startY), (b_endX, b_endY)) = cv2utils.scalingMatch(top, image)
((t_startX, t_startY), (t_endX, t_endY)) = cv2utils.scalingMatch(bottom, image)

image = image[b_endY:t_startY,b_startX:b_endX]

if args.outfile:
  cv2.imwrite(args.outfile, image)
else:
  cv2.imshow("Image", image)
  cv2.waitKey(0)
