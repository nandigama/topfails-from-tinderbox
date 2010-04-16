from django.shortcuts import render_to_response, get_list_or_404
from unittestweb.viewer.models import Builds, Trees, Tests, OS_CHOICES, get_most_failing_tests, get_fails_in_timerange
import re
from django.http import HttpResponse
import json

def latest(request,tree='Firefox'):
  failures = get_list_or_404(Tests.objects.filter(build__tree__name=tree).order_by('-build__starttime')[:20])
  if request.GET.has_key('json'):
    jtext = [{"Test_name":f.name, "Build_status":f.build.status, "Logfile": f.build.tinderbox_link(),"Changeset":f.build.json_changeset_link() , "Failure_description":f.description} for f in failures]
    return HttpResponse(json.dumps(jtext))
  else:
    return render_to_response('viewer/latest.html', {'failures': failures, 'tree' : tree})

def index(request,tree='Firefox'):
  failures = get_list_or_404(Tests.objects.filter(build__tree__name=tree).order_by('-build__starttime')[:20])
  return render_to_response('viewer/index.html', {'failures': failures, 'tree' : tree})


def trees(request,tree='Firefox'):
  alltrees = Trees.objects.all().order_by('name')
  return render_to_response('viewer/trees.html', {'trees': alltrees , 'tree' : tree})

def tree(request, tree='Firefox'):
  newestbuilds = get_list_or_404(Builds.objects.filter(tree__name__exact=tree).order_by('-starttime')[:5])
  return render_to_response('viewer/tree.html', {'tree': tree, 'newestbuilds': newestbuilds})

def changesets(request,tree='Firefox'):
  build_csets = Builds.objects.filter(tree__name__exact=tree).values('changeset').distinct()
  return render_to_response('viewer/changesets.html', { 'tree' : tree,'changesets': [b['changeset'] for b in build_csets]})

def changeset(request, changeset,tree='Firefox'):
  builds = get_list_or_404(Builds, changeset__exact=changeset)
  return render_to_response('viewer/changeset.html', {'changeset': changeset, 'builds': builds, 'tree' : tree})

def tests(request,tree='Firefox'):
    test_names = Tests.objects.filter(build__tree__name__exact=tree).values('name').distinct()
    if request.GET.has_key('json'):
      jtext = list(test_names)
      return HttpResponse(json.dumps(jtext))
    else:
      return render_to_response('viewer/tests.html', { 'tree' : tree, 'tests': [t['name'] for t in test_names]})

def test(request,tree='Firefox'):
  failures = get_list_or_404(Tests.objects.filter(build__tree__name__exact=tree).filter(name__exact=request.GET['name']).order_by('-build__starttime'))
  return render_to_response('viewer/test.html', {'test': request.GET['name'], 'failures': failures, 'tree' : tree})

def topfails(request,tree='Firefox'):
  failures = get_most_failing_tests(tree)
  if request.GET.has_key('json'):
    jtext = list(failures)
    return HttpResponse(json.dumps(jtext))
  else:
    return render_to_response('viewer/topfails.html', {'failures': failures, 'tree' : tree})
  
def Help(request,tree):
  return render_to_response('viewer/Help.html',{'tree':tree})  
  
def timeline(request,tree='Firefox'):
  name = request.GET['name']
  builds = get_list_or_404(Builds.objects.filter(tree__name__exact=tree), tests__name__exact=name)
  buildlist = []
  desc_list = []
  for b in builds:
    descs = b.tests_set.filter(name__exact=name).order_by('id')
    desc = '\n'.join(descs.values_list('description', flat=True))
    if desc not in desc_list:
      desc_list.append(desc)
    desc_i = desc_list.index(desc)
    buildlist.append({'build': b,
                      'desctype': desc_i,
                      'description': desc,
                      'os': OS_CHOICES[b.os][1],
                      'time': b.startdate().isoformat() + "Z",
                      })
  return render_to_response('viewer/timeline.html', {'test': name,
                                                     'descriptions': desc_list,
                                                     'builds': buildlist, 'tree' : tree})

def failswindow(request,tree='Firefox'):
  period=request.GET['window']
  m = re.match("(\d+)([ymwdh])", period)
  failures = get_fails_in_timerange(period,tree)
  if request.GET.has_key('json'):
    jtext = list(failures)
    return HttpResponse(json.dumps(jtext))
  else:
    if m.group(2) == 'd':
      prd='days'
    elif m.group(2) == 'h':
      prd = 'hours'
    elif m.group(2) == 'w':
      prd = 'weeks'
    elif m.group(2) == 'm':
      prd = 'months'
    elif m.group(2) == 'y':
      prd = 'years'
    else:
      prd = 'days'
    
      
    return render_to_response('viewer/failswindow.html', {'failures': failures,'n':m.group(1),'d':prd, 'tree' : tree})
    
