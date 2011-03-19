
__all__ = ['GeneralConfig']

from application.configuration import ConfigSection, ConfigSetting
from sipwping import cfg_filename


# Datatypes

class Port(int):
    def __new__(cls, value):
        try:
            value = int(value)
        except ValueError:
            return None
        if not (0 <= value <= 65535):
            raise ValueError("illegal port value: %s" % value)
        return value


# Configuration objects

class GeneralConfig(ConfigSection):                                                                                                                                           
    __cfgfile__ = cfg_filename
    __section__ = 'General'
                                                                                                                                                                          
    sip_udp_port = ConfigSetting(type=Port, value=0)
    sip_tcp_port = ConfigSetting(type=Port, value=None)
    http_port = ConfigSetting(type=Port, value=8888)



