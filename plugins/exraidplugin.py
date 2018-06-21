#!/usr/bin/python
from disco.bot import Bot, Plugin, Config
from disco.types.permissions import PermissionValue, Permissions
from disco.types.channel import PermissionOverwriteType

import cv2
import datetime
import re
import dateutil.parser
import traceback

import pokeocr
from pokediscord import pokediscord
from cv2utils import cv2utils

class ExRaidPluginConfig(Config):
  pass

@Plugin.with_config(ExRaidPluginConfig)
class ExRaidPlugin(Plugin):
  def load(self, ctx):
    super(ExRaidPlugin, self).load(ctx)
    self.top = cv2.imread(self.config.top_image)
    self.bottom = cv2.imread(self.config.bottom_image)
    self.ocr = pokeocr.pokeocr(self.config.location_regular_expression)
    self.exChannelRE = re.compile('^([0-9]{1,2})-([0-9]{1,2})_ex_')

  @staticmethod
  def getChannelByName(cname, channels):
    for channel in channels.values():
      if channel.name == cname:
        return channel
    return None

  @classmethod
  def getEveryoneRole(cls, guild):
    return cls.getRoleByName('@everyone', guild)

  @staticmethod
  def getRoleByName(name, guild):
    for id, role in guild.roles.iteritems():
      if str(role) == name:
        return role
    return None

  @staticmethod
  def dateDiff(datestring):
    begin = dateutil.parser.parse(datestring)
    now = datetime.datetime.today()
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
  def atReply(event, text):
    event.reply('<@' + str(event.message.author.id) + '> ' + text)

  @Plugin.listen('MessageCreate')
  def on_message_create(self, event):
    if not str(event.channel) in self.config.channels_to_watch:
      return None

    for key, value in event.message.attachments.iteritems():
      # Get the info from the image
      try:
        image = cv2utils.urlToImage(value.url)
        raidInfo = self.ocr.scanExRaidImage(image, self.top, self.bottom)
        if self.dateDiff(raidInfo.month + '-' + raidInfo.day + ' ' + raidInfo.begin).days < 0:
          self.atReply(event, self.config.messages['date_in_past'])
          continue
        cname = pokediscord.generateChannelName(raidInfo, self.config.include_city_in_channel_names)
        catname = pokediscord.generateCategoryName(raidInfo)
      except pokeocr.MatchNotCenteredException:
        traceback.print_exc()
        self.atReply(event, self.config.messages['match_not_centered'])
        continue
      except pokeocr.TooFewLinesException:
        traceback.print_exc()
        self.atReply(event, self.config.messages['too_few_lines'])
        continue
      except pokeocr.InvalidCityException:
        traceback.print_exc()
        self.atReply(event, self.config.messages['invalid_city'])
        continue
      except Exception:
        traceback.print_exc()
        self.atReply(event, self.config.messages['could_not_parse'])
        continue

      # Create the category if it doesn't exist
      category = self.getChannelByName(catname, event.guild.channels)
      if not category:
        category = event.guild.create_category(catname)

      # Create the channel if it doesn't exist
      channel = self.getChannelByName(cname, event.guild.channels)
      if not channel:
        try:
          channel = category.create_text_channel(cname)
          everyone = self.getEveryoneRole(event.guild)
          channel.create_overwrite(everyone, deny=PermissionValue(Permissions.READ_MESSAGES))
          for rname in self.config.roles_for_new_channels:
            role = self.getRoleByName(rname, event.guild)
            channel.create_overwrite(role, allow=PermissionValue(Permissions.READ_MESSAGES))
        except Exception:
          traceback.print_exc()
          self.atReply(event, self.config.messages['channel_create_error'])
          continue

        self.alphabetizeChannels(category, event.guild.channels)

      # Is the user already in the channel?
      if self.userInChannel(event.message.author, channel):
        self.atReply(event, self.config.messages['user_already_in_channel'])
        continue

      # Add the user to the channel
      try:
        channel.create_overwrite(event.message.author, allow=PermissionValue(Permissions.READ_MESSAGES))
        self.atReply(event, self.config.messages['added_success'] + ' <#' + str(channel.id) + '>')
        channel.send_message(self.config.messages['post_add_message'] + ' <@' + str(event.message.author.id) + '>')
      except Exception:
        traceback.print_exc()
        self.atReply(event, self.config.messages['channel_add_error'])
        continue

      # Purge old channels
      self.purgeOldChannels(event.guild.channels)
