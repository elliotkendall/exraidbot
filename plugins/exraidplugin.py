#!/usr/bin/python
from disco.bot import Bot, Plugin, Config
from disco.types.permissions import PermissionValue, Permissions

import cv2
import datetime
import re
import dateutil.parser

from pokeocr import pokeocr
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
    self.ocr = pokeocr()
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
    for channel in channels.values():
      date = pokediscord.channelNameToDate(channel.name)
      if not date:
        continue
      if self.dateDiff(date).days < -self.config.old_channel_grace_days:
        channel.delete()

  @Plugin.listen('MessageCreate')
  def on_message_create(self, event):
    if str(event.channel) in self.config.channels_to_watch:
      for key, value in event.message.attachments.iteritems():
        # Get the info from the image
        try:
          image = cv2utils.urlToImage(value.url)
          raidInfo = self.ocr.scanExRaidImage(image, self.top, self.bottom)
          if self.dateDiff(raidInfo.month + '-' + raidInfo.day + ' ' + raidInfo.begin).days < 0:
            event.reply(self.config.messages['date_in_past'])
            continue          
          cname = pokediscord.generateChannelName(raidInfo)
          catname = pokediscord.generateCategoryName(raidInfo)
        except Exception:
          event.reply(self.config.messages['could_not_parse'])
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
            event.reply(self.config.messages['channel_create_error'])
            continue

        # Add the user to the channel
        try:
          channel.create_overwrite(event.message.author, allow=PermissionValue(Permissions.READ_MESSAGES))
          event.reply('Added ' + event.message.author.username + ' to channel #' + cname)
        except Exception:
          event.reply(self.config.messages['channel_add_error'])
          continue

        # Purge old channels
        self.purgeOldChannels(event.guild.channels)
