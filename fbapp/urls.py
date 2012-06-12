from django.conf.urls.defaults import *

urlpatterns = patterns('fbsample.fbapp.views',
    #(r'^$', 'canvas'),
    (r'^webapp/$', 'web_app'),
    (r'^formsubmit/$', 'form_submit'),
    (r'^test/$', 'test'),
    (r'^status/$', 'status'),
    # Define other pages you want to create here
)

