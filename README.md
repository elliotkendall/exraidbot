# exraidbot

Exraidbot is a Discord bot that processes Pokemon Go EX Raid invitation
images.  When a user posts an invitation image in a specified channel, the
bot will create a channel for the given raid time/location and add the user
to that channel.  After a specified grace period, the bot will delete old
channels next time it runs.

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

- **roles_for_new_channels**: A list of the names of role that you want
  assigned to any new channels the bot creates.  If your server has admin or
  moderator roles, you might want to list them here to that people can
  manually tweak the channels.

- **location_regular_expression**: A regular expression to match the
  location line in invites in your area.  For US states other than
  California, you should just change "(CA|California)" as appropriate for
  your state, such as "(FL|Florida)".

- **old_channel_grace_days**: How many days after a raid is over that its
  channel should stick around. Set this to -1 to disable expiration.

- **messages**: The messages that the bot will respond with in various
  situations.

- **top_image** / **bottom_image**: The names of images to use for analysis
  of the invite images. You shouldn't need to edit these.

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
