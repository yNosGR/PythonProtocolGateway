from protocol_settings import Registry_Type


class reader_base:
    def connect():
        pass
    
    def read_registers(start, count=1, registry_type : Registry_Type = Registry_Type.INPUT, **kwargs):
        pass