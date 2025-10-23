from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Any URL starting with 'api/' will be handled by our 'api.urls' file
    path('api/', include('api.urls')),
]