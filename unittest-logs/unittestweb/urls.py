from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('unittestweb.viewer.views',
    (r'^$', 'index'),
    (r'^/$', 'index'),
    (r'^trees$', 'trees'),
    (r'^trees/(?P<tree>.+)$', 'tree'),
    (r'^changesets$', 'changesets'),
    (r'^changesets/(?P<changeset>[a-f0-9]+)$', 'changeset'),
    (r'^tests$', 'tests'),
    (r'^test$', 'test'),
    (r'^timeline$', 'timeline'),
    (r'^topfails$', 'topfails'),
    (r'^failswindow$','failswindow'),
)
