# This Python file uses the following encoding: utf-8
from PIL import Image
import pyocr
import pyocr.builders
import cv2
import sys
import re
import unicodedata
import time
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

class DisallowedOngoingRaidException(Exception):
  pass

class pokeocr:
  def __init__(self, location_regex):
    self.tool = pyocr.get_available_tools()[0]
    self.lang = self.tool.get_available_languages()[0]
    self.dateTimeRE = re.compile('^([A-Z][a-z]+) ?([0-9]{1,2}) ([0-9]{1,2}:[0-9]{2} ?[AP]M) .+ ([0-9]{1,2}:[0-9]{2} ?[AP]M)')
    self.ongoingTimeRE = re.compile('^Ongoing ([0-9]{1,2}:[0-9]{2} ?[AP]M) .+ ([0-9]{1,2}:[0-9]{2} ?[AP]M)')
    self.cityRE = re.compile(location_regex)
    self.getDirectionsRE = re.compile('Get.*ns')

  @staticmethod
  def isMatchCentered(width, startx, endx):
    matchw = endx - startx
    offset = (width - matchw) / 2
    diff = abs(offset - startx)

    # We want to return True/False, but we need to know the correct offset
    # if it's False. There's probably a better way to do this...
    if diff > (width * .04):
      return offset
    else:
      return True

  def cropExRaidImage(self, image, topleft, bottom, debug=False):
    height, width = image.shape[:2]

    # Run the scaling matcher to find the template, then sanity check the
    # match
    ((tl_left, tl_top), (tl_right, tl_bottom)) = cv2utils.scalingMatch(topleft, image)
    ((b_left, b_top), (b_right, b_bottom)) = cv2utils.scalingMatch(bottom, image)
    if not debug:
      val = self.isMatchCentered(width, b_left, b_right)
      if val != True:
        raise MatchNotCenteredException('Bottom template match not centered. Starts at ' + str(b_left) + ', should be ' + str(val))

    # Seek left from bottom left of top left match until we hit non-white
    # pixels
    for i in range(tl_left, 0, -1):
      pixel = image[tl_bottom,i]
      sum = int(pixel[0]) + int(pixel[1]) + int(pixel[2])
      if sum < 759:
        break
    newleft = i

    # Let's assume that the right offset is the same as the left. We could
    # match on a top-right image, but it would tank performance even more.
    right = width - newleft

    # Crop the image
    return image[tl_bottom:b_top,newleft:right]
  
  def scanExRaidImage(self, image, topleft, bottom, useCity=True, allowOngoing=True, debug=False):
    image = self.cropExRaidImage(image, topleft, bottom)

    # Scale up, which oddly helps with OCR
    height, width = image.shape[:2]
    image = cv2.resize(image, (0,0), fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # Increase contrast. Must be done before grayscale conversion
    image = cv2utils.increaseContrast(image)

    # Convert to grayscale
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Convert to PIL format
    pil = Image.fromarray(image)

    # OCR the text
    txt = self.tool.image_to_string(pil, lang=self.lang, builder=pyocr.builders.TextBuilder())

    # Replace any non-ASCII unicode characters with their closest
    # equivalents.  This is bad news for i18n, but helps us with a lot of
    # OCR issues
    txt = unicodedata.normalize('NFKD', txt)

    lines = txt.split("\n")

    # Sometimes OCR will insert extra empty lines, so let's strip them out
    newlines = []
    for i in range(len(lines)):
      if not len(lines[i].strip()) == 0:
        newlines.append(lines[i])
    lines = newlines

    if debug:
      return lines

    # If we're not going to use the city info anyway, we can process images
    # that are missing it
    if useCity:
      minlines = 4
    else:
      minlines = 3

    if len(lines) < minlines:
      raise TooFewLinesException('Found fewer lines of text than expected')

    ret = exRaidData()

    # A common issue is reading lowercase L as pipe. There should never be
    # pipes in this data, so let's just replace them.  We'll do this before
    # even trying a match because it's very low-risk
    lines[0] = lines[0].replace('|', 'l')

    match = self.dateTimeRE.match(lines[0])

    if not match:
      # Let's try to work around some common problems

      # "[Month] 5" gets read as "[Month] S".  This should be safe because
      # "S " and " S" shouldn't appear in legitimate date/time
      lines[0] = lines[0].replace('S ', '5 ', 1)
      lines[0] = lines[0].replace(' S', ' 5', 1)

      # Sometimes spaces get dropped. There's no reason a letter and number
      # should appear immediately next to each other in a date line
      lines[0] = re.sub('([0-9])([a-zA-Z])', r'\1 \2', lines[0])
      lines[0] = re.sub('([a-zA-Z])([0-9])', r'\1 \2', lines[0])

      match = self.dateTimeRE.match(lines[0])

    # Maybe it's an ongoing raid
    if not match:
      match = self.ongoingTimeRE.match(lines[0])
      if match and not allowOngoing:
        raise DisallowedOngoingRaidException('This invitation is for an ongoing raid')

    # Sometimes we get a leading jibberish line
    if not match:
      del lines[0]
      match = self.dateTimeRE.match(lines[0])

    if match:
      if len(match.groups()) == 4:
        # This is a normal invitation with all four fields
        ret.month = match.group(1)
        ret.day = match.group(2)
        beginindex = 3
        endindex = 4
      else:
        # This is for an ongoing raid, so use today for month/day
        ret.month = time.strftime('%B')
        ret.day = time.strftime('%d')
        beginindex = 1
        endindex = 2

      # Sometimes OCR drops the space between the minutes and AM/PM.  Let's
      # just strip all spaces for consistency
      ret.begin = match.group(beginindex).replace(' ', '')
      ret.end = match.group(endindex).replace(' ', '')
    else:
      raise InvalidDateTimeException('Date/time line did not match: ' + lines[0].encode('utf-8'))

    ret.location = lines[1]

    gdindex = 3
    match = self.cityRE.match(lines[2])
    if match:
      ret.city = match.group(1)
    elif (not useCity) and self.getDirectionsRE.match(lines[2]):
      # When we're ignoring the city, it's okay for this line to be Get
      # Directions
      gdindex = 2
    elif useCity:
      raise InvalidCityException('City line did not match: ' + lines[2].encode('utf-8'))

    match = self.getDirectionsRE.match(lines[gdindex])
    if not match:
      raise InvalidGetDirectionsException('Get directions did not match: ' + lines[gdindex].encode('utf-8'))

    return ret

class exRaidData:
  def __init__(self, **kwargs):
    self.__dict__.update(kwargs)
