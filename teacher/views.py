# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.core.exceptions import ObjectDoesNotExist
#from django.contrib.auth.models import Group
from teacher.models import Classroom
from student.models import Enroll
from account.models import Log, Message, MessagePoll, Profile
from student.models import Enroll, EnrollGroup, Assistant
from .forms import ClassroomForm, AnnounceForm
from django.http import JsonResponse
import StringIO
from datetime import datetime
import xlsxwriter
from django.utils.timezone import localtime
from django.utils import timezone
from django.http import HttpResponse


# 判斷是否為授課教師
def is_teacher(user, classroom_id):
    return user.groups.filter(name='teacher').exists() and Classroom.objects.filter(teacher_id=user.id, id=classroom_id).exists()

# 判斷是否開啟事件記錄
def is_event_open(request):
        enrolls = Enroll.objects.filter(student_id=request.user.id)
        for enroll in enrolls:
            classroom = Classroom.objects.get(id=enroll.classroom_id)
            if classroom.event_open:
                return True
        return False

# 判斷是否開啟課程事件記錄
def is_event_video_open(request):
        enrolls = Enroll.objects.filter(student_id=request.user.id)
        for enroll in enrolls:
            classroom = Classroom.objects.get(id=enroll.classroom_id)
            if classroom.event_video_open:
                return True
        return False
        
# 列出所有課程
class ClassroomListView(ListView):
    model = Classroom
    context_object_name = 'classrooms'
    paginate_by = 20
    def get_queryset(self):
        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看任課班級')
            log.save()        
        queryset = Classroom.objects.filter(teacher_id=self.request.user.id).order_by("-id")
        return queryset
        
#新增一個課程
class ClassroomCreateView(CreateView):
    model = Classroom
    form_class = ClassroomForm
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.save()
        # 將教師設為0號學生
        enroll = Enroll(classroom_id=self.object.id, student_id=self.request.user.id, seat=0)
        enroll.save()     
        # 記錄系統事件
        if is_event_open(self.request) :            
            log = Log(user_id=self.request.user.id, event=u'新增任課班級<'+self.object.name+'>')
            log.save()                
        return redirect("/teacher/classroom")        
        
# 修改選課密碼
def classroom_edit(request, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")
    classroom = Classroom.objects.get(id=classroom_id)
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom.name =form.cleaned_data['name']
            classroom.password = form.cleaned_data['password']
            classroom.save()
            # 記錄系統事件
            if is_event_open(request) :                
                log = Log(user_id=request.user.id, event=u'修改選課密碼<'+classroom.name+'>')
                log.save()                    
            return redirect('/teacher/classroom')
    else:
        form = ClassroomForm(instance=classroom)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))        
    
# 退選
def unenroll(request, enroll_id, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")    
    enroll = Enroll.objects.get(id=enroll_id)
    enroll.delete()
    classroom_name = Classroom.objects.get(id=classroom_id).name
    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'退選<'+classroom_name+'>')
        log.save()       
    return redirect('/student/classmate/'+classroom_id)  

# 列出所有公告
class AnnounceListView(ListView):
    model = Message
    context_object_name = 'messages'
    template_name = 'teacher/announce_list.html'    
    paginate_by = 20
    def get_queryset(self):

        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看班級公告')
            log.save()        
        queryset = Message.objects.filter(classroom_id=self.kwargs['classroom_id'], author_id=self.request.user.id).order_by("-id")
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceListView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	    

    # 限本班任課教師        
    def render_to_response(self, context):
        if not is_teacher(self.request.user, self.kwargs['classroom_id']):
            return redirect('/')
        return super(AnnounceListView, self).render_to_response(context)        
        
#新增一個公告
class AnnounceCreateView(CreateView):
    model = Message
    form_class = AnnounceForm
    template_name = 'teacher/announce_form.html'     
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.title = u"[公告]" + self.object.title
        self.object.author_id = self.request.user.id
        self.object.classroom_id = self.kwargs['classroom_id']
        self.object.save()
        self.object.url = "/teacher/announce/detail/" + str(self.object.id)
        self.object.save()
        # 班級學生訊息
        enrolls = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id'])
        for enroll in enrolls:
            messagepoll = MessagePoll(message_id=self.object.id, reader_id=enroll.student_id)
            messagepoll.save()
        # 記錄系統事件
        if is_event_open(self.request) :            
            log = Log(user_id=self.request.user.id, event=u'新增公告<'+self.object.title+'>')
            log.save()                
        return redirect("/teacher/announce/"+self.kwargs['classroom_id'])       
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceCreateView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	   
        
    # 限本班任課教師        
    def render_to_response(self, context):
        if not is_teacher(self.request.user, self.kwargs['classroom_id']):
            return redirect('/')
        return super(AnnounceCreateView, self).render_to_response(context)          
        
# 列出所有課程
class ClassroomListView(ListView):
    model = Classroom
    context_object_name = 'classrooms'
    paginate_by = 20
    def get_queryset(self):
        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看任課班級')
            log.save()        
        queryset = Classroom.objects.filter(teacher_id=self.request.user.id).order_by("-id")
        return queryset
        
#新增一個課程
class ClassroomCreateView(CreateView):
    model = Classroom
    form_class = ClassroomForm
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.save()
        # 將教師設為0號學生
        enroll = Enroll(classroom_id=self.object.id, student_id=self.request.user.id, seat=0)
        enroll.save()     
        # 記錄系統事件
        if is_event_open(self.request) :            
            log = Log(user_id=self.request.user.id, event=u'新增任課班級<'+self.object.name+'>')
            log.save()                
        return redirect("/teacher/classroom")        
        
