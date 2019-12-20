#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import importlib
import django
import logging

logger = logging.getLogger("error")
pathname = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, pathname)
sys.path.insert(0, os.path.abspath(os.path.join(pathname, '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autoadmin.settings")
importlib.reload(sys)

django.setup()
from salt.api import SaltAPI
from salt.models import Minions_status


def minion_status():
    sapi = SaltAPI()
    minions_status = sapi.runner("manage.status")

    for minion_id in minions_status['up']:
        hostname = Minions_status()
        try:
            res = Minions_status.objects.filter(minion_id=minion_id)
            if not res:
                hostname.minion_id = minion_id
                hostname.minion_status = "up"
                hostname.save()
        except Exception as e:
            logger.error(e.args)
    for minion_id in minions_status['down']:
        hostname = Minions_status()
        try:
            res = Minions_status.objects.filter(minion_id=minion_id)
            if not res:
                hostname.minion_id = minion_id
                hostname.minion_status = "down"
                hostname.save()
        except Exception as e:
            logger.error(e.args)


minion_status()