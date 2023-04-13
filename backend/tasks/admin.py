from django.contrib import admin

from .models import Task, Question, Coding

# Register your models here.

admin.site.register(Task)
admin.site.register(Question)
admin.site.register(Coding)