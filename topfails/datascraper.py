#!/usr/bin/env python
#Indentation is 2 spaces  ***** DO NOT USE TABS *****

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
#   Serge Gautherie <sgautherie.bz@free.fr>
#   Ted Mielczarek <ted.mielczarek@gmail.com>.
#   Murali Nandigama <Murali.Nandigama@Gmail.COM>
#   Jeff Hammel <jhammel@mozilla.com>
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

import re, os, sys, urllib, logging
import MySQLdb # Moved from  sqlite3 db  to MySQL
from time import ctime, sleep, time
from math import ceil
from optparse import OptionParser
from gzip import GzipFile
import binascii

# local imports
import logparser
import mappings

try:
  # 'Availability: Unix.'
  from time import tzset
except ImportError:
  print >>sys.stderr, "WARNING: time.tzset() is not available on non-Unixes!"

  # Define a fake function. (for development use only)
  # ToDo: Investigate Windows/etc situation. (Bug 525699)
  def tzset():
    pass

try:
  import simplejson as json
except ImportError:
  try:
    # 'New in version 2.6.'
    import json
  except ImportError:
    print >>sys.stderr, "ERROR: no simplejson nor json package found!"
    sys.exit(1)

from dbschema import CreateDBSchema  

# Number of seconds in a hour: 60 mn * 60 s = 3600 s.
S_IN_H = 3600
# Download data in 24 hours chunks so as not to overwhelm the tinderbox server.
chunksize = 24 * S_IN_H
# seconds between requests
SLEEP_TIME = 1

class BuildStatus():
  # Unavailable builds to skip.
  # Values need (only) to be less than the 'Success' one.
  NoBuild = -2
  InProgress = -1

  # Builds to save in the db.
  # Do not change these values (without updating db data).
  Success = 0
  TestFailed = 1
  Burning = 2
  Exception = 3
  Unknown = 4

csetre = re.compile("rev/([0-9A-Za-z]+)")
def FindChangesetInScrape(scrape):
  for line in scrape:
    m = csetre.search(line)
    if m:
      return m.group(1)
  return None

buildStatuses = {
  # "No build in progress".
  "null":       BuildStatus.NoBuild,
  # "Build in progress".
  "building":   BuildStatus.InProgress,
  # "Successful build".
  "success":    BuildStatus.Success,
  # "Successful build, but tests failed".
  "testfailed": BuildStatus.TestFailed,
  # "Build failed".
  "busted":     BuildStatus.Burning,
  # "Non-build failure". (i.e. "automation failure")
  "exception":  BuildStatus.Exception,
}
def BuildStatusFromText(status):
  try:
    return buildStatuses[status]
  except KeyError:
    # Log 'Unknown' status failure: this should not happen (unless new statuses are created), but we want to know if it does.
    logging.info("WARNING: unknown status = '%s'!" % status)
    return BuildStatus.Unknown

def GetOrInsertTree(conn, tree):
  """Get an id for a tree named |tree|. If it's not already in the trees
  table, insert a new row and return the id."""
  
  conn.execute("""
               SELECT id FROM viewer_tree WHERE name = %s
               """, (tree))
  if conn.rowcount > 0:
    return conn.fetchone()[0]

  # need to insert it
  conn.execute("""
        INSERT INTO viewer_tree (name) VALUES (%s)
        """, (tree))
  connection.commit()
  return conn.lastrowid

def GetOrInsertTest(conn, testname):
  """Get an id for a test named |testname|. If it's not already in the testnames
  table, insert a new row and return the id."""
  
  conn.execute("""
               SELECT id FROM viewer_test WHERE name = %s
               """, (testname))
  if conn.rowcount > 0:
    return conn.fetchone()[0]

  # need to insert it
  conn.execute("""
               INSERT INTO viewer_test (name) VALUES (%s)
               """, (testname))
  connection.commit()
  return conn.lastrowid

def HaveBuild(conn, treeid, _os, starttime):
  """See if we already have this build in our database."""
  conn.execute("""
               SELECT COUNT(*) FROM viewer_build WHERE tree_id = %s AND os = %s AND starttime = %s
               """, (treeid, _os, starttime))
  return conn.fetchone()[0] == 1

