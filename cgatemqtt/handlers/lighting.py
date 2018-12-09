
import re
import json


CGATE_CMD_RAMP = 'ramp'
CGATE_CMD_ON = 'on'
CGATE_CMD_OFF = 'off'
CGATE_MAX_LEVEL = 255
STATE_OFF = "OFF"
STATE_ON = "ON"
BASE_STATE_TOPIC = 'cgate/lighting/state'
BASE_CMD_TOPIC = 'cgate/lighting/cmd'

def mqtt2cgate(topic,msg):
    #TODO: validation of msg
    msg = json.loads(msg)
    group_address = topic.replace(BASE_CMD_TOPIC,'/')
    if msg['state'] == STATE_OFF:
        return(("lighting %s %s\n" % (CGATE_CMD_OFF,group_address)).encode("utf-8"))
    elif 'brightness' in msg and msg['brightness'] != None and msg['state'] == STATE_ON:
        cmd = CGATE_CMD_RAMP
        level = msg['brightness']
        ramp_time = 0
        if 'transition' in msg and msg['transition'] != None:
           ramp_time = msg['transition']
        return(("lighting %s %s %d %d\n" % (cmd,group_address,level,ramp_time)).encode("utf-8"))
    elif msg['state'] == STATE_ON:
        return(("lighting %s %s\n" % (CGATE_CMD_ON,group_address)).encode("utf-8"))
    return None

class LightingEventHandler():
    BASE_STATE_TOPIC = 'cgate/lighting/state'

    def __init__(self, topic=None,brightness=None,color_temp=None,color=None,effect=None,
                 state=None,transition=None,white_value=None,source=None):
        self.eventre = re.compile(r'lighting\s+(\w+)\s+(\S+)\s+([^#]*).*#sourceunit=(\d+)')
        self.topic = topic
        self.msg = {}
        self.msg['brightness'] = brightness
        self.msg['color_temp'] = color_temp
        self.msg['color'] = color
        self.msg['effect'] = effect
        self.msg['state'] = state
        self.msg['transition'] = transition
        self.msg['white_value'] = white_value
        self.msg['source'] = source

    def _set_from_cgate_data(self,cmd,address,param,src):
        self.topic = self.BASE_STATE_TOPIC + address.replace('//','/')
        param_set = param.strip().split()
        if cmd == CGATE_CMD_RAMP:
            self.msg['brightness'] = int(param_set[0])
            if self.msg['brightness'] == 0:
                self.msg['state'] = STATE_OFF
            else:
                self.msg['state'] = STATE_ON
            self.msg['transition'] = int(param_set[1])
        elif cmd == CGATE_CMD_ON:
            self.msg['brightness'] = CGATE_MAX_LEVEL
            self.msg['state'] = STATE_ON
        elif cmd == CGATE_CMD_OFF:
            self.msg['brightness'] = 0
            self.msg['state'] = STATE_OFF
        self.msg['source'] = src
        return True

    def match(self,event_string):
        edata = self.eventre.search(event_string)
        if edata is not None:
            return self._set_from_cgate_data(*edata.groups())
        else:
            return False

    def to_json(self):
        return json.dumps(self.msg)
