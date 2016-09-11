# -*- coding: UTF-8 -*-
from django.db import models
from django.contrib.auth.models import User
from teacher.models import Classroom
from django.utils import timezone

def upload_path_handler(instance, filename):
    return "static/certificate/0/{filename}".format(filename=instance.id+".jpg")

# 學生選課資料
class Enroll(models.Model):
    # 學生序號
    student_id = models.IntegerField(default=0)
    # 班級序號
    classroom_id = models.IntegerField(default=0)
    # 座號
    seat = models.IntegerField(default=0)
    # 組別
    group = models.IntegerField(default=0)
    # 創意秀組別
    group_show = models.IntegerField(default=0)
    # 12堂課證書
    certificate1 = models.BooleanField(default=False)
    certificate1_date = models.DateTimeField(default=timezone.now)
    # 實戰入門證書
    certificate2 = models.BooleanField(default=False) 
    certificate2_date = models.DateTimeField(default=timezone.now)	
    # 實戰進擊證書
    certificate3 = models.BooleanField(default=False)
    certificate3_date = models.DateTimeField(default=timezone.now)
    # 實戰高手證書
    certificate4 = models.BooleanField(default=False)
    certificate4_date = models.DateTimeField(default=timezone.now)
    # 12堂課 成績
    score_memo1 = models.IntegerField(default=0)
    # 實戰入門成績
    score_memo2 = models.IntegerField(default=0)
    # 實戰進擊成績
    score_memo3 = models.IntegerField(default=0)
    # 實戰高手成績
    score_memo4 = models.IntegerField(default=0)
	
    @property
    def classroom(self):
        return Classroom.objects.get(id=self.classroom_id)  

    @property        
    def student(self):
        return User.objects.get(id=self.student_id)      

    def __str__(self):
        return str(self.id)    

    class Meta:
        unique_together = ('student_id', 'classroom_id',)		
    
# 學生組別    
class EnrollGroup(models.Model):
    name = models.CharField(max_length=30)
    classroom_id = models.IntegerField(default=0)
    
class Work(models.Model):
    user_id = models.IntegerField(default=0) 
    index = models.IntegerField()
    number = models.CharField(max_length=30, unique=True)
    memo = models.TextField()
    publication_date = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=-1)
    scorer = models.IntegerField(default=0)
    
    def __unicode__(self):
        user = User.objects.filter(id=self.user_id)[0]
        index = self.index
        return user.first_name+"("+str(index)+")"

# 小老師        
class Assistant(models.Model):
    student_id = models.IntegerField(default=0)
    classroom_id = models.IntegerField(default=0)
    lesson = models.IntegerField(default=0)
    
    @property        
    def student(self):
        return User.objects.get(id=self.student_id)   

def upload_path_handler(instance, filename):
    return "static/pic/{id}/{filename}.jpg".format(id=instance.id, filename='run')	
			
#作業
class SWork(models.Model):
    student_id = models.IntegerField(default=0)
    index = models.IntegerField()
    picture = models.ImageField(upload_to = upload_path_handler, default = '/static/pic/null.jpg')
    memo = models.TextField(default='')
    code = models.TextField(default='')		
    publication_date = models.DateTimeField(default=timezone.now)
    score = models.IntegerField(default=-1)
    scorer = models.IntegerField(default=0)
		
    def __unicode__(self):
        user = User.objects.filter(id=self.student_id)[0]
        index = self.index
        return user.first_name+"("+str(index)+")"		