# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is TopFails site code.
#    
# The Initial Developer of the Original Code is
# Mozilla foundation
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#    Jeff Hammel <jhammel@mozilla.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import re

class LogParser(object):
  """abstract base class for parsing unittest logs"""

  # 'TestFailed' expected log format is "result | test | optional text".
  testfailedRe = re.compile(r"(TEST-UNEXPECTED-.*) \| (.*) \|(.*)")

  def parse(self, fp):
    """
    parse the file, returning the test failures:
    {'test': test, 'text': text, 'reason': mgroup(1)} ]
    -fp: file-like object
    """
    # Look for test failures.
    failures = []
    
    for line in fp.readlines():
      # Check all lines if they have INFO Running or url=file:/// stuff.
      # If it is mochitest, we see the former string pattern
      # If it is jsreftest,crashtest we see the later string pattern.
      if "INFO Running" in line or "[url = file:///" in line or "INFO | Loading" in line:
        potentialTestName=line
        if "[url = file:///" in line:
          if "?test=" in line:
            potentialTestName = potentialTestName.split('?test=')[1][0:-2]
          else:
            potentialTestName = potentialTestName.split('url = ')[1][0:-1]
        elif "INFO Running" in line:
          potentialTestName = potentialTestName.split('INFO Running ')[1][0:-4]
        elif "INFO | Loading" in line:
          potentialTestName = potentialTestName.split('INFO | Loading ')[1] 
        else :
          potentialTestName= "[unittest-log.py: no logged test]"
                
      m = self.testfailedRe.match(line)
      if not m:
        continue
        
      test = rawtest = m.group(2).strip() or "[unittest-log.py: no logged test]"
      if 'automation.py' in test or 'automationutils.processLeakLog' in test:
        if potentialTestName != "":
          test = rawtest = potentialTestName
          potentialTestName=""

      # Code bits below try to change back slash to forward slash
      # and get rid of varibale prepends to the /test/../.. names
              
      if rawtest.find('\\') != -1:
        test = rawtest.replace('\\','/')

      if test.find('/') != -1:
        tup=test.partition('build/')
        if len(tup[2]) > 2:
          test=tup[2]
        else :
          test=tup[0]
                
      text = m.group(3).strip() or "[unittest-log.py: no logged text]"
      failures.append({'test': test, 'text': text, 'reason': m.group(1).rstrip()})
        
    return failures
  
class ReftestParser(LogParser):
  """
  applies to
  - Reftest
  - Crashtest
  - JSReftest
  """

class MochitestParser(LogParser):
  """
  applies to
  - Mochitest-plain
  - Mochitest-chrome
  - Mochitest-browserchrome
  - Mochitest-a11y
  """

class XPCshellParser(LogParser):
  """
  parser XPCShell results
  """

class CheckParser(LogParser):
  """
  parses results from `make check` (C compiled code tests)
  """
