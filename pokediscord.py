import calendar
import datetime
import re
import pokeocr

class pokediscord:
  @staticmethod
  def channelNameToDate(cname):
    # 5-28_ex_sf_mission_creek_park
    exChannelRE = re.compile('^([0-9]{1,2}-[0-9]{1,2})_ex_')
    match = exChannelRE.match(cname)
    if match:
      return match.group(1)
    # ex_raids_5-28
    exCategoryRE = re.compile('^ex_raids_([0-9]{1,2}-[0-9]{1,2})')
    match = exCategoryRE.match(cname)
    if match:
      return match.group(1)
    return None

  @classmethod
  def generateCategoryName(cls, raidInfo, useCity = False):
    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day
    if useCity:
      return 'ex_raids_' + date + '_' + cls.cityToShortVersion(raidInfo.city)
    else:
      return 'ex_raids_' + date

  @staticmethod
  def cityToShortVersion(cname):
    city = ''
    # Take the first letter of each word
    for i in cname.lower().split():
      city += i[0]
    # Or if there was only one word, use the whole thing
    if len(city) == 1:
      city = cname.lower()
    return city

  @classmethod
  def generateChannelName(cls, raidInfo, commonLocations, useCityName = True):
    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day

    city = ''
    # It's okay not to have city info if we're not going to use it anyway
    try:
      city = cls.cityToShortVersion(raidInfo.city)
    except AttributeError, e:
      if useCityName:
        raise e

    location = raidInfo.location.lower().replace(' ', '_')
    location = re.sub('[^a-z0-9_]', '', location)
    location = location.strip('_')
    if raidInfo.location in commonLocations:
      begin = datetime.datetime.strptime(raidInfo.begin, '%I:%M%p')
      location += '_' + datetime.datetime.strftime(begin, "%H%M")
    if useCityName and city != '':
      channel =  date + '_ex_' + city + '_' + location
    else:
      channel =  date + '_ex_' + location
    return channel
