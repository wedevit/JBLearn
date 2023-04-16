from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

# router = DefaultRouter()
# router.register('', views.TaskViewSet)

# urlpatterns = router.urls

urlpatterns = [
    path('', views.CreateSubmission.as_view(), name='create_submission'),
    path('<uuid:token>', views.RetrieveSubmission.as_view(), name='retrieve_submission'),
    path('languages', views.LanguageList.as_view(), name='language_list'),
    path('sandbox', views.sandbox, name='sandbox'),
]