# core/urls.py
from django.urls import path
from core import views as core_views 
from . import views

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),


    path('projects/<int:project_pk>/tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/<int:pk>/e dit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('accounts/logout/', core_views.LogoutGetView.as_view(), name='logout'),
]