def UpdateLogfile(conn, treeid, _os, starttime, logfile):
  """Update empty 'logfile' for a given build (added in db schema v1)."""
  conn.execute("""
               UPDATE viewer_build SET logfile = %s WHERE tree_id = %s AND os = %s AND starttime = %s AND logfile IS NULL
               """, (logfile, treeid, _os, starttime))
  connection.commit()

def InsertBuild(conn, treeid, _os, starttime, status, logfile, changeset):
  """Insert a build into the builds table and return the id."""
  conn.execute("""
               INSERT INTO viewer_build (tree_id, os, starttime, status, logfile, changeset) VALUES (%s, %s, %s, %s, %s, %s)
               """, (treeid, _os, starttime, status, logfile, changeset))
  connection.commit()
  return conn.lastrowid

def HaveFailRecord(conn,buildid, result, testnames_id):
  """See if we already have this failRecord in our database."""
  conn.execute("""
               SELECT COUNT(*) FROM viewer_testfailure WHERE build_id = %s AND test_id = %s 
               """, (buildid, testnames_id))
  return conn.fetchone()[0] == 1
  
def InsertTest(conn, buildid, result, testnames_id, description):
  # ToDo: Add column to save result.
  conn.execute("""
               INSERT INTO viewer_testfailure (build_id, test_id, failtext) VALUES (%s, %s, %s)
               """, (buildid, testnames_id, description))
  connection.commit()
def asciirepl(match):
  # replace the hexadecimal characters with ascii characters
  s = match.group()  
  return binascii.unhexlify(s)  

def reformat_content(data):
  p = re.compile(r'\\x(\w{2})')
  return p.sub(asciirepl, data)
  
  
def fix_tbox_json(s): 
  """Fixes up tinderbox json.

  Tinderbox returns strings as single-quoted strings, and occasionally
  includes the unquoted substring 'undef' (with quotes) in the output, e.g.

  {'key': 'hello 'undef' world'}

  should return a dictionary

  {'key': 'hello \'undef\' world'}
  """

  json_data = re.sub(r"^tinderbox_data\s*=\s*", "", s)
  json_data = re.sub(r";$", "", json_data)
  retval = []
  in_str = False
  in_esc = False
  skip = 0
  for i,c in enumerate(json_data):
    # The tinderbox data is a fracked json. and it some times contains
    # Control characters. that would totally fail the json.loads step.
    # So, eliminate them .. all of them .. here -- Murali
    if (c < '\xFD' and c > '\x1F') or c == '\n' or c == '\r' :
      if skip > 0:
        skip -= 1
        continue
  
      if in_str:
        if in_esc:
          if c == "'":
            retval.append("'")
          else:
            retval.append("\\")
            retval.append(c)
          in_esc = False
        elif c == "\\":
          in_esc = True
        elif c == "\"":
          retval.append("\\\"")
        elif c == "'":
          if json_data[i:i+7] == "'undef'":
            retval.append("'undef'")
            skip = 7
          else:
            retval.append("\"")
            in_str = False
        else:
          retval.append(c)
      else:
        if c == "'":
          retval.append("\"")
          in_str = True
        else:
          retval.append(c)
  return "".join(retval)

parser = OptionParser()
parser.add_option("-s", "--span", action="store",
                  dest="timespan", default="20d",
                  help="Period of time to fetch data for (N[y,m,w,d,h], default=%default)")
parser.add_option("-t", "--tree", action="store",
                  dest="tree", default="Firefox",
                  help="Tinderbox tree to fetch data from (default=%default)")
parser.add_option("-d", "--database", action="store",
                  dest="db", default="topfails",
                  help="Database filename (default=%default)")
parser.add_option("--host", action="store",
                  dest="dbhost", default="localhost",
                  help="Database host name (default=%default)")
parser.add_option( "--port", action="store",
                  dest="dbport",default="3306",
                  help="Database port (default=%default)")
parser.add_option("-u", "--user", action="store",
                  dest="dbuser", default="root",
                  help="Database username (default=%default)")
parser.add_option("-p", "--passwd", action="store",
                  dest="dbpasswd",
                  help="Database user password")
parser.add_option("-v", "--verbose", action="store_true",
                  dest="verbose", default="False",
                  help="Enable verbose logging")
parser.add_option("--debug", action='store_true',
                  dest='debug', default=False,
                  help="enable interactive debugger on exceptions (pdb)")
