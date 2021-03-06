import re
from django.db import models, connection
from datetime import datetime
from time import ctime, sleep, time
from topfails.mappings import OSes

# class OS():
#   Windows = 0
#   Mac = 1
#   Linux = 2
#   Unknown = 3

# OS_CHOICES = (
#     (OS.Windows, 'Windows'),
#     (OS.Mac, 'Mac'),
#     (OS.Linux, 'Linux'),
#     (OS.Unknown, 'Unknown')
# )
OS_CHOICES = tuple([(index, OS) for index, OS in enumerate(OSes)])

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


class Tree(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=45, blank=True)
    
    def __unicode__(self):
      return self.name
    
class Build(models.Model):
    id = models.AutoField(primary_key=True)
    os = models.IntegerField(choices=OS_CHOICES)
    tree = models.ForeignKey(Tree)
    starttime = models.IntegerField(null=True, blank=True)
    status = models.IntegerField(choices=BUILDSTATUS_CHOICES)
    changeset = models.CharField(max_length=80,blank=True)
    logfile = models.CharField(max_length=300,blank=True)
    
    def startdate(self):
        return datetime.fromtimestamp(self.starttime)
    
    def changesetlink(self):
      if str(self.tree)  == 'Firefox':
        return '<a href="%s/rev/%s">%s</a>' % ("http://hg.mozilla.org/mozilla-central", self.changeset, self.changeset)
      elif str(self.tree) == 'Firefox3.6':
        return '<a href="%s/rev/%s">%s</a>' % ("http://hg.mozilla.org/releases/mozilla-1.9.2", self.changeset, self.changeset)
      elif str(self.tree) == 'Thunderbird' or str(self.tree) == 'SeaMonkey':  
        return '<a href="%s/rev/%s">%s</a>' % ("http://hg.mozilla.org/comm-central", self.changeset, self.changeset)
      else :
        return '<a href="%s/rev/%s">%s</a>' % ("http://hg.mozilla.org/mozilla-central", self.changeset, self.changeset) 
    
    def jsonchangesetlink(self):
      return "%s/rev/%s" %  ("http://hg.mozilla.org/mozilla-central", self.changeset)
    
    def tinderboxlink(self):
      if self.logfile:
        return "http://tinderbox.mozilla.org/showlog.cgi?log=%s/%s" % (self.tree.name, self.logfile)
      return "http://tinderbox.mozilla.org/showbuilds.cgi?tree=%s&maxdate=%d&hours=3" % (self.tree.name, self.starttime)
    

class Test(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=300, blank=True)
    
    def __unicode__(self):
      return self.name
   
class TestFailure(models.Model):
    id = models.AutoField(primary_key=True)
    build = models.ForeignKey(Build)
    test = models.ForeignKey(Test)
    failtext = models.CharField(max_length=400, blank=True)
       
    @classmethod
    def get_most_failing_tests(cls,tree):
      return cls.objects.filter(build__tree__name=tree).values('test__name').annotate(count=models.Count('test__name')).order_by('-count')[:25]
   
    @classmethod
    def get_time_failing_tests(cls,tree):
      return cls.objects.filter(build__tree__name=tree).values('test__name').annotate(count=models.Count('test__name')).order_by('-count')
    
    @classmethod
    def get_fails_in_timerange(cls,period,tree):
      
      # Get current time, in seconds.
      endtime = int(time())
      
      m = re.match("(\d+)([ymwdh])", period)
      if m is None:
        print >>sys.stderr, "ERROR: bad timespan = '%s'!" % options.timespan
        sys.exit(1)
      
      timespan = int(m.group(1)) * {'y': 365 * 24 * 3600,
                                    'm':  30 * 24 * 3600,
                                    'w':   7 * 24 * 3600,
                                    'd':       24 * 3600,
                                    'h':            3600}[m.group(2)]
      # Set current time to beginning of requested timespan ending now.
      curtime = endtime - timespan
      qs = cls.get_time_failing_tests(tree)
      return qs.filter(build__starttime__gt=curtime)

    
