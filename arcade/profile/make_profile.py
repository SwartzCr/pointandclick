"""Writes "Hotel Paradiso Arcade.mobileconfig": the restrictions for the arcade's own user account
on the kiosk Mac. Install it while logged in as that user (System Preferences > Profiles).

What it does, for that user only:
  - only Hotel Paradiso Arcade (and everything inside it) may run, plus macOS's own core parts
  - no websites (and no browser to visit them in anyway)
  - the arcade opens by itself at login
  - the Dock hides itself and can't be changed
"""
import os
import plistlib
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
APP = '/Applications/Hotel Paradiso Arcade.app'
NS = uuid.UUID('6b7a3c51-913a-4f0e-8d1c-5ac7a9a50714')


def ident(name):
    return 'io.github.swartzcr.hotelparadiso.arcade.profile.' + name


def payload(kind, name, display, body):
    p = {'PayloadType': kind, 'PayloadIdentifier': ident(name), 'PayloadUUID': str(uuid.uuid5(NS, name)).upper(),
         'PayloadVersion': 1, 'PayloadDisplayName': display, 'PayloadEnabled': True}
    p.update(body)
    return p


content = [
    payload('com.apple.applicationaccess.new', 'apps', 'Only the arcade can run', {
        'familyControlsEnabled': True,
        # everything inside these folders may run; anything else is refused
        'pathWhiteList': [APP + '/', '/System/Library/CoreServices/'],
        'pathBlackList': [],
        'whiteList': [],
    }),
    payload('com.apple.familycontrols.contentfilter', 'web', 'No websites', {
        'restrictWeb': True,
        'useContentFilter': False,
        'whitelistEnabled': True,
        'siteWhitelist': [],
    }),
    payload('com.apple.loginitems.managed', 'login', 'Open the arcade at login', {
        'AutoLaunchedApplicationDictionary-managed': [{'Path': APP, 'Hide': False}],
    }),
    payload('com.apple.dock', 'dock', 'Hide the Dock', {
        'autohide': True,
        'autohide-immutable': True,
        'contents-immutable': True,
        'static-only': True,
        'static-apps': [],
        'static-others': [],
        'show-recents': False,
    }),
]

profile = {
    'PayloadType': 'Configuration',
    'PayloadVersion': 1,
    'PayloadIdentifier': ident('main'),
    'PayloadUUID': str(uuid.uuid5(NS, 'main')).upper(),
    'PayloadDisplayName': 'Hotel Paradiso Arcade',
    'PayloadDescription': 'Turns this user account into an arcade: only Hotel Paradiso Arcade can run, no websites, '
                          'and the arcade opens at login. Install it while logged in as the arcade user.',
    'PayloadOrganization': 'Hotel Paradiso',
    'PayloadScope': 'User',
    'PayloadRemovalDisallowed': False,
    'PayloadContent': content,
}

with open(os.path.join(HERE, 'Hotel Paradiso Arcade.mobileconfig'), 'wb') as f:
    plistlib.dump(profile, f)
print('wrote Hotel Paradiso Arcade.mobileconfig')
