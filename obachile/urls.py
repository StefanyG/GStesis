from django.contrib import admin
from django.urls import path
from scholar import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', views.index, name='index'),
]
urlpatterns += staticfiles_urlpatterns()