# This Python file uses the following encoding: utf-8
from PIL import Image
import pyocr
import pyocr.builders
import cv2
import sys
import re
from cv2utils import cv2utils

class InvalidCityException(Exception):
  pass

class InvalidDateTimeException(Exception):
  pass

class InvalidGetDirectionsException(Exception):
  pass

class MatchNotCenteredException(Exception):
  pass

class TooFewLinesException(Exception):
  pass

class pokeocr:
  def __init__(self, location_regex):
    self.tool = pyocr.get_available_tools()[0]
    self.lang = self.tool.get_available_languages()[0]
    self.dateTimeRE = re.compile('^([A-Z][a-z]+) ?([0-9]{1,2}) ([0-9]{1,2}:[0-9]{2} ?[AP]M) .+ ([0-9]{1,2}:[0-9]{2} ?[AP]M)')
    self.cityRE = re.compile(location_regex)
    self.getDirectionsRE = re.compile('Get d[il]rect[il]ons')

  @staticmethod
  def isMatchCentered(width, startx, endx):
    matchw = endx - startx
    offset = (width - matchw) / 2
    diff = abs(offset - startx)

    # We want to return True/False, but we need to know the correct offset
    # if it's False. There's probably a better way to do this...
    if diff > (width * .015):
      return offset
    else:
      return True
  
  def scanExRaidImage(self, image, top, bottom):
    # Find the source image dimensions
    height, width, channels = image.shape

    # Run the scaling matcher to find the template, then sanity check the
    # match
    ((b_startX, b_startY), (b_endX, b_endY)) = cv2utils.scalingMatch(top, image)
    val = self.isMatchCentered(width, b_startX, b_endX)
    if val != True:
      raise MatchNotCenteredException('Top template match not centered. Starts at ' + str(b_startX) + ', should be ' + str(val))
    ((t_startX, t_startY), (t_endX, t_endY)) = cv2utils.scalingMatch(bottom, image)
    val = self.isMatchCentered(width, t_startX, t_endX)
    if val != True:
      raise MatchNotCenteredException('Bottom template match not centered. Starts at ' + str(t_startX) + ', should be ' + str(val))

    # Crop the image
    image = image[b_endY:t_startY,b_startX:b_endX]

    # Scale up small images
    height, width = image.shape[:2]
    if width < 509:
      image = cv2.resize(image, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # Increase contrast. Must be done before grayscale conversion
    image = cv2utils.increaseContrast(image)

    # Convert to grayscale
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Convert to PIL format
    pil = Image.fromarray(image)

    # OCR the text
    txt = self.tool.image_to_string(pil, lang=self.lang, builder=pyocr.builders.TextBuilder())
    lines = txt.split("\n")
    if len(lines) < 4:
      raise TooFewLinesException('Found fewer lines of text than expected')

    ret = exRaidData()

    match = self.dateTimeRE.match(lines[0])
    if match:
      ret.month = match.group(1)
      ret.day = match.group(2)
      ret.begin = match.group(3)
      ret.end = match.group(4)
    else:
      raise InvalidDateTimeException('Date/time line did not match: ' + lines[0].encode('utf-8'))

    ret.location = lines[1]

    match = self.cityRE.match(lines[2])
    if match:
      ret.city = match.group(1)
    else:
      raise InvalidCityException('City line did not match: ' + lines[2].encode('utf-8'))

    match = self.getDirectionsRE.match(lines[3])
    if not match:
      raise InvalidGetDirectionsException('Get directions did not match: ' + lines[3].encode('utf-8'))

    return ret

class exRaidData:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
