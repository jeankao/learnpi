# -*- coding: UTF-8 -*-
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.models import User
from django.template import RequestContext
from django.views.generic import ListView, CreateView
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group
from teacher.models import Classroom, TWork
from student.models import Enroll, EnrollGroup, Assistant, SWork
from account.models import Log, Message, MessagePoll, Profile, VisitorLog
from student.forms import EnrollForm, GroupForm, SeatForm, GroupSizeForm, SubmitForm
from django.utils import timezone
from django.core.files import File 
import cStringIO as StringIO
from PIL import Image,ImageDraw,ImageFont
from binascii import a2b_base64
import os

# 判斷是否為授課教師
def is_teacher(user, classroom_id):
    return  user.groups.filter(name='teacher').exists() and Classroom.objects.filter(teacher_id=user.id, id=classroom_id).exists()

# 判斷是否開啟事件記錄
def is_event_open(request):
        enrolls = Enroll.objects.filter(student_id=request.user.id)
        for enroll in enrolls:
            classroom = Classroom.objects.get(id=enroll.classroom_id)
            if classroom.event_open:
                return True
        return False

# 查看班級學生
def classmate(request, classroom_id):
        enrolls = Enroll.objects.filter(classroom_id=classroom_id).order_by("seat")
        enroll_group = []
        classroom_name=Classroom.objects.get(id=classroom_id).name
        for enroll in enrolls:
            login_times = len(VisitorLog.objects.filter(user_id=enroll.student_id))
            if enroll.group > 0 :
                enroll_group.append([enroll, EnrollGroup.objects.get(id=enroll.group).name, login_times])
            else :
                enroll_group.append([enroll, "沒有組別", login_times])
        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看班級學生<'+classroom_name+'>')
            log.save()                        
        return render_to_response('student/classmate.html', {'classroom_name':classroom_name, 'enroll_group':enroll_group}, context_instance=RequestContext(request))

# 顯示所有組別
def group(request, classroom_id):
        student_groups = []
        classroom = Classroom.objects.get(id=classroom_id)
        group_open = Classroom.objects.get(id=classroom_id).group_open        
        groups = EnrollGroup.objects.filter(classroom_id=classroom_id)
        try:
                student_group = Enroll.objects.get(student_id=request.user.id, classroom_id=classroom_id).group
        except ObjectDoesNotExist :
                student_group = []		
        for group in groups:
            enrolls = Enroll.objects.filter(classroom_id=classroom_id, group=group.id)
            student_groups.append([group, enrolls, classroom.group_size-len(enrolls)])
            
        #找出尚未分組的學生
        def getKey(custom):
            return custom.seat	
        enrolls = Enroll.objects.filter(classroom_id=classroom_id)
        nogroup = []
        for enroll in enrolls:
            if enroll.group == 0 :
		        nogroup.append(enroll)		
	    nogroup = sorted(nogroup, key=getKey)

        # 記錄系統事件
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'查看分組<'+classroom.name+'>')
            log.save()        
        return render_to_response('student/group.html', {'nogroup': nogroup, 'group_open': group_open, 'student_groups':student_groups, 'classroom':classroom, 'student_group':student_group, 'teacher': is_teacher(request.user, classroom_id)}, context_instance=RequestContext(request))

# 新增組別
def group_add(request, classroom_id):
        if request.method == 'POST':
            classroom_name = Classroom.objects.get(id=classroom_id).name            
            form = GroupForm(request.POST)
            if form.is_valid():
                group = EnrollGroup(name=form.cleaned_data['name'],classroom_id=int(classroom_id))
                group.save()
                
                # 記錄系統事
                if is_event_open(request) :                  
                    log = Log(user_id=request.user.id, event=u'新增分組<'+classroom_name+'><'+form.cleaned_data['name']+'>')
                    log.save()        
        
                return redirect('/student/group/'+classroom_id)
        else:
            form = GroupForm()
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))
        
# 設定組別人數
def group_size(request, classroom_id):
        if request.method == 'POST':
            form = GroupSizeForm(request.POST)
            if form.is_valid():
                classroom = Classroom.objects.get(id=classroom_id)
                classroom.group_size = form.cleaned_data['group_size']
                classroom.save()
                
                # 記錄系統事
                if is_event_open(request) :                  
                    log = Log(user_id=request.user.id, event=u'設定組別人數<'+classroom.name+'><'+str(form.cleaned_data['group_size'])+'>')
                    log.save()        
        
                return redirect('/student/group/'+classroom_id)
        else:
            classroom = Classroom.objects.get(id=classroom_id)
            form = GroupSizeForm(instance=classroom)
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))        

