#!/usr/bin/python
from disco.bot import Bot, Plugin, Config
from disco.types.permissions import PermissionValue, Permissions
from disco.types.channel import PermissionOverwriteType


import cv2
import datetime
import re
import dateutil.parser
import traceback
from fuzzywuzzy import fuzz

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
    def userInChannel(user, chan_role):
        for roles in user.roles:
            print(roles)
            print(chan_role.id)
            if roles == chan_role.id:
                return True
        return False

    @staticmethod
    def atReply(message, text, author=None):
        if author is None:
            author = message.author
        message.reply('<@' + str(author.id) + '> ' + text)

    @Plugin.listen('MessageReactionAdd')
    def on_reaction_add(self, event):
        if not str(event.channel) in self.config.channels_to_watch:
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
        if not str(event.channel) in self.config.channels_to_watch:
            return None
        self.process_message(event)

    def process_message(self, event, message=None):
        if message is None:
            message = event.message
        for key, value in message.attachments.iteritems():
            # Get the info from the image
            try:
                image = cv2utils.urlToImage(value.url)
                raidInfo = self.ocr.scanExRaidImage(image, self.top, self.bottom, useCity=self.config.include_city_in_channel_names)
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
                cname = pokediscord.generateChannelName(raidInfo, self.config.include_city_in_channel_names)
                try:
                    catname = self.config.channel_category
                except AttributeError:
                    catname = pokediscord.generateCategoryName(raidInfo)
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
            new_role = pokediscord.generateRoleName(raidInfo)
            if not channel:
                try:
                    channel = category.create_text_channel(cname)
                    everyone = self.getEveryoneRole(event.guild)
                    channel.create_overwrite(everyone, deny=PermissionValue(Permissions.READ_MESSAGES))
                    for rname in self.config.roles_for_new_channels:
                        modrole = self.getRoleByName(rname, event.guild)
                        channel.create_overwrite(modrole, allow=PermissionValue(Permissions.READ_MESSAGES))
                except Exception:
                    traceback.print_exc()
                    self.atReply(message, self.config.messages['channel_create_error'])
                    continue

            # Create the role if it doesn't exist
            if not self.getRoleByName(new_role, event.guild):
                try:
                    event.guild.create_role(name=new_role)
                    role = self.getRoleByName(new_role, event.guild)
                    channel.create_overwrite(role, allow=PermissionValue(Permissions.READ_MESSAGES))
                    print("made a new role")
                except Exception:
                    traceback.print_exc()
                    self.atReply(message, self.config.messages['channel_create_error'])
                    continue

                self.alphabetizeChannels(category, event.guild.channels)

            # Is the user already in the channel?
            chan_role = self.getRoleByName(new_role, event.guild)
            user = event.client.state.users.get(event.user_id)
            member = event.guild.get_member(user)
            if self.userInChannel(member, chan_role):
                self.atReply(message, self.config.messages['user_already_in_channel'])
                continue

            # Add the user to the channel
            try:
                user = event.guild.get_member(message.author)
                role = self.getRoleByName(new_role, event.guild)
                user.add_role(role)
                self.atReply(message, self.config.messages['added_success'] + ' <#' + str(channel.id) + '>')
                channel.send_message(self.config.messages['post_add_message'] + ' <@' + str(message.author.id) + '>')
            except Exception:
                traceback.print_exc()
                self.atReply(message, self.config.messages['channel_add_error'])
                continue

            # Purge old channels
            self.purgeOldChannels(event.guild.channels)
