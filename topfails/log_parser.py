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
#   Jeff Hammel <jhammel@mozilla.com>
#   Murali Nandigama <Murali.Nandigama@Gmail.COM>
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

  def get_potentialTestName(self, line):
    """return potential test name [None by default]"""
    return None
    
  def parse(self, fp):
    """
    parse the file, returning the test failures:
    {'test': test, 'text': text, 'reason': mgroup(1)} ]
    -fp: file-like object
    """
    # Look for test failures.
    failures = []
    lines = fp.readlines()
    potentialTestName = None
    for idx, line in enumerate(lines):

      # get the potential real name for reporting
      # a test for an automation.py or automationutils.processLeakLog failure
      potentialTestName = self.get_potentialTestName(line) or potentialTestName

      # test to see if the line is a failure
      m = self.testfailedRe.match(line)
      if not m:
        continue

      # name of the test
      test = m.group(2).strip() or "[unittest-log.py: no logged test]"

      # substitute potentialTestName for the test name if
      # test is automation.py or automationutils.processLeakLog
      if 'automation.py' in test or 'automationutils.processLeakLog' in test:
        if potentialTestName is not None: 
          test = potentialTestName
          potentialTestName = None

      # Code bits below try to change back slash to forward slash
      # and get rid of varibale prepends to the /test/../.. names              
      if test.find('\\') != -1:
        test = test.replace('\\','/')
      if test.find('/') != -1:
        tup=test.partition('build/')
        if len(tup[2]) > 2:
          test=tup[2]
        else :
          test=tup[0]

      # fail log text
      text = m.group(3).strip() or "[unittest-log.py: no logged text]"

      # append interesting data to failures return value
      failures.append({'test': test, 'text': text, 'reason': m.group(1).rstrip()})
        
    return failures
  
class ReftestParser(LogParser):
  """
  applies to
  - Reftest
  - Crashtest
  - JSReftest

  TODO:
  - look for PROCESS-CRASH as well as UNEXPECTED-FAIL
    [PROCESS-CRASH is a harness crash]
  - need an actual log file with TEST-UNEXPECTED-FAIL with automation.py
  """

  def get_potentialTestName(self, line):
    """
    If it is jsreftest,crashtest we see 'INFO | Loading' in line
    as the potential real test name
    """
    if "INFO | Loading" in line:
      return line.split('INFO | Loading ', 1)[-1]
    
  
class MochitestParser(LogParser):
  """
  applies to
  - Mochitest-plain
  - Mochitest-chrome
  - Mochitest-browserchrome
  - Mochitest-a11y

  TODO: unhandled cases:
  - harness completes and automation.py hangs:
  "'62521 INFO TEST-PASS | /tests/content/xbl/test/test_bug542406.xhtml | Field three readonly?\n',
 '62523 INFO Passed: 60569\n',
 '62524 INFO Failed: 44\n',
 '62525 INFO Todo:   770\n',
 '62526 INFO SimpleTest FINISHED\n',
 'TEST-UNEXPECTED-FAIL | automation.py | application timed out after 330 seconds with no output\n',
 "Can't trigger Breakpad, just killing process\n",
 'INFO | automation.py | Application ran for: 0:24:44.270038\n',
 'INFO | automation.py | Reading PID log: /var/folders/H5/H5TD8hgwEqKq9hgKlayjWU+++TM/-Tmp-/tmpEjNEf2pidlog\n',
 "WARNING | automationutils.processLeakLog() | refcount logging is off, so leaks can't be detected!\n",
 '\n',
 'INFO | runtests.py | Running tests: end.\n',
 'program finished with exit code 247\n',
 'elapsedTime=1496.639870\n',"
  """

  def get_potentialTestName(self, line):
    """Check all lines if they have INFO Running"""
    if "INFO Running" in line:
      return line.split('INFO Running ', 1)[-1].rstrip('.') # strip trailing ellipsis

  
class XPCshellParser(LogParser):
  """
  parser XPCShell results
  """

class CheckParser(LogParser):
  """
  parses results from `make check` (C compiled code tests)
  """