# 加入組別
def group_enroll(request, classroom_id,  group_id):
        classroom = Classroom.objects.get(id=classroom_id)
        members = Enroll.objects.filter(group=group_id)
        if len(members) < classroom.group_size:
            group_name = EnrollGroup.objects.get(id=group_id).name
            enroll = Enroll.objects.filter(student_id=request.user.id, classroom_id=classroom_id)
            enroll.update(group=group_id)
            # 記錄系統事件 
            if is_event_open(request) :          
                log = Log(user_id=request.user.id, event=u'加入組別<'+classroom.name+'><'+group_name+'>')
                log.save()         
        return redirect('/student/group/'+classroom_id)

# 刪除組別
def group_delete(request, group_id, classroom_id):
    group = EnrollGroup.objects.get(id=group_id)
    group.delete()
    classroom_name = Classroom.objects.get(id=classroom_id).name

    # 記錄系統事件 
    if is_event_open(request) :      
        log = Log(user_id=request.user.id, event=u'刪除組別<'+classroom_name+'><'+group.name+'>')
        log.save()       
    return redirect('/student/group/'+classroom_id)  
    
# 是否開放選組
def group_open(request, classroom_id, action):
    classroom = Classroom.objects.get(id=classroom_id)
    if action == "1":
        classroom.group_open=True
        classroom.save()
        # 記錄系統事件 
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'開放選組<'+classroom.name+'>')
            log.save()            
    else :
        classroom.group_open=False
        classroom.save()
        # 記錄系統事件 
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event=u'關閉選組<'+classroom.name+'>')
            log.save()                
    return redirect('/student/group/'+classroom_id)  	
	
# 列出選修的班級
def classroom(request):
        enrolls = Enroll.objects.filter(student_id=request.user.id).order_by("-id")
        # 記錄系統事件 
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event='查看選修班級')
            log.save()          
        return render_to_response('student/classroom.html',{'enrolls': enrolls}, context_instance=RequestContext(request))    
    
# 查看可加入的班級
def classroom_add(request):
        classrooms = Classroom.objects.all().order_by('-id')
        classroom_teachers = []
        for classroom in classrooms:
            enroll = Enroll.objects.filter(student_id=request.user.id, classroom_id=classroom.id)
            if enroll.exists():
                classroom_teachers.append([classroom,classroom.teacher.first_name,1])
            else:
                classroom_teachers.append([classroom,classroom.teacher.first_name,0])   
        # 記錄系統事件 
        if is_event_open(request) :          
            log = Log(user_id=request.user.id, event='查看可加入的班級')
            log.save() 
        return render_to_response('student/classroom_add.html', {'classroom_teachers':classroom_teachers}, context_instance=RequestContext(request))
    
# 加入班級
def classroom_enroll(request, classroom_id):
        scores = []
        if request.method == 'POST':
                form = EnrollForm(request.POST)
                if form.is_valid():
                    try:
                        classroom = Classroom.objects.get(id=classroom_id)
                        if classroom.password == form.cleaned_data['password']:
                                enroll = Enroll(classroom_id=classroom_id, student_id=request.user.id, seat=form.cleaned_data['seat'])
                                enroll.save()
                                # 記錄系統事件 
                                if is_event_open(request) :  
                                    log = Log(user_id=request.user.id, event=u'加入班級<'+classroom.name+'>')
                                    log.save()                                 
                        else:
                                return render_to_response('message.html', {'message':"選課密碼錯誤"}, context_instance=RequestContext(request))
                      
                    except Classroom.DoesNotExist:
                        pass
                    
                    
                    return redirect("/student/group/" + str(classroom.id))
        else:
            form = EnrollForm()
        return render_to_response('form.html', {'form':form}, context_instance=RequestContext(request))
        
# 修改座號
def seat_edit(request, enroll_id, classroom_id):
    enroll = Enroll.objects.get(id=enroll_id)
    if request.method == 'POST':
        form = SeatForm(request.POST)
        if form.is_valid():
            enroll.seat =form.cleaned_data['seat']
            enroll.save()
            classroom_name = Classroom.objects.get(id=classroom_id).name
            # 記錄系統事件 
            if is_event_open(request) :              
                log = Log(user_id=request.user.id, event=u'修改座號<'+classroom_name+'>')
                log.save() 
            return redirect('/student/classroom')
    else:
        form = SeatForm(instance=enroll)

    return render_to_response('form.html',{'form': form}, context_instance=RequestContext(request))  

# 登入記錄
class LoginLogListView(ListView):
    context_object_name = 'visitorlogs'
    paginate_by = 20
    template_name = 'student/login_log.html'
    def get_queryset(self):
        visitorlogs = VisitorLog.objects.filter(user_id=self.kwargs['user_id']).order_by("-id")
        # 記錄系統事件
        if is_event_open(self.request) :          
            user = User.objects.get(id=self.kwargs['user_id'])
            log = Log(user_id=self.request.user.id, event=u'查看登入記錄<'+user.first_name+'>')
            log.save()          
        return visitorlogs
        
    def get_context_data(self, **kwargs):
        context = super(LoginLogListView, self).get_context_data(**kwargs)
        if self.request.GET.get('page') :
            context['page'] = int(self.request.GET.get('page')) * 20 - 20
        else :
            context['page'] = 0
        return context        

