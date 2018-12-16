import configparser
import getopt
import json
import logging
import logging.config
import re
import telnetlib
import threading
import sys
import paho.mqtt.client as mqtt
import cgatemqtt.handlers.lighting as lighting
import cgatemqtt.components.light as light
import cgatemqtt.components.fan as fan
import cgatemqtt.cgateapi.command as cmd

class CommandManager(threading.Thread):
    BASE_CMD_TOPIC = 'cgate/lighting/cmd'
    def __init__(self,mqttclient):
        threading.Thread.__init__(self)
        self.mqttclient = mqttclient
        self.mqttclient.on_message = self.on_message

    def on_message(self,client, userdata, msg):
        logger.debug("MQTT-Rx: %s %s" % (msg.topic,str(msg.payload)))
        # translate command to CGate command
        if msg.topic.startswith('cgate/lighting/cmd/fan'):
            cgate_cmd = fan.mqtt2cgate(msg.topic, msg.payload)
        else:
            # default base topic is for lights
            cgate_cmd = light.mqtt2cgate(msg.topic, msg.payload)
        # send command to CGate
        if cgate_cmd is not None:
            logger.debug("CGate-Tx: %s" % cgate_cmd)
            result = self.cc.command(cgate_cmd.decode("utf-8"))
            logger.debug("CGate-Resp: %s : %s" % (result.resp_code,result.msg.rstrip()))
        else:
            logger.warning("Unknown MQTT message on command topic %s" % msg.topic)

    def run(self):
        # connect to CGate command port
        self.mqttclient.subscribe(self.BASE_CMD_TOPIC+"/#")
        self.cc = cmd.CGateCommand()
        result = self.cc.connect(config['cgate']['host'],
                        port=config.getint('cgate', 'command_port', fallback=20023))
        logger.debug("CGateCommand connect: %s" % result)
        result = self.cc.net_open(config['cgate']['project'], config['cgate']['network'])
        logger.debug("CGateCommand net open: %s" % result)

class EventManager(threading.Thread):
    def __init__(self,mqttclient):
        threading.Thread.__init__(self)
        self.mqttclient = mqttclient
        self.lighting_eh = lighting.LightingEventHandler(config)

    def run(self):
        # connect to CGate event port
        self.tn = telnetlib.Telnet(config['cgate']['host'],
                                   port=config.getint('cgate', 'event_port', fallback=20025))
        while True:
            event = self.tn.read_until(b"\n")
            logger.debug("CGate-Event: %s" % event.decode("utf-8").rstrip())
            comp = self.lighting_eh.match(event.decode("utf-8"))
            #if comp is None:
                #try next event handler
                # only have the lighting eh for now

            #publish event to MQTT
            if comp is not None:
                logger.debug("MQTT-Tx: topic:%s data:%s" % (comp.topic,
                      comp.get_message()))
                # send to mqtt topic
                self.mqttclient.publish(comp.topic, payload=comp.get_message())

def on_connect(client, userdata, flags, rc):
    logger.info("Connected to mqtt broker with result code "+str(rc))
    cmd_thread.start()
    event_thread.start()


#def on_message(client, userdata, msg):
#    print(msg.topic+" "+str(msg.payload))


def usage():
    print("""
Usage:
   Options:
   -c <file> (--config-file)    config filename 
""")

def pars_args(argv):
    config_file = None
    debug = False
    try:
      opts, args = getopt.getopt(argv,"c:",["config-file="])
    except getopt.GetoptError:
      print('Error reading input arguments.')
      usage()
      exit(1)
    for opt, arg in opts:
      if opt in ("-c", "--config-file"):
        config_file = arg
    if not config_file:
      usage()
      print('Error: config file (-c) is a required argument.')
      exit(1)
    return (config_file, debug)

#def load_config(config_file):
#    config = configparser.ConfigParser()
#    config.read(config_file)
#    cgate_host = config['cgate']['host']
#    cgate_project = config['cgate']['project']
#    cgate_network = config['cgate']['network']
#    cgate_network = config['cgate']['command_port']
#    cgate_network = config['cgate'].getint('event_port',20025)

def main():
    global cmd_thread
    global event_thread
    global config
    global logger
    (config_file, debug) = pars_args(sys.argv[1:])
    config = configparser.ConfigParser()
    config.read(config_file)
    logging.config.fileConfig(config['logging']['config'])
    logger = logging.getLogger('CGateMQTTServer')
    client = mqtt.Client()
    cmd_thread = CommandManager(client)
    event_thread = EventManager(client)
    client.on_connect = on_connect

    client.username_pw_set(config['mqtt']['user'],password=config['mqtt']['password'])
    client.connect(config['mqtt']['host'], config['mqtt'].getint('port'), 60)
    client.loop_forever()

if __name__ == '__main__':
    main()

