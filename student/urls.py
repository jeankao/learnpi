# -*- coding: UTF-8 -*-
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from . import views
from student.views import AnnounceListView, WorkListView

urlpatterns = [
    # 選課
    url(r'^classroom/enroll/(?P<classroom_id>[^/]+)/$', views.classroom_enroll),      
    url(r'^classroom/add/$', views.classroom_add),  
    url(r'^classroom/$', views.classroom),
   	url(r'^classroom/seat/(?P<enroll_id>\d+)/(?P<classroom_id>\d+)/$', views.seat_edit, name='seat_edit'),
    # 同學
    url(r'^classmate/(?P<classroom_id>\d+)/$', views.classmate), 
    url(r'^loginlog/(?P<user_id>\d+)/$', views.LoginLogListView.as_view()),     
    # 分組
    url(r'^group/enroll/(?P<classroom_id>[^/]+)/(?P<group_id>[^/]+)/$', views.group_enroll),    
    url(r'^group/add/(?P<classroom_id>[^/]+)/$', views.group_add),     
    url(r'^group/(?P<classroom_id>[^/]+)/$', views.group),   
    url(r'^group/size/(?P<classroom_id>[^/]+)/$', views.group_size),      
    url(r'^group/open/(?P<classroom_id>[^/]+)/(?P<action>[^/]+)/$', views.group_open),     
  	url(r'^group/delete/(?P<group_id>[^/]+)/(?P<classroom_id>[^/]+)/$', views.group_delete),
    #公告
    url(r'^announce/(?P<classroom_id>\d+)/$', login_required(AnnounceListView.as_view()), name='announce-list'),
    #作業
    url(r'^work/(?P<classroom_id>\d+)/$', login_required(WorkListView.as_view()), name='work-list'),  
    url(r'^work/submit/(?P<index>\d+)/$', views.submit),    
    url(r'^work/show/(?P<index>\d+)/$', views.show),      
    url(r'^work/memo/(?P<classroom_id>\d+)/(?P<index>\d+)/$', views.memo), 
    # 課程  
    url(r'^lesson/(?P<lesson>[^/]+)/$', views.lesson),    
    url(r'^lessons/(?P<unit>[^/]+)/$', views.lessons),   
    #url(r'^lesson/log/(?P<lesson>[^/]+)/$', views.lesson_log), 
]