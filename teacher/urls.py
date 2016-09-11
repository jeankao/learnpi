# -*- coding: UTF-8 -*-
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views
from teacher.views import ClassroomListView, ClassroomCreateView, AnnounceListView, AnnounceCreateView, WorkListView, WorkCreateView

urlpatterns = [
    url(r'^classroom/$', login_required(ClassroomListView.as_view()), name='classroom-list'),
    url(r'^classroom/add/$', login_required(ClassroomCreateView.as_view()), name='classroom-add'),
    url(r'^classroom/edit/(?P<classroom_id>\d+)/$', views.classroom_edit, name='classroom-edit'),
    # 退選
    url(r'^unenroll/(?P<enroll_id>\d+)/(?P<classroom_id>\d+)/$', views.unenroll),  	  
    #公告
    url(r'^announce/(?P<classroom_id>\d+)/$', login_required(AnnounceListView.as_view()), name='announce-list'),
    url(r'^announce/add/(?P<classroom_id>\d+)/$', login_required(AnnounceCreateView.as_view()), name='announce-add'),  
    url(r'^announce/detail/(?P<message_id>\d+)/$', views.announce_detail),
    #系統事件記錄
    url(r'^event/(?P<classroom_id>\d+)/(?P<user_id>\d+)/$', views.EventListView.as_view()),
    url(r'^event/clear/(?P<classroom_id>\d+)/$', views.clear),
    url(r'^event/excel/(?P<classroom_id>\d+)/$', views.event_excel),
    url(r'^event/make/$', views.event_make),    
    url(r'^event/video/make/$', views.event_video_make),
    # 作業
    url(r'^work/(?P<classroom_id>\d+)/$', login_required(WorkListView.as_view()), name='work-list'),
    url(r'^work/add/(?P<classroom_id>\d+)/$', login_required(WorkCreateView.as_view()), name='work-add'),
    url(r'^work/edit/(?P<classroom_id>\d+)/$', views.work_edit, name='work-edit'),  
]