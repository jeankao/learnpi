# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.core.exceptions import ObjectDoesNotExist
#from django.contrib.auth.models import Group
from teacher.models import Classroom, TWork
from student.models import Enroll
from account.models import Log, Message, MessagePoll, Profile, PointHistory
from student.models import Enroll, EnrollGroup, Assistant, SWork
from .forms import ClassroomForm, AnnounceForm, WorkForm, ScoreForm
from django.http import JsonResponse
import StringIO
from datetime import datetime
import xlsxwriter
from django.utils.timezone import localtime
from django.utils import timezone
from django.http import HttpResponse
from account.avatar import *


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

# 列出所有課程
class WorkListView(ListView):
    model = TWork
    context_object_name = 'works'
    paginate_by = 20
    def get_queryset(self):
        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看作業列表')
            log.save()        
        queryset = TWork.objects.filter(teacher_id=self.request.user.id, classroom_id=self.kwargs['classroom_id']).order_by("-id")
        return queryset
			
    def get_context_data(self, **kwargs):
        context = super(WorkListView, self).get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        return context	
        
#新增一個課程
class WorkCreateView(CreateView):
    model = TWork
    form_class = WorkForm
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.teacher_id = self.request.user.id
        self.object.classroom_id = self.kwargs['classroom_id']
        self.object.save()  
        # 記錄系統事件
        if is_event_open(self.request) :            
            log = Log(user_id=self.request.user.id, event=u'新增作業<'+self.object.title+'>')
            log.save()                
        return redirect("/teacher/work/"+self.kwargs['classroom_id'])        
        
# 修改選課密碼
def work_edit(request, classroom_id):
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
    			
# 列出某作業所有同學名單
def work_class(request, classroom_id, work_id):
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    classroom_name = Classroom.objects.get(id=classroom_id).name
    classmate_work = []
    scorer_name = ""
    for enroll in enrolls:
        try:    
            work = SWork.objects.get(student_id=enroll.student_id, index=work_id)
            if work.scorer > 0 :
                scorer = User.objects.get(id=work.scorer)
                scorer_name = scorer.first_name
            else :
                scorer_name = "1"
        except ObjectDoesNotExist:
            work = SWork(index=work_id, student_id=1)
        try:
            group_name = EnrollGroup.objects.get(id=enroll.group).name
        except ObjectDoesNotExist:
            group_name = "沒有組別"
        assistant = Assistant.objects.filter(classroom_id=classroom_id, student_id=enroll.student_id, lesson=work_id)
        if assistant.exists():
            classmate_work.append([enroll,work,1, scorer_name, group_name])
        else :
            classmate_work.append([enroll,work,0, scorer_name, group_name])   
    def getKey(custom):
        return custom[0].seat
	
    classmate_work = sorted(classmate_work, key=getKey)
    
    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'列出某作業所有同學名單<'+classroom_name+'><'+work_id+'>')
        log.save()          
    return render_to_response('teacher/work_class.html',{'classmate_work': classmate_work, 'classroom_id':classroom_id, 'index': work_id}, context_instance=RequestContext(request))
	
	# 教師評分
