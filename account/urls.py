# -*- coding: UTF-8 -*-
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$',  views.MessageListView.as_view(), name='dashboard'),  
    #登入
    url(r'^login/$', views.user_login, name='login'),
    #登出
    url(r'^logout/$',auth_views.logout),  
  
    #列出所有帳號
    url(r'^userlist/$', views.UserListView.as_view()),      
    #註冊帳號
    url(r'^register/$', views.register, name='register'),    
    #設定教師
    url(r'^teacher/make/$', views.make, name='make'),      
    # 讀取訊息
    url(r'^message/(?P<messagepoll_id>\d+)/$', views.message),
    # 私訊
    url(r'^line/(?P<classroom_id>\d+)/$', views.LineListView.as_view()),    
    url(r'^line/class/(?P<classroom_id>\d+)/$', views.LineClassListView.as_view()),        
    url(r'^line/add/(?P<classroom_id>\d+)/(?P<user_id>\d+)/$', views.LineCreateView.as_view()),
    url(r'^line/detail/(?P<message_id>\d+)/$', views.line_detail),
    #訪客
    url(r'^visitor/$', views.VisitorListView.as_view()),    
    url(r'^visitorlog/(?P<visitor_id>\d+)/$', views.VisitorLogListView.as_view()),
    #修改密碼
    url(r'^password-change/$', auth_views.password_change, name='password_change'),
    url(r'^password-change/done/$', auth_views.password_change_done, name='password_change_done'),    
    url(r'^password/(?P<user_id>\d+)/$', views.password),
    #系統事件記錄
    url(r'^event/(?P<user_id>\d+)/$', views.EventListView.as_view()),
    url(r'^event/admin/$', views.EventAdminListView.as_view()),
    url(r'^event/admin/classroom/(?P<classroom_id>\d+)/$', views.EventAdminClassroomListView.as_view()),  
    #修改真實姓名
    url(r'^realname/(?P<user_id>\d+)/$', views.adminrealname),    
    url(r'^realname/$', views.realname, name='realname'), 
    #修改學校
    url(r'^school/$', views.adminschool),     
    #修改信箱
    url(r'^email/$', views.adminemail),      
]