# 列出所有公告
class AnnounceListView(ListView):
    model = Message
    context_object_name = 'messages'
    template_name = 'student/announce_list.html'    
    paginate_by = 20
    
    def get_queryset(self):
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看班級公告')
            log.save()        
        messages = Message.objects.filter(classroom_id=self.kwargs['classroom_id'], author_id=classroom.teacher_id).order_by("-id")
        queryset = []
        for message in messages:
            messagepoll = MessagePoll.objects.get(message_id=message.id, reader_id=self.request.user.id)
            queryset.append([messagepoll, message])
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(AnnounceListView, self).get_context_data(**kwargs)
        context['classroom'] = Classroom.objects.get(id=self.kwargs['classroom_id'])
        return context	    

    # 限本班同學
    def render_to_response(self, context):
        try:
            enroll = Enroll.objects.get(student_id=self.request.user.id, classroom_id=self.kwargs['classroom_id'])
        except ObjectDoesNotExist :
            return redirect('/')
        return super(AnnounceListView, self).render_to_response(context)    
      
# 列出所有作業
class WorkListView(ListView):
    model = TWork
    context_object_name = 'works'
    template_name = 'student/work_list.html'    
    paginate_by = 20
    
    def get_queryset(self):
        classroom = Classroom.objects.get(id=self.kwargs['classroom_id'])
        # 記錄系統事件
        if is_event_open(self.request) :    
            log = Log(user_id=self.request.user.id, event='查看班級作業')
            log.save()        
        queryset = TWork.objects.filter(classroom_id=self.kwargs['classroom_id']).order_by("-id")
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super(WorkListView, self).get_context_data(**kwargs)
        context['classroom_id'] = self.kwargs['classroom_id']
        return context	    

    # 限本班同學
    def render_to_response(self, context):
        try:
            enroll = Enroll.objects.get(student_id=self.request.user.id, classroom_id=self.kwargs['classroom_id'])
        except ObjectDoesNotExist :
            return redirect('/')
        return super(WorkListView, self).render_to_response(context)    
			
def submit(request, index):
        scores = []
        if request.method == 'POST':
            form = SubmitForm(request.POST, request.FILES)
            if form.is_valid():						
                try: 
                    work = SWork.objects.get(index=index, student_id=request.user.id)				
                except ObjectDoesNotExist:
                    work = SWork(index=index, student_id=request.user.id)		
                work.save()					
                dataURI = form.cleaned_data['screenshot']
                head, data = dataURI.split(',', 1)
                mime, b64 = head.split(';', 1)
                mtype, fext = mime.split('/', 1)
                binary_data = a2b_base64(data)
                directory = "static/pic/{uid}/{id}".format(uid=request.user.id, id=work.id)
                image_file = "static/pic/{uid}/{id}/{filename}.jpg".format(uid=request.user.id, id=work.id, filename='run')
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(image_file, 'wb') as fd:
                    fd.write(binary_data)
                    fd.close()
                work.code=form.cleaned_data['code']
                work.picture=image_file
                work.memo=form.cleaned_data['memo']
                work.save()
                # 記錄系統事件 
                if is_event_open(request) :                      
                    log = Log(user_id=request.user.id, event=u'新增作業成功<'.encode("UTF-8")+index.encode("UTF-8")+'>')
                    log.save() 
                return redirect("/student/work/show/"+index)
            else:
                return render_to_response('student/submit.html', {'error':form.errors}, context_instance=RequestContext(request))
        else:
            form = SubmitForm()
        return render_to_response('student/submit.html', {'form':form, 'scores':scores, 'index':index}, context_instance=RequestContext(request))

def show(request, index):
        work = SWork.objects.get(index=index, student_id=request.user.id)
        return render_to_response('student/show.html', {'work':work}, context_instance=RequestContext(request))

      
# 查詢某作業所有同學心得
def memo(request, classroom_id, index):
    enrolls = Enroll.objects.filter(classroom_id=classroom_id)
    datas = []
    for enroll in enrolls:
        try:
            work = SWork.objects.get(index=index, student_id=enroll.student_id)
            datas.append([enroll.seat, enroll.student.first_name, work.memo])
        except ObjectDoesNotExist:
            datas.append([enroll.seat, enroll.student.first_name, ""])
    def getKey(custom):
        return custom[0]
    datas = sorted(datas, key=getKey)	
    # 記錄系統事件
    if is_event_open(request) :      
        log = Log(user_id=request.user.id, event=u'查看某作業所有同學心得<'+index+'>')
        log.save()    
    return render_to_response('student/memo.html', {'datas': datas}, context_instance=RequestContext(request))
