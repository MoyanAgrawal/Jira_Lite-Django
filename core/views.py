# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.views import View
from .models import Project, Task, Comment, Organization
from .forms import SignUpForm, ProjectForm, TaskForm, CommentForm
from .models import ActivityLog
from django.contrib.auth.views import LogoutView
from django.contrib.auth import logout




class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = [] 

    def test_func(self):
        profile = getattr(self.request.user, 'profile', None)
        if not profile:
            return False
        return profile.role in self.allowed_roles



# Signup
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            org_name = form.cleaned_data.get('organization_name')
            selected_org = form.cleaned_data.get('organization')

            user = form.save(commit=False)
            user.email = form.cleaned_data.get('email')
            user.save()

            profile = user.profile
            profile.role = role

            if role == 'admin':
                if not org_name:
                    form.add_error('organization_name', 'Organization name is required for Admin role.')
                    return render(request, 'registration/signup.html', {'form': form})
                org = Organization.objects.create(name=org_name)
                profile.organization = org
            else:
                if not selected_org:
                    form.add_error('organization', 'You must select an organization for Manager/Member roles.')
                    return render(request, 'registration/signup.html', {'form': form})
                profile.organization = selected_org

            profile.save()
            login(request, user)
            return redirect('project_list')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})





class LogoutGetView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.full_logout(request)

    def post(self, request, *args, **kwargs):
        return self.full_logout(request)

    def full_logout(self, request):
        
        request.session.flush()

        
        logout(request)

        
        response = super().get(request)
        for cookie in request.COOKIES:
            response.delete_cookie(cookie)
        return response
    




# Project list
class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'core/project_list.html'
    context_object_name = 'projects'
    def get_queryset(self):
        org = self.request.user.profile.organization
        return Project.objects.filter(organization=org)





class ProjectCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'core/project_form.html'
    allowed_roles = ['admin','manager']
    def form_valid(self, form):
        form.instance.organization = self.request.user.profile.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('project_list')






class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'core/project_detail.html'
    context_object_name = 'project'
    def get_queryset(self):
        return Project.objects.filter(organization=self.request.user.profile.organization)






# Task create (Managers/Admins)
class TaskCreateView(LoginRequiredMixin, RoleRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'
    allowed_roles = ['admin','manager']
    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs['project_pk'], organization=request.user.profile.organization)
        return super().dispatch(request, *args, **kwargs)
    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        ActivityLog.objects.create(task=self.object, actor=self.request.user, verb=f"Task created: {self.object.title}")
        return response
    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.project.pk})






# Task update (Managers or assigned user)
class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'
    def get_queryset(self):
        
        return Task.objects.filter(project__organization=self.request.user.profile.organization)
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        role = request.user.profile.role
        if role in ('admin','manager') or self.object.assignee == request.user:
            return super().dispatch(request, *args, **kwargs)
        return redirect('project_detail', pk=self.object.project.pk)
    def form_valid(self, form):
        
        original = Task.objects.get(pk=self.object.pk)
        response = super().form_valid(form)
        changes = []
        if original.status != self.object.status:
            changes.append(f"status {original.status} -> {self.object.status}")
        if original.assignee != self.object.assignee:
            changes.append(f"assignee {original.assignee} -> {self.object.assignee}")
        if changes:
            ActivityLog.objects.create(task=self.object, actor=self.request.user, verb="; ".join(changes))
        else:
            ActivityLog.objects.create(task=self.object, actor=self.request.user, verb="task updated")
        return response
    def get_success_url(self):
        return reverse_lazy('task_detail', kwargs={'pk': self.object.pk})






# Task details and comment post handling
class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'core/task_detail.html'
    context_object_name = 'task'
    def get_queryset(self):
        return Task.objects.filter(project__organization=self.request.user.profile.organization)
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['comment_form'] = CommentForm()
        ctx['activities'] = self.object.activities.order_by('-created_at')
        return ctx
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = self.object
            comment.author = request.user
            comment.save()
            ActivityLog.objects.create(task=self.object, actor=request.user, verb=f"commented: {comment.content[:60]}")
            return redirect('task_detail', pk=self.object.pk)
        return self.get(request, *args, **kwargs)





# Project delete (managers/admins)
class ProjectDeleteView(LoginRequiredMixin, RoleRequiredMixin, DeleteView):
    model = Project
    template_name = 'core/project_confirm_delete.html'
    allowed_roles = ['admin','manager']
    def get_queryset(self):
        return Project.objects.filter(organization=self.request.user.profile.organization)
    def get_success_url(self):
        return reverse_lazy('project_list')





# Project Edit (managers/admins)
class ProjectUpdateView(LoginRequiredMixin, RoleRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'core/project_form.html' 
    allowed_roles = ['admin', 'manager']

    def get_queryset(self):
        
        return Project.objects.filter(organization=self.request.user.profile.organization)

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})