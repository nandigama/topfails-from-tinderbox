#!/usr/bin/env python
"""
Build name:
<OS> <branch> [type of build]

Examples:

The builder: <OS> <branch> build (e.g. 'Linux mozilla-central build')
-- in this case [type of build] is the string 'build'

A debug test: <OS> <branch> debug test <test type>
-- in this case [type of build] is the string 'debug test <test type>'

An opt test: <OS> <branch> opt test <test type>

A leak test: <OS> <branch> leak test <test type>

Talos:
<OS> <branch> talos (e.g. 'Rev3 Fedora 12x64 mozilla-central talos')
-or-
<OS> <branch> talos <type> (e.g. 'Rev3 Fedora 12x64 mozilla-central talos cold')

Currently, the mappings are coded here (in python);  this has the restriction
that the mappings cannot be (intelligently) programmatically updated.
If it is desired that the mappings may be undated programmatically
(e.g. from the command line), then a [presumedly text-ish] storage method
should be used for these mappings, e.g. an .ini file

So....

All of this data lives in the buildbot-configs.
See http://hg.mozilla.org/build/buildbot-configs/file/tip/mozilla2/config.py
The mappings are duplicated here for expediency.

 - what really should happen is that this config file should be imported and
   used here.  In order for this to happen:
   - the config.py file should be refactored so that it is consumable (and probably the entire buildbot-configs as well)
   - buildbot-configs (or whatever this piece is refactored into) should
     become a real python package or otherwise installable/depended upon
"""

import re

# OS mappings
OSes = [ 'Linux',
         'Linux x86-64',
         'OS X 10.5.2',
         'OS X 10.6.2',
         'Rev3 Fedora 12',
         'Rev3 Fedora 12x64',
         'Rev3 MacOSX Leopard 10.5.8',
         'Rev3 MacOSX Snow Leopard 10.6.2',
         'Rev3 WINNT 5.1',
         'Rev3 WINNT 6.1',
         'WINNT 5.2' ]
OS_to_index = dict([(OS, index) for index, OS in enumerate(OSes)])
index_to_OS = dict([(index, OS) for index, OS in enumerate(OSes)])
OSdata = { 'Linux': {'name': 'Linux', 'bits': 32 },
           'Rev3 Fedora 12': { 'name': 'Fedora', 'bits': 32},
           'Rev3 Fedora 12x64': { 'name': 'Fedora', 'bits': 64},
	   'Linux x86-64': { 'name': 'Linux', 'bits': 64},
	   'OS X 10.5.2': { 'name': 'MAC OSX', 'bits': 32},
	   'OS X 10.6.2': { 'name': 'MAC OSX', 'bits': 64},
	   'Rev3 MacOSX Leopard 10.5.8': { 'name': 'MAC OSX', 'bits': 32},
	   'Rev3 MacOSX Snow Leopard 10.6.2': { 'name': 'MAC OSX', 'bits': 64},
	   'Rev3 WINNT 5.1': { 'name': 'Windows', 'bits': 32},
	   'Rev3 WINNT 6.1': { 'name': 'Windows', 'bits': 64},
	   'WINNT 5.2': { 'name': 'Windows', 'bits': 32},
    }

# branch objects
# branches = [ 'mozilla-central',
#              'mozilla-1.9.2',
#              'comm-central',
#              'comm-central-trunk'
#     ]
trees = { 'Firefox': 'mozilla-central',
          'Firefox3.6': 'mozilla-1.9.2',
          'Thunderbird': 'comm-central',
          'SeaMonkey': 'comm-central-trunk',
          }

build_name_regex = r'(?P<os>%s) (?P<branch>%s) (?P<type>.*)' % ('|'.join(OSes), '|'.join(trees.values()))
build_name_regex = re.compile(build_name_regex)
def parse_build_name(name):
  match = re.match(build_name_regex, name)
  if match is None:
    return None
  return match.groupdict()

if __name__ == '__main__':
  import sys
  for arg in sys.argv[1:]:
    print parse_build_name(arg)
    
