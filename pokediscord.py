import calendar
import datetime
import dateutil.parser
import re
import pokeocr

class pokediscord:
  @staticmethod
  def parseChannelName(cname):
    # 5-28_ex_sf_mission_creek_park
    exChannelRE = re.compile('^([0-9]{1,2})-([0-9]{1,2})_ex_([a-z]+)_(.*)')
    match = exChannelRE.match(cname)
    if match:
      ret = pokeocr.exRaidData()
      ret.month = match.group(1)
      ret.day = match.group(2)
      ret.city = match.group(3)
      ret.location = match.group(4)
      ret.begin = '9:00 AM'
      ret.end = '9:45 AM'
      return ret
    return None

  @staticmethod
  def generateCategoryName(raidInfo):
    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day
    return 'ex_raids_' + date

  @staticmethod
  def generateChannelName(raidInfo):
    commonLocations = ['Starbucks', 'Find shiny deals at Sprint']

    date = str(list(calendar.month_name).index(raidInfo.month)) + '-' + raidInfo.day
    city = ''
    for i in raidInfo.city.lower().split():
      city += i[0]
    if len(city) == 1:
      city = raidInfo.city.lower()
    location = raidInfo.location.lower().replace(' ', '_')
    if raidInfo.location in commonLocations:
      begin = datetime.datetime.strptime(raidInfo.begin, '%I:%M %p')
      location += '_' + datetime.datetime.strftime(begin, "%H:%M")
    channel =  date + '_ex_' + city + '_' + location
    return channel

  @staticmethod
  def dateDiff(raidInfo):
    begin = dateutil.parser.parse(raidInfo.month + ' ' + raidInfo.day + ' ' + raidInfo.begin)
    now = datetime.datetime.today()
    return begin - now
