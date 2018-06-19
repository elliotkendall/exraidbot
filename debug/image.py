#!/usr/bin/python
import cv2
import sys
from cv2utils import cv2utils

f = open('config/exraid.json')
config = json.load(f)
f.close()

top = cv2.imread(config['top_image'])
bottom = cv2.imread(config['bottom_image'])
image = cv2.imread(sys.argv[1])

((b_startX, b_startY), (b_endX, b_endY)) = cv2utils.scalingMatch(top, image)
((t_startX, t_startY), (t_endX, t_endY)) = cv2utils.scalingMatch(bottom, image)

image = image[b_endY:t_startY,b_startX:b_endX]

cv2.imshow("Image", image)
cv2.waitKey(0)
