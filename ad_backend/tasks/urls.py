# tasks/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, MyTasksView, AvailableTasksView

router = DefaultRouter()
router.register(r'', TaskViewSet, basename='tasks')  # ← empty string

urlpatterns = [
    path('', include(router.urls)),
    path('my-tasks/', MyTasksView.as_view(), name='my_tasks'),
    path('available-tasks/', AvailableTasksView.as_view(), name='available_tasks'),
]