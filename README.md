# exraidbot

Exraidbot is a Discord bot that processes Pokemon Go EX Raid invitation
images.  When a user posts an invitation image in a specified channel, the
bot will create a channel for the given raid time/location and add the user
to that channel.  After a specified grace period, the bot will delete old
channels next time it runs.

## Requirements

Make sure you have the necessary Python modules.  You can fetch them all
with pip:

`pip install opencv-python-headless numpy imutils python-dateutil pyocr disco-py`

You will also need libtesseract with English OCR support.  On a Debian-like
distribution, you can get those with:

`apt install libtesseract3 tesseract-ocr-eng`

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

- **old_channel_grace_days**: How many days after a raid is over that its
  channel should stick around

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
