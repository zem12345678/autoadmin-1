from rest_framework.routers import DefaultRouter
from .views import ListKeyView, AddKeyView, MinonStatusViewSet, RejectKeyView, DeleteKeyView, JobsHistoryView, \
    JobsActiveView, JobsKillView, JobsScheduleView, JobsDetailView
from django.conf.urls import include, url

salt_router = DefaultRouter()
salt_router.register(r'minion/status', MinonStatusViewSet, base_name="minion_status")

urlpatterns = [
    url(r'^', include(salt_router.urls)),
    # key管理
    url(r'^key/$', ListKeyView.as_view()),
    url(r'^key/add/$', AddKeyView.as_view()),
    url(r'^key/reject/$', RejectKeyView.as_view()),
    url(r'^key/delete/$', DeleteKeyView.as_view()),

    # Job管理
    url(r'^jobs/history/$', JobsHistoryView.as_view()),
    url(r'^jobs/active/$', JobsActiveView.as_view()),
    url(r'^jobs/detail/$', JobsDetailView.as_view()),
    url(r'^jobs/kill/$', JobsKillView.as_view()),
    url(r'^jobs/schedule/$', JobsScheduleView.as_view()),
]
