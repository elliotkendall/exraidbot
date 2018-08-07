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
        date = raidInfo.day + '-' + str(list(calendar.month_name).index(raidInfo.month))
        return 'ex_raids_' + date

    @staticmethod
    def generateChannelName(raidInfo, useCityName=False):
        commonLocations = ['Starbucks', 'Find shiny deals at Sprint']

        date = raidInfo.day + '-' + str(list(calendar.month_name).index(raidInfo.month))

        city = ''
        # It's okay not to have city info if we're not going to use it anyway
        try:
            for i in raidInfo.city.lower().split():
                city += i[0]
            if len(city) == 1:
                city = raidInfo.city.lower()
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
            channel = date + '_ex_' + city + '_' + location
        else:
            channel = date + '_ex_' + location
        return channel
