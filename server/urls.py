from django.conf.urls import include, url

from django.contrib import admin
admin.autodiscover()

from website import views

urlpatterns = [
    url(r'^$', views.info, name='slack-info'),
    url(r'^auth', views.auth, name='slack-auth'),
    url(r'^command', views.command, name='slack-command'),
    url(r'^config', views.config, name='slack-config'),
    url(r'^button', views.button_callback, name='slack-button')
    url(r'^privacy', views.privacy, name='slack-privacy')
]
