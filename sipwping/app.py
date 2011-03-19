# coding=utf8

# Copyright (C) 2011 Saúl Ibarra Corretgé <saghul@gmail.com>
#

from threading import Event, Thread

from application import log
from application.notification import IObserver, NotificationCenter
from application.python.util import Null, Singleton
from sipsimple.core import Engine
from twisted.internet import reactor
from twisted.internet.error import ReactorNotRunning
from zope.interface import implements

from sipwping import __version__
from sipwping.configuration import GeneralConfig
from sipwping.web import HTTPListener


class SIPOptionsApplication(object):
    __metaclass__ = Singleton
    implements(IObserver)

    def __init__(self):
        self.http_listener = None
        self.reactor_thread = None
        self.state = None
        self.stop_event = Event()
        self.supported_transports = []

    def start(self):
        self.reactor_thread = Thread(name='Reactor Thread', target=self._run_reactor)
        self.reactor_thread.start()

    def stop(self):
        if self.stopped:
            return
        engine = Engine()
        engine.stop()
        self.reactor_thread.join()
        self.stop_event.set()

    @property
    def stopped(self):
        return self.state == 'stopped'

    def _run_reactor(self):
        from eventlet.twistedutil import join_reactor
        reactor.callLater(0, self._start_engine)
        reactor.run(installSignalHandlers=False)

    def _start_engine(self):
        engine = Engine()
        NotificationCenter().add_observer(self, sender=engine)
        engine.start(
            ip_address=None,
            udp_port=GeneralConfig.sip_udp_port,
            tcp_port=GeneralConfig.sip_tcp_port,
            tls_port=None,
            user_agent='SIPwPinger %s' % __version__,
            log_level=0
        )

    def handle_notification(self, notification):
        handler = getattr(self, '_NH_%s' % notification.name, Null)
        handler(notification)

    def _NH_SIPEngineDidStart(self, notification):
        self.state = 'started'
        engine = Engine()
        for transport in ('udp', 'tcp', 'tls'):
            if getattr(engine, '%s_port' % transport) is not None:
                self.supported_transports.append(transport)
        self.http_listener = HTTPListener()
        self.http_listener.start()
        log.msg('SIP Engine started')
        log.msg('Enabled SIP transports: %s' % ', '.join(transport.upper() for transport in self.supported_transports))

    def _NH_SIPEngineDidEnd(self, notification):
        log.msg('SIP Engine stopped')
        self.state = 'stopped'
        self.http_listener.stop()
        reactor.stop()

    def _NH_SIPEngineDidFail(self, notification):
        log.msg('SIP Engine failed')
        if self.http_listener is not None:
            self.http_listener.stop()
        try:
            reactor.stop()
        except ReactorNotRunning:
            pass
        self.stop_event.set()


