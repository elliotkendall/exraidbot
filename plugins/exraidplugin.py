#!/usr/bin/python
from disco.bot import Bot, Plugin, Config
from disco.types.permissions import PermissionValue, Permissions
from disco.types.channel import PermissionOverwriteType, PermissionOverwrite

import cv2
import datetime
import re
import dateutil.parser
import traceback
import os
from fuzzywuzzy import fuzz
from string import Template

import pokeocr
from pokediscord import pokediscord
from cv2utils import cv2utils

class ExRaidPluginConfig(Config):
  def loadDefaults(self, config):
    name = self.__module__.lower()
    if name.endswith('plugin'):
      name = name[:-6]
    if name.startswith('plugins.'):
      name = name[8:]
    file = os.path.join(config.plugin_config_dir, name) + '.default.' + config.plugin_config_format
    try:
      defaults = self.from_file(file)
    except IOError:
      # File doesn't exist
      return
    for key, value in defaults.__dict__.iteritems():
      if not key in self.__dict__:
        self.key = value

@Plugin.with_config(ExRaidPluginConfig)
class ExRaidPlugin(Plugin):
  def load(self, ctx):
    super(ExRaidPlugin, self).load(ctx)
    self.config.loadDefaults(self.bot.config)
    self.topleft = cv2.imread(self.config.top_left_image)
    self.bottom = cv2.imread(self.config.bottom_image)
    self.ocr = pokeocr.pokeocr(self.config.location_regular_expression)
    self.exChannelRE = re.compile('^([0-9]{1,2})-([0-9]{1,2})_ex_')

  @staticmethod
  def getChannelByName(cname, channels):
    for channel in channels.values():
      if channel.name == cname:
        return channel
    return None

  # Returns the closest matching channel name
  @staticmethod
  def getChannelByNameFuzzy(cname, channels):
    has_ts_re = re.compile('_([0-9]{4})$')

    match = has_ts_re.search(cname)
    if match:
      ts = match.group(1)
    else:
      ts = 0

    best = None
    bscore = None
    for channel in channels.values():
      score = fuzz.ratio(channel.name, cname)
      match = has_ts_re.search(channel.name)
      if match:
        thists = match.group(1)
      else:
        thists = 0

      if (bscore is None or score > bscore) and ts == thists:
        best = channel
        bscore = score

    return (best, bscore)

  @classmethod
  def getEveryoneRole(cls, guild):
    return cls.getRoleByName('@everyone', guild)

  @staticmethod
  def getRoleByName(name, guild):
    for id, role in guild.roles.iteritems():
      if role.name == name:
        return role
    return None

  @staticmethod
  def dateDiff(datestring):
    begin = dateutil.parser.parse(datestring)
    now = datetime.datetime.today()
    # There's no year in raid invite images, so we have to handle
    # year-end wrapping manually
    if now.month == 12 and begin.month == 1:
      begin = dateutil.parser.parse(datestring + ' ' + str(now.year + 1))
    elif now.month == 1 and begin.month == 12:
      begin = dateutil.parser.parse(datestring + ' ' + str(now.year - 1))

    return begin - now

  def purgeOldChannels(self, channels):
    if self.config.old_channel_grace_days == -1:
      return None
    for channel in channels.values():
      date = pokediscord.channelNameToDate(channel.name)
      if not date:
        continue
      if self.dateDiff(date).days < -self.config.old_channel_grace_days:
        channel.delete()

  @staticmethod
  def alphabetizeChannels(category, channels):
    subchannels = {}
    for channel in channels.values():
      if channel.parent is None:
        continue
      if channel.parent.name == category.name:
        subchannels[channel.name] = channel

    pos = 0
    for name, channel in sorted(subchannels.iteritems()):
      channel.set_position(pos)
      pos += 1

  @staticmethod
  def userInChannel(user, channel):
    for snowflake, overwrite in channel.overwrites.iteritems():
      if overwrite.type == PermissionOverwriteType.MEMBER and overwrite.id == user.id:
        return True
    return False

  @staticmethod
  def atReply(message, text, author=None):
    if author is None:
      author=message.author
    message.reply('<@' + str(author.id) + '> ' + text)

  @Plugin.listen('MessageReactionAdd')
  def on_reaction_add(self, event):
    if not '#' + event.channel.name in self.config.channels_to_watch:
      return None

    message = event.channel.get_message(event.message_id)
    if len(message.attachments) < 1:
      return None

    user = event.client.state.users.get(event.user_id)
    member = event.guild.get_member(user)

    allowed = False
    for roleid in member.roles:
      role = event.guild.roles[roleid]
      if role.name in self.config.roles_who_can_reprocess_messages:
        allowed = True
    if not allowed and message.author.id != event.user_id:
      self.atReply(message, self.config.messages['not_allowed_to_reprocess'], user)
      return None

    self.process_message(event, message)

  @Plugin.listen('MessageCreate')
  def on_message_create(self, event):
    if not '#' + event.channel.name in self.config.channels_to_watch:
      return None
    self.process_message(event)

  def process_message(self, event, message=None):
    if message is None:
      message = event.message
    for key, value in message.attachments.iteritems():
      # Get the info from the image
      try:
        image = cv2utils.urlToImage(value.url)
        raidInfo = self.ocr.scanExRaidImage(image, self.topleft, self.bottom, useCity=self.config.include_city_in_channel_names, allowOngoing=self.config.allow_ongoing_raids)
        try:
          if raidInfo.city not in self.config.allowed_cities and len(self.config.allowed_cities) > 0:
            self.atReply(message, self.config.messages['city_not_allowed'] + ', '.join(self.config.allowed_cities))
            continue
        except AttributeError:
          # We'll assume no city is okay
          pass
        if self.dateDiff(raidInfo.month + '-' + raidInfo.day + ' ' + raidInfo.begin).days < 0:
          self.atReply(message, self.config.messages['date_in_past'])
          continue
        cname = pokediscord.generateChannelName(raidInfo, self.config.common_locations, self.config.include_city_in_channel_names)
        try:
          catname = self.config.channel_category
        except AttributeError:
          catname = pokediscord.generateCategoryName(raidInfo, self.config.include_city_in_category_names)
      except pokeocr.MatchNotCenteredException:
        traceback.print_exc()
        self.atReply(message, self.config.messages['match_not_centered'])
        continue
      except pokeocr.TooFewLinesException:
        traceback.print_exc()
        self.atReply(message, self.config.messages['too_few_lines'])
        continue
      except pokeocr.InvalidCityException:
        traceback.print_exc()
        self.atReply(message, self.config.messages['invalid_city'])
        continue
      except pokeocr.DisallowedOngoingRaidException:
        traceback.print_exc()
        self.atReply(message, self.config.messages['ongoing_raids_not_allowed'])
        continue
      except Exception:
        traceback.print_exc()
        self.atReply(message, self.config.messages['could_not_parse'])
        continue

      # Create the category if it doesn't exist
      category = self.getChannelByName(catname, event.guild.channels)
      if not category:
        category = event.guild.create_category(catname)

      # Create the channel if it doesn't exist
      channel = self.getChannelByName(cname, event.guild.channels)
      if not channel:
        try:
          overwrites = []
          for rname in self.config.roles_for_new_channels:
            role = self.getRoleByName(rname, event.guild)
            if role is None:
              print 'Warning: role ' + rname + ' does not exist'
              continue
            overwrites.append(PermissionOverwrite(
             id = role.id,
             type = PermissionOverwriteType.ROLE,
             allow = PermissionValue(Permissions.READ_MESSAGES)))

          everyone = self.getEveryoneRole(event.guild)
          overwrites.append(PermissionOverwrite(
           id = everyone.id,
           type = PermissionOverwriteType.ROLE,
           deny = PermissionValue(Permissions.READ_MESSAGES)))
          channel = category.create_text_channel(cname, permission_overwrites=overwrites)
        except Exception:
          traceback.print_exc()
          self.atReply(message, self.config.messages['channel_create_error'])
          continue

        # Post a sticky message to track who's in the channel
        raidInfoMessage = Template(self.config.messages['raid_info_channel_message'])
        uic_message_text = raidInfoMessage.substitute(
          location=raidInfo.location,
          month=raidInfo.month, day=raidInfo.day,
          begin=raidInfo.begin) + '. ' + self.config.messages['users_in_channel_message']
        uic_message = channel.send_message(uic_message_text)
        uic_message.pin()

        self.alphabetizeChannels(category, event.guild.channels)

      # Is the user already in the channel?
      if self.userInChannel(message.author, channel):
        self.atReply(message, self.config.messages['user_already_in_channel'] + ' <#' + str(channel.id) + '>')
        continue

      # Add the user to the channel
      try:
        deny=None
        if self.config.allow_at_everyone:
          channel.create_overwrite(message.author, allow=PermissionValue(Permissions.READ_MESSAGES))
        else:
          channel.create_overwrite(message.author, allow=PermissionValue(Permissions.READ_MESSAGES), deny=PermissionValue(Permissions.MENTION_EVERYONE))
        self.atReply(message, self.config.messages['added_success'] + ' <#' + str(channel.id) + '>')
        channel.send_message(self.config.messages['post_add_message'] + ' <@' + str(message.author.id) + '>')
      except Exception:
        traceback.print_exc()
        self.atReply(message, self.config.messages['channel_add_error'])
        continue

      # Add them to the pinned message
      for pin in channel.get_pins():
        if self.config.messages['users_in_channel_message'] in pin.content:
          pin.edit(pin.content + ' <@' + str(message.author.id) + '>')

      # Purge old channels
      self.purgeOldChannels(event.guild.channels)
