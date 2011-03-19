# coding=utf8

# Copyright (C) 2011 Saúl Ibarra Corretgé <saghul@gmail.com>
#

import re

from application.notification import IObserver, NotificationCenter
from application.python.util import Null, Singleton
from sipsimple.core import SIPURI, SIPCoreError
from twisted.internet import reactor
from twisted.web import server
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from zope.interface import implements

from sipwping import __version__
from sipwping.configuration import GeneralConfig
from sipwping.jsonlib import jsonlib
from sipwping.options import SIPOptionsRequestHandler 

server.version = 'SIPwPing %s' % __version__


class DataCache(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._data = {}

    def get(self, key):
        return self._data.get(key, None)

    def put(self, key, value):
        self._data[key] = value
        reactor.callLater(180, self._data.pop, key, None)


class OptionsResourceHandler(object):
    implements(IObserver)

    def __init__(self, request):
        jsondata = request.content.getvalue()
        try:
            data = jsonlib.loads(jsondata)
        except (jsonlib.DecodeError, ValueError):
            request.setResponseCode(400, 'Could not decode JSON data')
            request.finish()
            return
        try:
            target_uri = data.get('target_uri', '')
            if not re.match('^(sip:|sips:)', target_uri):
                target_uri = 'sip:%s' % target_uri
            target_uri = SIPURI.parse(target_uri)
        except SIPCoreError:
            request.setResponseCode(400, 'Supplied SIP URI is invalid')
            request.finish()
            return
        cache = DataCache()
        data = cache.get(str(target_uri))
        if data is not None:
            request.setHeader('Content-Type', 'application/json')
            request.write(jsonlib.dumps(data))
            request.finish()
            return
        self._target_uri = target_uri
        self._request = request
        self._handler = SIPOptionsRequestHandler(target_uri)
        NotificationCenter().add_observer(self, sender=self._handler)
        self._handler.start()

    def _send_response(self, notification_data):
        data = notification_data.__dict__.copy()
        timestamp = data.pop('timestamp')
        data['timestamp'] = str(timestamp)
        cache = DataCache()
        cache.put(str(self._target_uri), data)
        self._request.setHeader('Content-Type', 'application/json')
        self._request.write(jsonlib.dumps(data))
        self._request.finish()

    def handle_notification(self, notification):
        handler = getattr(self, '_NH_%s' % notification.name, Null)
        handler(notification)

    def _NH_SIPOptionsRequestDidSucceed(self, notification):
        NotificationCenter().remove_observer(self, sender=notification.sender)
        self._send_response(notification.data)

    def _NH_SIPOptionsRequestDidFail(self, notification):
        NotificationCenter().remove_observer(self, sender=notification.sender)
        self._send_response(notification.data)


class OptionsResource(Resource):

    def render_POST(self, request):
        OptionsResourceHandler(request)
        return NOT_DONE_YET


class HTTPListener(object):

    def __init__(self):
        self._root = Resource()
        self._root.putChild('options', OptionsResource())
        self._site = server.Site(self._root)
        self._listener = None

    def start(self):
        self._listener = reactor.listenTCP(GeneralConfig.http_port, self._site)

    def stop(self):
        self._listener.stopListening()

