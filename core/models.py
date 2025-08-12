from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Organization(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name




class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('member', 'Member'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    def __str__(self): return f"{self.user.username} ({self.role})"




# Projects
class Project(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name



# Tasks
STATUS_CHOICES = (
    ('todo', 'To Do'),
    ('inprogress', 'In Progress'),
    ('done', 'Done'),
)

PRIORITY_CHOICES = (
    ('low', 'Low'),
    ('med', 'Medium'),
    ('high', 'High'),
)



class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='med')
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks_assigned')
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.title



class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Comment by {self.author} on {self.task}"



class ActivityLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    verb = models.CharField(max_length=255)  
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.verb} @ {self.created_at}"

 

@receiver(post_save, sender=User)  #decorator
def ensure_profile_exists(sender, instance, created):
    if created:
        Profile.objects.create(user=instance)