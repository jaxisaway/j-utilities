# run the josh
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import config
import db
import gif_roles
import assignable_roles
import starboards_config
import souls_config
import word_tracker_config
import birthdays
import commands.commands_birthdays
import commands.commands_starboard
import commands.commands_gif
import commands.commands_roles
import commands.commands_mod
import commands.commands_help
import commands.commands_souls
import commands.commands_tracker
import events

# use your josh here
config.bot.run('tooooooken here')
