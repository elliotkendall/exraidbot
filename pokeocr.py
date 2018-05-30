# This Python file uses the following encoding: utf-8
from PIL import Image
import pyocr
import pyocr.builders
import cv2
import sys
import re
from cv2utils import cv2utils

class pokeocr:
  def __init__(self):
    self.tool = pyocr.get_available_tools()[0]
    self.lang = self.tool.get_available_languages()[0]
    self.dateTimeRE = re.compile('^([A-Z][a-z]+) ?([0-9]{1,2}) ([0-9]{1,2}:[0-9]{2} [AP]M) .+ ([0-9]{1,2}:[0-9]{2} [AP]M)$')
    self.cityRE = re.compile('(.*)[,.‘] (CA|California). United States')

  @staticmethod
  def isMatchCentered(width, startx, endx):
    matchw = endx - startx
    offset = (width - matchw) / 2
    diff = abs(offset - startx)

    # We want to return True/False, but we need to know the correct offset
    # if it's False. There's probably a better way to do this...
    if diff < (width * .01):
      return offset
    else:
      return True
  
  def scanExRaidImage(self, image, top, bottom):
    # Find the source image dimensions
    height, width, channels = image.shape

    # Run the scaling matcher to find the template, then sanity check the
    # match
    ((b_startX, b_startY), (b_endX, b_endY)) = cv2utils.scalingMatch(top, image)
    val = self.isMatchCentered(width, b_startX, b_startY)
    if val != True:
      raise Exception('Top template match not centered. Starts at ' + str(b_startX) + ', should be ' + str(val))
    ((t_startX, t_startY), (t_endX, t_endY)) = cv2utils.scalingMatch(bottom, image)
    val = self.isMatchCentered(width, t_startX, t_startY)
    if val != True:
      raise Exception('Bottom template match not centered. Starts at ' + str(t_startX) + ', should be ' + str(val))

    # Crop the image
    image = image[b_endY:t_startY,b_startX:b_endX]

    # Convert to grayscale
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Convert to PIL format
    pil = Image.fromarray(image)

    # OCR the text
    txt = self.tool.image_to_string(pil, lang=self.lang, builder=pyocr.builders.TextBuilder())
    lines = txt.split("\n")
    ret = exRaidData()

    match = self.dateTimeRE.match(lines[0])
    if match:
      ret.month = match.group(1)
      ret.day = match.group(2)
      ret.begin = match.group(3)
      ret.end = match.group(4)
    else:
      raise Exception('Date/time line did not match: ' + lines[0].encode('utf-8'))

    ret.location = lines[1]

    match = self.cityRE.match(lines[2])
    if match:
      ret.city = match.group(1)
    else:
      raise Exception('City line did not match: ' + lines[2].encode('utf-8'))

    if lines[3] != 'Get directions':
      raise Exception('Get directions did not match: ' + lines[3].encode('utf-8'))

    return ret

class exRaidData:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
