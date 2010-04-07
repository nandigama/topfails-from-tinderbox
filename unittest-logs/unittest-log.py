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

class OS():
  Windows = 0
  Mac = 1
  Linux = 2
  Unknown = 3

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

def OSFromBuilderName(name):
  if name.startswith("Linux"):
    return OS.Linux
  if name.startswith("MacOSX") or name.startswith("OS X"):
    return OS.Mac
  if name.startswith("WINNT"):
    return OS.Windows
  return OS.Unknown

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
  
  conn.execute("""SELECT id FROM trees WHERE name = %s""", (tree))
  rows = conn.fetchone()
  if len(rows) > 0:
    return rows[0]

  # need to insert it
  conn.execute("""INSERT INTO trees (name) VALUES (%s)""", (tree,))
  return conn.lastrowid

def HaveBuild(conn, treeid, os, starttime):
  """See if we already have this build in our database."""
  conn.execute("""SELECT COUNT(*) FROM builds WHERE treeid = %s AND os = %s AND starttime = %s""", (treeid, os, starttime))
  return conn.fetchone()[0] == 1

def UpdateLogfile(conn, treeid, os, starttime, logfile):
  """Update empty 'logfile' for a given build (added in db schema v1)."""
  conn.execute("""UPDATE builds SET logfile = %s WHERE treeid = %s AND os = %s AND starttime = %s AND logfile IS NULL""", (logfile, treeid, os, starttime))

def InsertBuild(conn, treeid, os, starttime, status, logfile, changeset):
  """Insert a build into the builds table and return the id."""
  conn.execute("""INSERT INTO builds (treeid, os, starttime, status, logfile, changeset) VALUES (%s, %s, %s, %s, %s, %s)""", (treeid, os, starttime, status, logfile, changeset))
  return conn.lastrowid

def InsertTest(conn, buildid, result, name, description):
  # ToDo: Add column to save result.
  conn.execute("""INSERT INTO tests (buildid, name, description) VALUES (%s, %s, %s)""", (buildid, name, description))

def fix_tbox_json(s): # Check :: This seems to be a problem ? Murali
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
                  dest="timespan", default="15d",
                  help="Period of time to fetch data for (N[y,m,w,d,h], default=%default)")
parser.add_option("-t", "--tree", action="store",
                  dest="tree", default="Firefox",
                  help="Tinderbox tree to fetch data from (default=%default)")
parser.add_option("-d", "--database", action="store",
                  dest="db", default="topfailsdb",
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

(options, args) = parser.parse_args()

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
    connection.close()
  except  MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit (1)
  try:
    connection  =  MySQLdb.connect (host  =  options.dbhost,
                                      port  =  int(options.dbport),
                                      db  =  options.db,
                                      user  =  options.dbuser,
                                      passwd  =  options.dbpasswd)
    conn=connection.cursor()
  except MySQLdb.Error, e:
    print "Error %d: %s" % (e.args[0], e.args[1])
    sys.exit(1)
  
  CreateDBSchema(conn)


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

  tboxurl = "http://tinderbox.mozilla.org/showbuilds.cgi?tree=%(tree)s&maxdate=%(maxdate)d&noignore=1&hours=%(hours)d&json=1" \
              % {'tree': options.tree,
                 'maxdate': curtime + chunksize, # tbox wants the end time
                 'hours': int(chunksize / S_IN_H)}
  u = urllib.urlopen(tboxurl)
  tboxjson = ''.join(u.readlines())
  u.close()

  tboxjson = fix_tbox_json(tboxjson)
  try:
    tboxdata = json.loads(tboxjson)
  except Exception, inst:
    print >>sys.stderr, "Error parsing JSON: %s" % inst
    continue

  # we only care about unit test boxes
  unittest_indices = [tboxdata['build_name_index'][x] for x in tboxdata['build_name_index'] if re.search("test|xpc", x)]
  # read build table
  # 'TestFailed' expected log format is "result | test | optional text".
  testfailedRe = re.compile(r"(TEST-UNEXPECTED-.*) \| (.*) \|(.*)")
  for timerow in tboxdata['build_table']:
    for index in unittest_indices:
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
      os = OSFromBuilderName(name)
      starttime = int(build['buildtime'])
      # skip builds we've already seen
      if HaveBuild(conn, treeid, os, starttime):
        logging.info("Skipping already seen build '%s' at %d (%s)" % (name, starttime, ctime(starttime)))

        # Call 'UpdateLogfile()' anyway.
        UpdateLogfile(conn, treeid, os, starttime, build['logfile'])
        continue

      # must have scrape data for changeset
      if build['logfile'] not in tboxdata['scrape']:
        continue
      changeset = FindChangesetInScrape(tboxdata['scrape'][build['logfile']])
      if changeset is None:
        continue

      buildid = InsertBuild(conn, treeid, os, starttime, status, build['logfile'], changeset)

      # 'Success' is fine as is.
      if status == BuildStatus.Success:
        pass

      # Parse log to save 'TestFailed' results.
      elif status == BuildStatus.TestFailed:
        logging.info("Checking build log for '%s' at %d (%s)" % (name, starttime, ctime(starttime)))
        try:
          # Grab the build log.
          log, headers = urllib.urlretrieve("http://tinderbox.mozilla.org/%s/%s" % (options.tree, build['logfile']))
          gz = GzipFile(log)
          # Look for test failures.
          for line in gz:
            m = testfailedRe.match(line)
            if m:
              test = m.group(2).strip() or "[unittest-log.py: no logged test]"
              text = m.group(3).strip() or "[unittest-log.py: no logged text]"
              InsertTest(conn, buildid, m.group(1).rstrip(), test, text)
        except:
          logging.error("Unexpected error: %s" % sys.exc_info()[0])
          #XXX: handle me?

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
        InsertTest(conn, buildid, "TEST-UNEXPECTED-FAIL", "unittest-log.py", "Unknown status = '%s'!" % build['buildstatus'])
        continue



  if chunk < totalchunks:
    sleep(SLEEP_TIME)
  curtime += chunksize

conn.close()

logging.info("Done")
