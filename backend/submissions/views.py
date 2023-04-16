from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveAPIView, ListCreateAPIView

import subprocess

from .models import Submission, Language
from .serializers import CreateSubmissionSerializer,  RetrieveSubmissionSerializer, LanguageSerializer

def sandbox(request):
    return HttpResponse(subprocess.check_output(['isolate','--version']), content_type="text/plain")


class LanguageList(ListAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    

class CreateSubmission(ListCreateAPIView):
    queryset = Submission.objects.all()
    serializer_class = CreateSubmissionSerializer
    

class RetrieveSubmission(RetrieveAPIView):
    queryset = Submission.objects.all()
    serializer_class = RetrieveSubmissionSerializer
    
    def get_object(self):
        if 'pk' in self.kwargs:
            self.lookup_field = 'pk'
        elif 'token' in self.kwargs:
            self.lookup_field = 'token'

        return super().get_object()
    
