# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models, connection
from datetime import datetime

class OS():
  Windows = 0
  Mac = 1
  Linux = 2
  Unknown = 3

OS_CHOICES = (
    (OS.Windows, 'Windows'),
    (OS.Mac, 'Mac'),
    (OS.Linux, 'Linux'),
    (OS.Unknown, 'Unknown')
)

class BuildStatus():
  Success = 0
  TestFailed = 1
  Burning = 2
  Exception = 3
  Unknown = 4

BUILDSTATUS_CHOICES = (
    (BuildStatus.Success, 'Success'),
    (BuildStatus.TestFailed, 'Test Failed'),
    (BuildStatus.Burning, 'Burning'),
    (BuildStatus.Exception, 'Exception'),
    (BuildStatus.Unknown, 'Unknown')
)

class Trees(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.TextField(blank=True)
    def __unicode__(self):
        return self.name
    class Meta:
        db_table = 'trees'

class Builds(models.Model):
    id = models.IntegerField(primary_key=True)
    tree = models.ForeignKey(Trees, db_column="treeid")
    os = models.IntegerField(choices=OS_CHOICES)
    starttime = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(choices=BUILDSTATUS_CHOICES)
    logfile = models.TextField(blank=True)
    changeset = models.TextField(blank=True)
    def startdate(self):
        return datetime.fromtimestamp(self.starttime)
    def changeset_link(self):
      return '<a href="%s/rev/%s">%s</a>' % ("http://hg.mozilla.org/mozilla-central", self.changeset, self.changeset)
    def tinderbox_link(self):
      if self.logfile:
        return "http://tinderbox.mozilla.org/showlog.cgi?log=%s/%s" % (self.tree.name, self.logfile)
      return "http://tinderbox.mozilla.org/showbuilds.cgi?tree=%s&maxdate=%d&hours=3" % (self.tree.name, self.starttime)
    class Meta:
        db_table = 'builds'

class Tests(models.Model):
    id = models.IntegerField(primary_key=True)
    build = models.ForeignKey(Builds, db_column="buildid")
    name = models.TextField(blank=True)
    description = models.TextField(blank=True)
    class Meta:
        db_table = 'tests'

def get_most_failing_tests():
    cursor = connection.cursor()
    cursor.execute("select count(*), name from (select builds.id, name from builds inner join tests on builds.id = tests.buildid  group by builds.id, name) group by name order by count(*) desc limit 250")
    for row in cursor:
        yield row
