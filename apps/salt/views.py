import coreapi
from rest_framework import viewsets, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from salt.api import SaltAPI
from salt.serializers import MinionStausSerializer
from .models import Minions_status
from django.http import Http404
from rest_framework.schemas import AutoSchema
from rest_framework.exceptions import APIException
import logging
import json

logger = logging.getLogger('default')


class MinonStatusViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    list:
    查看salt-minion的状态
    """
    serializer_class = MinionStausSerializer
    queryset = Minions_status.objects.all()


class ListKeyView(APIView):
    """
    列出所有的key
    """

    def get(self, request, *args, **kwargs):
        sapi = SaltAPI()
        result = sapi.list_all_key()
        minion_key = []
        if isinstance(result, dict):
            if result.get("status") is False:
                return result, 500
            for minions_rejected in result.get("minions_rejected"):
                minion_key.append({"minions_status": "Rejected", "minions_id": minions_rejected})
            for minions_denied in result.get("minions_denied"):
                minion_key.append({"minions_status": "Denied", "minions_id": minions_denied})
            for minions in result.get("minions"):
                minion_key.append({"minions_status": "Accepted", "minions_id": minions})
            for minions_pre in result.get("minions_pre"):
                minion_key.append({"minions_status": "Unaccepted", "minions_id": minions_pre})
        else:
            logger.error("Get minion key error: %s" % result)
        return Response({"data": minion_key, "status": True, "message": ""}, 200)


class AddKeyView(APIView):
    """
    接受key
    """

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(name='hostname', required=True, location='form', description='主机列表', type='array'),
        ]
    )

    def check_object(self, hostname):
        try:
            obj = Minions_status.objects.get(minion_id=hostname)
            return obj.minion_id
        except Minions_status.DoesNotExist:
            # raise Http404
            contenxt = hostname + " doesn't exist"
            raise APIException(contenxt)

    def post(self, request):
        hostnames = request.data.get('hostname', None)
        for hostname in hostnames:
            minion_id = self.check_object(hostname)
            sapi = SaltAPI()
            sapi.accept_key(minion_id)
        return Response({"status": 1})


class RejectKeyView(APIView):
    """
    拒绝key
    """

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(name='hostname', required=True, location='form', description='主机列表', type='array'),
        ]
    )

    def check_object(self, hostname):
        try:
            obj = Minions_status.objects.get(minion_id=hostname)
            return obj.minion_id
        except Minions_status.DoesNotExist:
            contenxt = hostname + " doesn't exist"
            raise APIException(contenxt)

    def post(self, request):
        hostnames = request.data.get('hostname', None)
        for hostname in hostnames:
            minion_id = self.check_object(hostname)
            sapi = SaltAPI()
            sapi.reject_key(minion_id)
        return Response({"status": 1})


class DeleteKeyView(APIView):
    """
    删除key
    """

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(name='hostname', required=True, location='form', description='主机列表', type='array'),
        ]
    )

    def check_object(self, hostname):
        try:
            obj = Minions_status.objects.get(minion_id=hostname)
            return obj.minion_id
        except Minions_status.DoesNotExist:
            contenxt = hostname + " doesn't exist"
            raise APIException(contenxt)

    def delete(self, request):
        hostnames = request.data.get('hostname', None)
        for hostname in hostnames:
            minion_id = self.check_object(hostname)
            sapi = SaltAPI()
            sapi.delete_key(minion_id)
        return Response({"status": 1})


class JobsHistoryView(APIView):
    """
    查看jobs历史
    """

    def get(self, request):
        sapi = SaltAPI()
        jids = sapi.runner("jobs.list_jobs")
        return Response(jids)


class JobsActiveView(APIView):
    """
    get:
    获取正在运行的jobs
    """

    def get(self, request):
        job_active_list = []
        sapi = SaltAPI()
        result = sapi.runner("jobs.active")
        if request:
            for jid, info in result.items():
                # 不能直接把info放到append中
                info.update({"Jid": jid})
                job_active_list.append(info)
        return Response({"data": job_active_list, "status": 1, "message": ""}, 200)


class JobsKillView(APIView):
    """
    delete:
    杀掉运行的job
    :parameter action: kill
    :parameter minion_ids: {"v-zpgeek-01": 12345,"v-zpgeek-02": 2345}
    """
    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(name='action', required=True, location='query', description='kill', type='string'),
            coreapi.Field(name='jid', required=True, location='query', description='20191220141748273576', type='string'),
            coreapi.Field(name='minion_ids', required=True, location='query', description='json字符串', type='string')
        ]
    )

    def delete(self, request):
        action = request.query_params.get('action', None)
        jid = request.query_params.get('jid', None)
        minion_ids = request.query_params.get('minion_ids', None)
        print(json.loads(minion_ids))
        if action and jid and minion_ids:
            for minion in json.loads(minion_ids):
                for minion_id, ppid in minion.items():
                    # 获取pgid 并杀掉
                    kill_ppid_pid = r'''ps -eo pid,pgid,ppid,comm |grep %s |grep salt-minion |
                                         awk '{print "kill -- -"$2}'|sh''' % ppid
                    try:
                        # 通过kill -- -pgid 删除salt 相关的父进程及子进程
                        sapi = SaltAPI()
                        pid_result = sapi.shell_remote_execution(minion_id, kill_ppid_pid)
                        logger.info("kill %s %s return: %s" % (minion, kill_ppid_pid, pid_result))
                    except Exception as e:
                        logger.info("kill %s %s error: %s" % (minion, jid, e))
            return Response({"status": 1, "message": ""}, 200)
        else:
            return Response({"status": 0, "message": "The specified jid or action or minion_id "
                                                "parameter does not exist"}, 400)


class JobsDetailView(APIView):
    """
    get:
    查看单个具体job
    """
    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(name='jid', required=True, location='query', description='12345678', type='string'),
        ]
    )

    def get(self, request, *args, **kwargs):
        jid = request.query_params.get('jid', None)
        sapi = SaltAPI()
        result = sapi.jobs_info(jid)
        return Response(result)


class JobsScheduleView(APIView):
    """
    get:
    查看定时任务
    """

    def get(self, request):
        sapi = SaltAPI()
        jids_running = sapi.runner("jobs.active")
        return Response(jids_running)