parser.add_option("--die", action='store_true',
                  dest='die', default=False,
                  help="enable application to die on error")
(options, args) = parser.parse_args()

# check parsed options
if options.tree not in mappings.trees:
  parser.error("Unknown tree: '%s'; should be one of [%s]" % (options.tree, ', '.join(mappings.trees)))

logging.basicConfig(level=options.verbose and logging.DEBUG or logging.WARNING)

os.environ['TZ'] = "US/Pacific"
tzset()
# Get current time, in seconds.
endtime = int(time())

m = re.match("(\d+)([ymwdh])", options.timespan)
if m is None:
  print >>sys.stderr, "ERROR: bad timespan = '%s'!" % options.timespan
  sys.exit(1)

timespan = int(m.group(1)) * {'y': 365 * 24 * S_IN_H,
                              'm':  30 * 24 * S_IN_H,
                              'w':   7 * 24 * S_IN_H,
                              'd':       24 * S_IN_H,
                              'h':            S_IN_H}[m.group(2)]
# Set current time to beginning of requested timespan ending now.
curtime = endtime - timespan


createdb=False


try:
  connection  =  MySQLdb.connect (host  =  options.dbhost,
                                    port  =  int(options.dbport),
                                    db  =  options.db,
                                    user  =  options.dbuser,
                                    passwd  =  options.dbpasswd)
  conn=connection.cursor()
except MySQLdb.Error, e:
  print "Error %d: %s" % (e.args[0], e.args[1])
  createdb = True
     

if createdb:
  connection = MySQLdb.connect (host  =  options.dbhost,
                                    port  =  int(options.dbport),
                                    user  =  options.dbuser,
                                    passwd  =  options.dbpasswd)
  conn = connection.cursor()
  try:
    createdatabase='create database %s' %(options.db)
    conn.execute (createdatabase)
    conn.close()
    connection.commit()
    connection.close()
  except  MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit (1)
  try:
    connection = MySQLdb.connect(host=options.dbhost,
                                 port=int(options.dbport),
                                 db=options.db,
                                 user=options.dbuser,
                                 passwd=options.dbpasswd)
    conn=connection.cursor()
  except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)

  # if the database doesn't exist, create the schema using django by
  # running models.py syncdb
  # set the dbuser and dbpasswd environment vsariables for settings.py
  # to work properly
  os.environ['dbuser'] = options.dbuser
  os.environ['dbpasswd'] = options.dbpasswd
  from django.core.management import execute_manager
  import settings
  execute_manager(settings, ['manage.py','syncdb'])


treeid = GetOrInsertTree(conn, options.tree)

logging.info("Reading tinderbox data...")

chunk = 0
# add a fudge factor here, since builds can take up to 3 hours to finish,
# and we can't get the changeset unless we ask for time up to the end of the
# build
endtime += 3 * S_IN_H
timespan += 3 * S_IN_H
totalchunks = int(ceil(float(timespan) / chunksize))

