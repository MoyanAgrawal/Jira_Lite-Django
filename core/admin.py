from django.contrib import admin
from .models import Organization, Profile, Project, Task, Comment, ActivityLog

admin.site.register(Organization)
admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(ActivityLog)