from classes.protocol_settings import Registry_Type


class transport_base:
    def __init__(self, settings : dict[str,str]) -> None:
        pass

    def connect():
        pass
    
    def read_registers(start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        pass

    def write_register(self, register : int, value : int, **kwargs):
        pass