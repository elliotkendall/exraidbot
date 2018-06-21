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

  @staticmethod
  def generateCategoryName(raidInfo):
    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day
    return 'ex_raids_' + date

  @staticmethod
  def generateChannelName(raidInfo, useCityName = True):
    commonLocations = ['Starbucks', 'Find shiny deals at Sprint']

    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day

    city = ''
    for i in raidInfo.city.lower().split():
      city += i[0]
    if len(city) == 1:
      city = raidInfo.city.lower()

    location = raidInfo.location.lower().replace(' ', '_')
    location = re.sub('[^a-z0-9]', '', location)
    if raidInfo.location in commonLocations:
      begin = datetime.datetime.strptime(raidInfo.begin, '%I:%M %p')
      location += '_' + datetime.datetime.strftime(begin, "%H%M")
    if useCityName:
      channel =  date + '_ex_' + city + '_' + location
    else:
      channel =  date + '_ex_' + location
    return channel
