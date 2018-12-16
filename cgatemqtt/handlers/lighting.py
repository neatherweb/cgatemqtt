
import re
import json
import cgatemqtt.components.light as light
import cgatemqtt.components.fan as fan

CGATE_CMD_RAMP = 'ramp'
CGATE_CMD_ON = 'on'
CGATE_CMD_OFF = 'off'
CGATE_MAX_LEVEL = 255
STATE_OFF = "OFF"
STATE_ON = "ON"
BASE_STATE_TOPIC = 'cgate/lighting/state'
BASE_CMD_TOPIC = 'cgate/lighting/cmd'

class LightingEventHandler():

    def __init__(self, config):
        self.config = config
        self.eventre = re.compile(r'lighting\s+(\w+)\s+(\S+)\s+([^#]*).*#sourceunit=(\d+)')
        self.fan_groups = json.loads(config.get('lighting','fans',fallback='[]'))
        print(str(self.fan_groups))

    def match(self,event_string):
        edata = self.eventre.search(event_string)
        if edata is not None:
            cmd,address,param,src = edata.groups()
            group = int(address.split('/').pop())
            if group in self.fan_groups:
                return fan.Fan().set_from_cgate_data(cmd,address,param,src)
            else:
                return light.Light().set_from_cgate_data(cmd,address,param,src)
        else:
            return None

