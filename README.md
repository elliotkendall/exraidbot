# exraidbot

Exraidbot is a Discord bot that processes Pokemon Go EX Raid invitation
images.  When a user posts an invitation image in a specified channel, the
bot will create a channel for the given raid time/location and add the user
to that channel.  After a specified grace period, the bot will delete old
channels next time it runs.

## Features

- Monitors a configurable list of channels

- Creates categories by date

- Creates channels by date, location name, (optionally) city name, and (for
  non-unique locations) time of day

- Add users to channels

- Announces in the channel when a user has been newly added

- When a user reacts to a message in a monitored channel, processes the
  message as though it were just posted.  This feature is useful for going
  through a backlog of messages from when the bot was offline.  See
  **roles_who_can_reprocess_messages** under **Local Configuration**, below,
  for more information.

- Optionally deletes old channels after a configurable number of days have
  passed since the raid took place

## Installation

### Linux

Make sure you have the necessary Python modules.  You can fetch them all
with pip:

`pip install -r requirements.txt`

You will also need libtesseract with English OCR support.  On a Debian-like
distribution, you can get those with:

`apt install libtesseract3 tesseract-ocr-eng`

### Windows

Download and install the latest version of Python 2 from
https://www.python.org/downloads/.  I used the 2.7.15 x86-64 MSI installer. 
Make sure to select the "Add python.exe to Path" option.

In the exraidbot directory, run `pip install -r requirements.txt`

Download and run a tesseract installer from
https://github.com/UB-Mannheim/tesseract/wiki.  I used
tesseract-ocr-setup-3.05.01.exe.

Add the location of the tesseract.exe file to your PATH.  To do that,
right-click on your computer icon, select properties, and then select
Advanced.  Click the Environment Variables...  button.  Under System
variables, select Path and press Edit...  Select New and enter C:\\Program
Files (x86)\\Tesseract-OCR, or whatever you installed tesseract.  Press OK
to exit out of all of the configuration windows.  Re-launch any cmd or other
command line windows, and try running `tesseract`.  If everything went
correctly, you should see the tesseract command line usage help.

In my testing, I've been unable to get things working correctly with either
Cygwin or the libtesseract DLL.  If anyone else figures either of those
options out, please let me know.

### Mac OS

These instructions were developed on Mac OS 10.13 High Sierra.  They may not
work unmodified on earlier or later versions.

Install Xcode from the App Store if you don't already have it.

If you just installed Xcode, run "sudo xcodebuild -license" and agree to the
terms.

Install homebrew from https://brew.sh/ if you don't already have it.

Run "brew install tesseract"

Run "sudo easy_install pip"

Change to the directory where you've checked out the exraidbot code.

Run "pip install --user -r requirements.txt"

Run "pip install --user 'numpy>=1.11.1' six==1.11.0".  For some reason, pip
installs versions of these modules that it knows are incompatible with some
other modules.

## Discord Configuration

Create a Discord user for your bot, get an authentication token for it, and
invite it to your server.  For example, you can use the instructions at
https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token

Create a Discord role for your bot.  Right now, the bot requires
administrator permission, but I'm going to work on reducing that in the
future.

Assign your bot to the new role, and you should be ready to go.

## Local Configuration

Edit config.json and specify the authentication token you got in the
previous section.

Edit config/exraid.json and customize the settings to your liking.

- **channels_to_watch**: A list of channels where the bot will watch for
  images to be uploaded

- **roles_for_new_channels**: A list of the names of roles that you want
  assigned to any new channels the bot creates.  If your server has admin or
  moderator roles, you might want to list them here to that people can
  manually tweak the channels.

- **roles_who_can_reprocess_messages**: A list of the names of roles that
  are able to request that a message be reprocessed.  Individual users can
  always reprocess their own messages.  See **Features**, above, for more
  information.

- **fuzzy_channel_match_threshold**: How much "fuzz" to allow when looking
  for duplicate channel names, which helps with OCR errors.  For example,
  "argonne_playground" vs. "argonne_piayground" is a threshold of 99.  Set
  to 100 to disable fuzzy matching.

- **location_regular_expression**: A regular expression to match the
  location line in invites in your area.  For US states other than
  California, you should just change "(CA|California)" as appropriate for
  your state, such as "(FL|Florida)".

- **allowed_cities**: A list of cities that the bot will make channels for.
  Helpful to restrict your server to a specific area. Set to an empty list
  to allow any city.

- **old_channel_grace_days**: How many days after a raid is over that its
  channel should stick around. Set this to -1 to disable expiration.

- **include_city_in_channel_names**: Whether or not to include the name of
  the city in the names of channels we create.  If your Discord covers only
  a single city, you may wish to set this to false.

- **channel_category**: If set, the bot will place newly created channels
  in this category. If not, it will be named for the day of the raid.

- **messages**: The messages that the bot will respond with in various
  situations.

- **top_left_image** / **bottom_image**: The names of images to use for
  analysis of the invite images.  You shouldn't need to edit these.

## Running

Once you've configured everything, run the following command from the
directory with all the exraidbot files:

`python -m disco.cli --config config.json`

## Using Docker

If you prefer, you can run the bot out of a Docker container.  Edit the
local config files as described above, then build the image:

`docker build -t exraidbot .`

And run it:

`docker run exraidbot`

## Frequently Asked Questions

### When I run the bot, I see a message about "DeprecationWarning: BaseException.message has been deprecated as of Python 2.6". What does that mean?

You can safely ignore this warning.  It means that the Python tesseract
bindings are using a feature of the language that's slated to go away in the
future.

### How can I run the bot in the background?

When you launch the bot, it stays in the foreground.  If you'd like to run
it in the background, I recommend using the screen program:
https://www.howtoforge.com/linux_screen

## Debugging

I've included a few scripts to help debug problems with your python setup
and/or individual raid invitation images.

- **ocr.py**: Shows you what the optical character recognition (OCR) library
  returns for a specific image.  The output should look something like this:
  `[u'June 5 5:00 PM - 5:45 PM', u'Stern Grove Entrance', u'San Francisco. CA. United States', u'Get directions']`

- **raidinfo.py**: Shows the parsed version of the above, plus the name of
  the channel we would create.  For example:
  `{'city': u'San Francisco', 'begin': u'5:00 PM', 'end': u'5:45 PM', 'month': u'June', 'location': u'Stern Grove Entrance', 'day': u'5'}`
  `6-5_ex_sf_stern_grove_entrance`

- **image.py**: Shows a cropped version of the image including just the part
  that we would run OCR against.

## Discord Server

If you'd like to chat, you can stop by the Discord server I'm using to test
and develop the bot. Here's an invite link: https://discord.gg/2yfq5yk

## Who Uses exraidbot?

Here are some Pokemon Go Discord communities that are using exraidbot.

- **SF Pogo Raids Meetup**, San Francisco, California, USA

- **[DTC Pokemon Go](https://www.dtc.fyi/)**, Chicago, Illinois, USA

- **Fermi, Chicago Western Suburbs, Illinois, USA

- **Perth PoGo, Perth, Australia

Please let me know if your community is using exraidbot so I can add you to
this list.  Thanks.
