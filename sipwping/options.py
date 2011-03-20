# coding=utf8

# Copyright (C) 2011 Saúl Ibarra Corretgé <saghul@gmail.com>
#

from __future__ import with_statement

from collections import deque
from threading import RLock

from application.notification import IObserver, NotificationCenter
from application.python.util import Null
from sipsimple.account import ContactURIFactory
from sipsimple.core import Request, SIPURI
from sipsimple.core import FromHeader, ToHeader, RouteHeader
from sipsimple.lookup import DNSLookup
from zope.interface import implements

from sipwping.util import TimestampedNotificationData


class SIPOptionsRequestHandler(object):
    implements(IObserver)

    def __init__(self, target_uri):
        assert isinstance(target_uri, SIPURI)
        self.options_request = None
        self.target_uri = target_uri
        self._contact_factory = ContactURIFactory()
        self._routes = None

    def start(self):
        lookup = DNSLookup()
        NotificationCenter().add_observer(self, sender=lookup)
        from sipwping.app import SIPOptionsApplication
        lookup.lookup_sip_proxy(self.target_uri, SIPOptionsApplication().supported_transports)

    def _send_options(self):
        notification_center = NotificationCenter()
        route = self._routes.popleft()
        route_header = RouteHeader(route.get_uri())
        try:
            local_uri = self._contact_factory[route.transport]
        except KeyError:
            notification_center.post_notification('SIPOptionsRequestDidFail', sender=self, data=TimestampedNotificationData(code=0, reason='Could not build local URI'))
            return
        self.options_request = Options(FromHeader(local_uri),
                                       ToHeader(self.target_uri),
                                       route_header)
        notification_center.add_observer(self, sender=self.options_request)
        self.options_request.send(3)

    def handle_notification(self, notification):
        handler = getattr(self, '_NH_%s' % notification.name, Null)
        handler(notification)

    def _NH_DNSLookupDidSucceed(self, notification):
        NotificationCenter().remove_observer(self, sender=notification.sender)
        self._routes = deque(notification.data.result)
        self._send_options()

    def _NH_DNSLookupDidFail(self, notification):
        NotificationCenter().remove_observer(self, sender=notification.sender)

    def _NH_SIPOptionsDidSucceed(self, notification):
        notification_center = NotificationCenter()
        notification_center.remove_observer(self, sender=notification.sender)
        notification_center.post_notification('SIPOptionsRequestDidSucceed', sender=self, data=TimestampedNotificationData(code=notification.data.code, reason=notification.data.reason))

    def _NH_SIPOptionsDidFail(self, notification):
        notification_center = NotificationCenter()
        notification_center.remove_observer(self, sender=notification.sender)
        if not self._routes:
            notification_center.post_notification('SIPOptionsRequestDidFail', sender=self, data=TimestampedNotificationData(code=notification.data.code, reason=notification.data.reason))
            return
        self._send_options()


class Options(object):
    implements(IObserver)

    def __init__(self, from_header, to_header, route_header, credentials=None, extra_headers=[]):
        self._request = Request("OPTIONS", to_header.uri, from_header, to_header, route_header,
                                credentials=credentials, extra_headers=extra_headers)
        self._lock = RLock()

    from_header = property(lambda self: self._request.from_header)
    to_header = property(lambda self: self._request.to_header)
    route_header = property(lambda self: self._request.route_header)
    credentials = property(lambda self: self._request.credentials)
    in_progress = property(lambda self: self._request.state == "IN_PROGRESS")
    peer_address = property(lambda self: self._request.peer_address)

    def send(self, timeout=None):
        notification_center = NotificationCenter()
        with self._lock:
            notification_center.add_observer(self, sender=self._request)
            try:
                self._request.send(timeout)
            except:
                notification_center.remove_observer(self, sender=self._request)

    def end(self):
        with self._lock:
            self._request.end()

    def handle_notification(self, notification):
        handler = getattr(self, '_NH_%s' % notification.name, Null)
        handler(notification)

    def _NH_SIPRequestDidSucceed(self, notification):
        with self._lock:
            NotificationCenter().post_notification("SIPOptionsDidSucceed", sender=self,
                                                   data=TimestampedNotificationData(code=notification.data.code,
                                                                                    reason=notification.data.reason))

    def _NH_SIPRequestDidFail(self, notification):
        with self._lock:
            NotificationCenter().post_notification("SIPOptionsDidFail", sender=self,
                                                   data=TimestampedNotificationData(code=notification.data.code,
                                                                                    reason=notification.data.reason))

    def _NH_SIPRequestDidEnd(self, notification):
        with self._lock:
            NotificationCenter().remove_observer(self, sender=notification.sender)