while curtime < endtime and chunk < totalchunks:
  chunk += 1
  logging.info("Chunk %d/%d" % (chunk, totalchunks))

  if (endtime - curtime) < chunksize:
    chunksize = endtime - curtime

  tboxurl = "http://tinderbox.mozilla.org/showbuilds.cgi?tree=%(tree)s&maxdate=%(maxdate)d&noignore=1&hours=%(hours)d&json=1&noignore=1" \
              % {'tree': options.tree,
                 'maxdate': curtime + chunksize, # tbox wants the end time
                 'hours': int(chunksize / S_IN_H)}
  u = urllib.urlopen(tboxurl)
  tboxjson = u.read()
  #tboxjson = tboxjson.encode('utf-8').decode('string_escape').decode('utf-8')
  #tboxjson = ''.join(u.readlines())
  u.close()
  
  tboxjson = fix_tbox_json(tboxjson)
  try:
    tboxdata = json.loads(tboxjson)
  except Exception, inst:
    print >>sys.stderr, "Error parsing JSON: %s" % inst
    continue

  # dictionary of parsers
  parsers = {
    'check': logparser.CheckParser,
    'mochitest': logparser.MochitestParser,
    'reftest': logparser.ReftestParser,
    'jsreftest': logparser.ReftestParser,
    'crashtest': logparser.ReftestParser,
    'xpcshell': logparser.XPCshellParser,
    }

  # regular expression to find the harness
  harness_regex = r'.* (%s)(-.*)?' % '|'.join(parsers.keys())
  
  # we only care about unit test boxes
  unittest_indices = [(logname, index) #tboxdata['build_name_index'][index]
                      for logname, index in tboxdata['build_name_index'].items()
                      if re.search("ref|mochi|xpc|check", logname)]

  # 'TestFailed' expected log format is "result | test | optional text".
  # testfailedRe = re.compile(r"(TEST-UNEXPECTED-.*) \| (.*) \|(.*)")
  # XXX ^ to delete
  
  # read build table
  for timerow in tboxdata['build_table']:
    for logname, index in unittest_indices:
      if index >= len(timerow) or timerow[index] == -1:
        continue

      build = timerow[index]
      if 'buildname' not in build or \
         'logfile'   not in build:
        continue

      status = BuildStatusFromText(build['buildstatus'])
      # Skip unavailable "builds".
      if status < BuildStatus.Success:
        continue

      name = build['buildname']
      build_name_dict = mappings.parse_build_name(name)
      if build_name_dict:
        _os = mappings.OS_to_index[build_name_dict['os']]
      else:
        _os = -1 # UNKNOWN
      starttime = int(build['buildtime'])
      # skip builds we've already seen
      if HaveBuild(conn, treeid, _os, starttime):
        logging.info("Skipping already seen build '%s' at %d (%s)" % (name, starttime, ctime(starttime)))

        # Call 'UpdateLogfile()' anyway.
        UpdateLogfile(conn, treeid, _os, starttime, build['logfile'])
        continue

      # must have scrape data for changeset
      if build['logfile'] not in tboxdata['scrape']:
        continue
      changeset = FindChangesetInScrape(tboxdata['scrape'][build['logfile']])
      if changeset is None:
        continue

      buildid = InsertBuild(conn, treeid, _os, starttime, status, build['logfile'], changeset)

      # 'Success' is fine as is.
      if status == BuildStatus.Success:
        pass

      # Parse log to save 'TestFailed' results.
      elif status == BuildStatus.TestFailed :
        logging.info("Checking build log for '%s' at %d (%s)" % (name, starttime, ctime(starttime)))
        try:
          failures = []
          # Grab the build log.
          log, headers = urllib.urlretrieve("http://tinderbox.mozilla.org/%s/%s" % (options.tree, build['logfile']))
          gz = GzipFile(log) # I need a list of lines from the build log

          # assured to match because we search for this above
          harness_type = re.match(harness_regex, logname).groups()[0]
          parser = parsers.get(harness_type, logparser.LogParser)()
          failures = parser.parse(gz)

          # add the failures to the database
          for failure in failures:

            # convenience variables; can probably delete
            test = failure['test']
            text = failure['text']
            reason = failure['reason']
            
            testnames_id=GetOrInsertTest(conn,test)
            if HaveFailRecord(conn,buildid,  reason, testnames_id):
              logging.info("Skipping already recorded failure '%s' in build with id '%s' with failure record '%s' " % (test, buildid, text))
            else:  
              InsertTest(conn, buildid, reason, testnames_id, text)
                      
        except Exception, e:
          errstring = "Unexpected error: %s" % e
          if options.debug:
            print errstring
            import pdb; pdb.set_trace()
          elif options.die:
            raise
          else:
            logging.error(errstring)

      # Ignore 'Burning' builds: tests may have run nontheless, but it's safer to discard them :-|
      elif status == BuildStatus.Burning:
        continue
      
      # Ignore 'Exception' builds: should only be worse than 'Burning'.
      # (Don't know much at time of writing, since this feature is not active yet: see bug 476656 and follow-ups.)
      elif status == BuildStatus.Exception:
        continue

      # Save 'Unknown' status failure: this should not happen (unless new statuses are created), but we want to know if it does.
      elif status == BuildStatus.Unknown:
        # Add a fake test failure.
        InsertTest(conn, buildid, "TEST-UNEXPECTED-FAIL", "99999999999", "Unknown status = '%s'!" % build['buildstatus'])
        continue



  if chunk < totalchunks:
    sleep(SLEEP_TIME)
  curtime += chunksize
  
conn.close()
connection.commit()
connection.close()
logging.info("Done")
