from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Task
from .serializers import TaskSerializer


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    

# def index(request):
#     tasks = Task.objects.all()
#     return render(request, 'tasks/index.html', {'tasks': tasks})


# def edit(request, id):
#     task = Task.objects.get(pk=id)
#     if request.method == 'POST':
#         task.source = request.POST['source']
#         task.save()

#     return render(request, 'tasks/edit.html', {'task': task})
