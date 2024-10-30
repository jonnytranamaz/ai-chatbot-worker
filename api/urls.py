from django.urls import include, path
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.urlpatterns import format_suffix_patterns
from api.views import *


urlpatterns = [
    path('models/get-latest-model/', views.get_latest_model, name='get-latest-model'),
    path('models/train-model/', views.train_model, name='train-model'),
    path('convertdata/', ConvertData.as_view(), name='convertdata'),
    path('models/replace-model-of-rasa/', views.replace_model_of_rasa , name='replace-model-of-rasa'),
    path('models/auto-deploy/', views.convert_data_and_train_and_replace_model, name='convert_data_and_train_and_replace_model'),
]


urlpatterns = format_suffix_patterns(urlpatterns)