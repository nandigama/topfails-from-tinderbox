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
  CREATE TABLE viewer_tree (
      id integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
      name varchar(45) NOT NULL
      )
  """)
  
  conn.execute("""
  CREATE TABLE viewer_build (
      id integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
      os integer NOT NULL,
      tree_id integer NOT NULL,
      starttime integer,
      status integer NOT NULL,
      changeset varchar(80) NOT NULL,
      logfile varchar(300) NOT NULL
      )
  """)
 
  conn.execute("""
  ALTER TABLE viewer_build 
  ADD CONSTRAINT tree_id_refs_id_11e44bee 
  FOREIGN KEY (tree_id) 
  REFERENCES viewer_tree (id)
  """)

  conn.execute("""
  CREATE TABLE viewer_test (
      id integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
      name varchar(300) NOT NULL
      )
  """)
 
  conn.execute("""
  CREATE TABLE viewer_testfailure (
      id integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
      build_id integer NOT NULL,
      test_id integer NOT NULL,
      failtext varchar(400) NOT NULL
      )
  """)
  
  conn.execute("""
  ALTER TABLE viewer_testfailure 
  ADD CONSTRAINT test_id_refs_id_1cc1b9e6 
  FOREIGN KEY (test_id) 
  REFERENCES viewer_test (id)
  """)
  
  conn.execute("""
  ALTER TABLE viewer_testfailure 
  ADD CONSTRAINT build_id_refs_id_112c09cb 
  FOREIGN KEY (build_id) 
  REFERENCES viewer_build (id)
  """)
  
  conn.execute("""
  CREATE INDEX viewer_build_tree_id ON viewer_build (tree_id)
  """)
  
  conn.execute("""
  CREATE INDEX viewer_testfailure_build_id ON viewer_testfailure (build_id)
  """)
  
  conn.execute("""
  CREATE INDEX viewer_testfailure_test_id ON viewer_testfailure (test_id)
  """)


