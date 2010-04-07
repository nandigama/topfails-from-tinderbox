
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

#
# DB schema maintenance functions.
#

import logging

__all__ = \
 [
  "CreateDBSchema"
 ]

def CreateDBSchema(conn):
  logging.info("Executing CreateDBSchema()")
 
  
  conn.execute("""
               CREATE TABLE IF NOT EXISTS trees( id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, name TEXT)
               """)

  conn.execute("""
               CREATE TABLE IF NOT EXISTS builds(id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, treeid INT, os INT, starttime INT, status INT, changeset TEXT, logfile TEXT)
              """)
  conn.execute("""
               CREATE INDEX builds_starttime ON builds (starttime)
               """)

  conn.execute("""
               CREATE TABLE IF NOT EXISTS tests (buildid INT, name TEXT, description TEXT)
               """)
  conn.execute("""
               CREATE INDEX tests_name ON tests (name(1024))
               """)


