import re
import telnetlib
import time
import cgatemqtt.cgateapi.exceptions as ex
import cgatemqtt.cgateapi.cgatecodes as codes

CMD_TIMEOUT = 5
CONNECT_TIMEOUT = 10
MORE_TIMEOUT = 1

class CGateCommand():
    def __init__(self):
        #regular expression to parse response codes and messages
        self.respre = re.compile(r'(\d+)(-|\s)(.*)')

    class _Response():
        def __init__(self, code, msg):
            self.resp_code = int(code)
            self.msg = msg

    def _read(self,timeout=CMD_TIMEOUT):
        result = self.tn.read_until(b"\r\n",timeout).decode("utf-8")
        if result == '':
            raise ex.GgateCommandTimeout('Timeout waiting for response on CGate'
                                      'command interface')
        rdata = self.respre.search(result)
        if rdata is None:
           raise ex.GgateCommandError('Error parsing command response.')
        code = rdata.group(1)
        msg = rdata.group(3)+"\n"
        while rdata.group(2) == '-': #more response data
            result = self.tn.read_until(b"\r\n",MORE_TIMEOUT).decode("utf-8")
            rdata = self.respre.search(result)
            msg += rdata.group(3)+"\n"
        return self._Response(code, msg)

    def _msg2av(self, msg):
        av_list = []
        msg = msg.rstrip()
        for line in msg.split("\n"):
            av_list.append(dict(s.split('=', 1) for s in line.split()))
        return av_list

    def connect(self,host,port=20023):
        self.host = host
        self.port = port

        self.tn = telnetlib.Telnet(self.host,port=self.port)
        resp = self._read(CONNECT_TIMEOUT)
        if resp.resp_code == codes.SERVICE_READY:
            return ("CGateCommand: %d %s" % (resp.resp_code,resp.msg))
        else:
            raise ex.GgateCommandError("Connection failed %s:%d [%d]%s" %
                (self.host, self.port, resp.resp_code, resp.msg))

    def command(self, command):
        command = command+"\n"
        self.tn.write(command.encode("utf-8"))
        return self._read()

    def command_with_av_resp(self, cmd, expected_code):
        resp = self.command(cmd)
        if resp.resp_code == expected_code:
            return self._msg2av(resp.msg)
        else:
            raise ex.GgateCommandError('Error calling "',cmd,'" code:',resp.resp_code)

    def project_list(self):
        return self.command_with_av_resp("project list", 123)

    def net_list(self, project_id):
        return self.command_with_av_resp(("net list //%s" % project_id), 131)

    def net_open(self, project_id, net_id):
        resp = self.command("net open //%s/%s" % (project_id, net_id))
        if resp.resp_code == 200:
           return True
        else:
           raise ex.GgateCommandError('Error opening network; code:',resp.resp_code)

def main():
    cc = CGateCommand()
    cc.connect("127.0.0.1")
    cc.command("noop")

if __name__ == '__main__':
    main()