def scoring(request, classroom_id, user_id, index):
    user = User.objects.get(id=user_id)
    enroll = Enroll.objects.get(classroom_id=classroom_id, student_id=user_id)
    try:
        assistant = Assistant.objects.filter(classroom_id=classroom_id,lesson=index,student_id=request.user.id)
    except ObjectDoesNotExist:            
        if not is_teacher(request.user, classroom_id):
            return render_to_response('message.html', {'message':"您沒有權限"}, context_instance=RequestContext(request))
        
    try:
        work3 = SWork.objects.get(student_id=user_id, index=index)
    except ObjectDoesNotExist:
        work3 = SWork(index=index, student_id=user_id)
        
    if request.method == 'POST':
        form = ScoreForm(request.user, request.POST)
        if form.is_valid():
            work = SWork.objects.filter(index=index, student_id=user_id)
            if not work.exists():
                work = SWork(index=index, student_id=user_id, score=form.cleaned_data['score'], publication_date=timezone.now())
                work.save()
                # 記錄系統事件
                if is_event_open() :            
                    log = Log(user_id=request.user.id, event=u'新增評分<'+user.first_name+'><'+work.score+'分>')
                    log.save()                      
            else:
                if work[0].score < 0 :   
                    # 小老師
                    if not is_teacher(request.user, classroom_id):
    	                # credit
                        update_avatar(request.user.id, 2, 1)
                        # History
                        history = PointHistory(user_id=request.user.id, kind=2, message='1分--小老師:<'+index.encode('utf-8')+'><'+enroll.student.first_name.encode('utf-8')+'>', url=request.get_full_path())
                        history.save()				
    
				    # credit
                    update_avatar(enroll.student_id, 1, 1)
                    # History
                    history = PointHistory(user_id=user_id, kind=1, message='1分--作業受評<'+index.encode('utf-8')+'><'+request.user.first_name.encode('utf-8')+'>', url=request.get_full_path())
                    history.save()		                        
                
                work.update(score=form.cleaned_data['score'])
                work.update(scorer=request.user.id)
                # 記錄系統事件
                if is_event_open(request) :                   
                    log = Log(user_id=request.user.id, event=u'更新評分<'+user.first_name+u'><'+str(work[0].score)+u'分>')
                    log.save()                    
						
            if is_teacher(request.user, classroom_id):         
                if form.cleaned_data['assistant']:
                    try :
					    assistant = Assistant.objects.get(student_id=user_id, classroom_id=classroom_id, lesson=index)
                    except ObjectDoesNotExist:
                        assistant = Assistant(student_id=user_id, classroom_id=classroom_id, lesson=index)
                        assistant.save()	
                        
                    # create Message
                    title = "<" + assistant.student.first_name.encode("utf-8") + u">擔任小老師<".encode("utf-8") + index.encode('utf-8') + ">"
                    url = "/teacher/score_peer/" + str(index) + "/" + classroom_id + "/" + str(enroll.group) 
                    message = Message.create(title=title, url=url, time=timezone.now())
                    message.save()                        
                    
                    group = Enroll.objects.get(classroom_id=classroom_id, student_id=assistant.student_id).group
                    if group > 0 :
                        enrolls = Enroll.objects.filter(group = group)
                        for enroll in enrolls:
                            # message for group member
                            messagepoll = MessagePoll.create(message_id = message.id,reader_id=enroll.student_id)
                            messagepoll.save()
                    
                return redirect('/teacher/work/class/'+classroom_id+'/'+index)
            else: 
                return redirect('/teacher/score_peer/'+index+'/'+classroom_id+'/'+str(enroll.group))

    else:
        work = SWork.objects.filter(index=index, student_id=user_id)
        if not work.exists():
            form = ScoreForm(user=request.user)
        else:
            form = ScoreForm(instance=work[0], user=request.user)
    return render_to_response('teacher/scoring.html', {'form': form,'work':work3, 'student':user, 'classroom_id':classroom_id}, context_instance=RequestContext(request))

# 小老師評分名單
def score_peer(request, index, classroom_id, group):
    try:
        assistant = Assistant.objects.get(lesson=index, classroom_id=classroom_id, student_id=request.user.id)
    except ObjectDoesNotExist:
        return redirect("/student/group/work/"+index+"/"+classroom_id)

    enrolls = Enroll.objects.filter(classroom_id=classroom_id, group=group)
    lesson = ""
    classmate_work = []
    for enroll in enrolls:
        if not enroll.student_id == request.user.id : 
            scorer_name = ""
            try:    
                work = Work.objects.get(user_id=enroll.student.id, index=index)
                if work.scorer > 0 :
                    scorer = User.objects.get(id=work.scorer)
                    scorer_name = scorer.first_name
            except ObjectDoesNotExist:
                work = Work(index=index, user_id=1, number="0")        
            classmate_work.append([enroll.student,work,1, scorer_name])
        lesson = lesson_list[int(index)-1]
    # 記錄系統事件
    if is_event_open(request) :        
        log = Log(user_id=request.user.id, event=u'小老師評分名單<'+index+'><'+group+'>')
        log.save()    
    return render_to_response('teacher/score_peer.html',{'enrolls':enrolls, 'classmate_work': classmate_work, 'classroom_id':classroom_id, 'lesson':lesson, 'index': index}, context_instance=RequestContext(request))
