# coding=utf8

# Copyright (C) 2011 Saúl Ibarra Corretgé <saghul@gmail.com>
#

from application.notification import NotificationData
from datetime import datetime
from dateutil.tz import tzlocal


# Modified from original in python-sipsimple
class TimestampedNotificationData(NotificationData):

    def __init__(self, **kwargs):
        self.timestamp = datetime.now(tzlocal())
        NotificationData.__init__(self, **kwargs)

