
import re
import json


CGATE_CMD_RAMP = 'ramp'
CGATE_CMD_ON = 'on'
CGATE_CMD_OFF = 'off'
CGATE_MAX_LEVEL = 255
STATE_OFF = "OFF"
STATE_ON = "ON"
CGATE_LEVEL_LOW = 50
CGATE_LEVEL_MEDIUM = 150
CGATE_LEVEL_HIGH = 255
FAN_LOW = 'low'
FAN_MEDIUM = 'medium'
FAN_HIGH = 'high'
SPEED_TOPIC = 'speed'

BASE_STATE_TOPIC = 'cgate/lighting/state/fan'
BASE_CMD_TOPIC = 'cgate/lighting/cmd/fan'

def mqtt2cgate(topic,msg):
    #TODO: validation of msg
    #msg = json.loads(msg)
    msg = msg.decode("utf-8")
    if topic.split('/').pop() == SPEED_TOPIC:
        topic = re.sub('/speed$', '', topic)
        group_address = topic.replace(BASE_CMD_TOPIC,'/')
        if msg == FAN_LOW:
            cmd = CGATE_CMD_RAMP
            level = CGATE_LEVEL_LOW
            ramp_time = 0
            return(("lighting %s %s %d %d\n" % (cmd,group_address,level,ramp_time)).encode("utf-8"))
        elif msg == FAN_MEDIUM:
            cmd = CGATE_CMD_RAMP
            level = CGATE_LEVEL_MEDIUM
            ramp_time = 0
            return(("lighting %s %s %d %d\n" % (cmd,group_address,level,ramp_time)).encode("utf-8"))
        elif msg == FAN_HIGH:
            cmd = CGATE_CMD_RAMP
            level = CGATE_LEVEL_HIGH
            ramp_time = 0
            return(("lighting %s %s %d %d\n" % (cmd,group_address,level,ramp_time)).encode("utf-8"))
    else:
        group_address = topic.replace(BASE_CMD_TOPIC,'/')
        if msg == STATE_OFF:
            return(("lighting %s %s\n" % (CGATE_CMD_OFF,group_address)).encode("utf-8"))
        elif msg == STATE_ON:
            return(("lighting %s %s\n" % (CGATE_CMD_ON,group_address)).encode("utf-8"))
    return None

class Fan():
    def __init__(self, topic=None, state=None):
        self.topic = topic
        self.msg = state

    def set_from_cgate_data(self,cmd,address,param,src):
        self.topic = BASE_STATE_TOPIC + address.replace('//','/')
        param_set = param.strip().split()
        if cmd == CGATE_CMD_RAMP:
            self.topic = self.topic + '/' + SPEED_TOPIC
            level = int(param_set[0])
            if level == 0:
                self.msg = STATE_OFF
            elif level > 0 and level <= CGATE_LEVEL_LOW:
                self.msg = FAN_LOW
            elif level > CGATE_LEVEL_LOW and level <= CGATE_LEVEL_MEDIUM:
                self.msg = FAN_MEDIUM
            elif level > CGATE_LEVEL_MEDIUM and level <= CGATE_LEVEL_HIGH:
                self.msg = FAN_HIGH
        elif cmd == CGATE_CMD_ON:
            self.msg = STATE_ON
        elif cmd == CGATE_CMD_OFF:
            self.msg = STATE_OFF
        return self

    def get_message(self):
        return self.msg