# 修改選課密碼
def classroom_edit(request, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")
    classroom = Classroom.objects.get(id=classroom_id)
    if request.method == 'POST':
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom.name =form.cleaned_data['name']
            classroom.password = form.cleaned_data['password']
            classroom.save()
            # 記錄系統事件
            if is_event_open(request) :                
                log = Log(user_id=request.user.id, event=u'修改選課密碼<'+classroom.name+'>')
                log.save()                    
            return redirect('/teacher/classroom')
    else:
        form = ClassroomForm(instance=classroom)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))        
    
# 退選
def unenroll(request, enroll_id, classroom_id):
    # 限本班任課教師
    if not is_teacher(request.user, classroom_id):
        return redirect("homepage")    
    enroll = Enroll.objects.get(id=enroll_id)
    enroll.delete()
    classroom_name = Classroom.objects.get(id=classroom_id).name
    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'退選<'+classroom_name+'>')
        log.save()       
    return redirect('/student/classmate/'+classroom_id)  
  
# 公告
def announce_detail(request, message_id):
    message = Message.objects.get(id=message_id)
    classroom = Classroom.objects.get(id=message.classroom_id)
    
    announce_reads = []
    
    messagepolls = MessagePoll.objects.filter(message_id=message_id)
    for messagepoll in messagepolls:
        enroll = Enroll.objects.get(classroom_id=message.classroom_id, student_id=messagepoll.reader_id)
        announce_reads.append([enroll.seat, enroll.student.first_name, messagepoll])
    
    def getKey(custom):
        return custom[0]	
    announce_reads = sorted(announce_reads, key=getKey)
    
    if is_event_open(request) :            
        log = Log(user_id=request.user.id, event=u'查看公告<'+message.title+'>')
        log.save()  
    return render_to_response('teacher/announce_detail.html', {'message':message, 'classroom':classroom, 'announce_reads':announce_reads}, context_instance=RequestContext(request))
# 記錄系統事件
class EventListView(ListView):
    context_object_name = 'events'
    paginate_by = 50
    template_name = 'teacher/event_list.html'

    def get_queryset(self):    
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        # 記錄系統事件
        if is_event_open(self.request) :           
            log = Log(user_id=self.request.user.id, event=u'查看班級事件<'+classroom.name+'>')
            log.save()       
        enrolls = Enroll.objects.filter(classroom_id=self.kwargs['classroom_id']);
        users = []
        for enroll in enrolls:
            if enroll.seat > 0 :
                users.append(enroll.student_id)
        if self.kwargs['user_id'] == "0":
            if self.request.GET.get('q') != None:
                queryset = Log.objects.filter(user_id__in=users, event__icontains=self.request.GET.get('q')).order_by('-id')
            else :
                queryset = Log.objects.filter(user_id__in=users).order_by('-id')
        else :
            if self.request.GET.get('q') != None:
                queryset = Log.objects.filter(user_id=self.kwargs['user_id'],event__icontains=self.request.GET.get('q')).order_by('-id')
            else : 
                queryset = Log.objects.filter(user_id__in=users).order_by('-id')
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(EventListView, self).get_context_data(**kwargs)
        q = self.request.GET.get('q')
        context.update({'q': q})
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        context['classroom'] = classroom
        context['is_event_open'] = Classroom.objects.get(id=self.kwargs['classroom_id']).event_open
        context['is_event_video_open'] = Classroom.objects.get(id=self.kwargs['classroom_id']).event_video_open       
        return context		
def clear(request, classroom_id):
    Log.objects.all().delete()
    # 記錄系統事件
    if is_event_open(request) :       
        log = Log(user_id=request.user.id, event=u'清除所有事件')
        log.save()            
    return redirect("/account/event/0")
    
def event_excel(request, classroom_id):
    classroom = Classroom.objects.get(id=classroom_id)
    # 記錄系統事件
    if is_event_open(request) :       
        log = Log(user_id=request.user.id, event=u'下載事件到Excel')
        log.save()        
    output = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(output)    
    #workbook = xlsxwriter.Workbook('hello.xlsx')
    worksheet = workbook.add_worksheet()
    date_format = workbook.add_format({'num_format': 'dd/mm/yy hh:mm:ss'})
    enrolls = Enroll.objects.filter(classroom_id=classroom_id);
    users = []
    for enroll in enrolls:
        if enroll.seat > 0 :
            users.append(enroll.student_id)
    events = Log.objects.filter(user_id__in=users).order_by('-id')
    index = 1
    for event in events:
        if event.user_id > 0 :
            worksheet.write('A'+str(index), event.user.first_name)
        else: 
            worksheet.write('A'+str(index), u'匿名')
        worksheet.write('B'+str(index), event.event)
        worksheet.write('C'+str(index), str(localtime(event.publish)))
        index = index + 1

    workbook.close()
    # xlsx_data contains the Excel file
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Report-'+classroom.name+'-'+str(localtime(timezone.now()).date())+'.xlsx'
    xlsx_data = output.getvalue()
    response.write(xlsx_data)
    return response

def event_make(request):
    action = request.POST.get('action')
    classroom_id = request.POST.get('classroomid')    
    if classroom_id and action :
            classroom = Classroom.objects.get(id=classroom_id)
            if action == 'open':
                classroom.event_open = True
            else :
                classroom.event_open = False
            classroom.save()
            return JsonResponse({'status':'ok'}, safe=False)
    else:
            return JsonResponse({'status':'ko'}, safe=False)
     
def event_video_make(request):
    action = request.POST.get('action')
    classroom_id = request.POST.get('classroomid')      
    if classroom_id and action :
            classroom = Classroom.objects.get(id=classroom_id)
            if action == 'open':
                classroom.event_video_open = True
            else :
                classroom.event_video_open = False
            classroom.save()
            return JsonResponse({'status':'ok'}, safe=False)
    else:
            return JsonResponse({'status':'ko'}, safe=False)

		