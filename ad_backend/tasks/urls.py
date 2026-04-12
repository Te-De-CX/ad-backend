# tasks/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, MyTasksView, AvailableTasksView

router = DefaultRouter()

# 🔥 Use plural for consistency (best practice for REST APIs)
router.register('tasks', TaskViewSet, basename='tasks')

urlpatterns = [
    # 🔹 All ViewSet routes (list, detail, custom actions)
    path('', include(router.urls)),

    # 🔹 User-specific endpoints
    path('my-tasks/', MyTasksView.as_view(), name='my_tasks'),
    path('available-tasks/', AvailableTasksView.as_view(), name='available_tasks'),
]

