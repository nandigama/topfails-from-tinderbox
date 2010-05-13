from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('topfails.viewer.views',
    (r'^$', 'index'),
    url(r'^trees/(?P<tree>.+)?$','trees', name='trees'),
    url(r'^tree/(?P<tree>.+)?$','tree', name='tree'),
    url(r'^changesets/(?P<tree>.+)?$','changesets', name='changesets'),
    url(r'^changesets/(?P<tree>.+)/(?P<changeset>[a-f0-9]+)$', 'changeset', name='changeset'),
    url(r'^tests/(?P<tree>.+)?$','tests', name='tests'),
    url(r'^test/(?P<tree>.+)?$','test', name='test'),
    url(r'^timeline/(?P<tree>.+)?$','timeline', name='timeline'),
    url(r'^topfails/(?P<tree>.+)?$','topfails', name='topfails'),
    url(r'^failswindow/(?P<tree>.+)?$','failswindow', name='failswindow'),
    url(r'^latest/(?P<tree>.+)?$','latest', name='latest'),
    url(r'^Help/(?P<tree>.+)?$','Help', name='Help'),
)