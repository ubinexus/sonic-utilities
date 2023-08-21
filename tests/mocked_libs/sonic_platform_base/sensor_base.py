class VoltageSensorBase():
    @classmethod
    def get_unit(cls):
        return "mV"


class CurrentSensorBase():
    @classmethod
    def get_unit(cls):
        return "mA"
