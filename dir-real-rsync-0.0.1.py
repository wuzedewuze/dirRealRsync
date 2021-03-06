#!/usr/bin/python
#-*-coding:utf-8-*-

import os
import commands
import time
import sys
from  pyinotify import  WatchManager, Notifier,ProcessEvent,IN_DELETE, IN_CREATE,IN_MODIFY
import pyinotify


#进程事件监控执行类
class EventHandler(ProcessEvent):

    def __init__(self,log_file_path,source_path,des_ip,des_path):
        ProcessEvent.__init__(self)                # 继承父类的初始化方法参数
        self.log_file_path = log_file_path
        self.source_path = source_path
        self.des_ip = des_ip
        self.des_path = des_path

    #记录日志的装饰器
    def rsync_log(function):
        def log_closure(self,event):
            function(self,event)       #执行引用的函数
            current_time = time.strftime("%Y-%m-%d_%H:%M:%S",time.localtime())
            log=open(self.log_file_path,'a')
            log.write("%s %s file: %s \n"  %  (current_time,event.maskname,os.path.join(event.path,event.name)))
            log.flush()
            log.close()
        return log_closure

    #检查文件类型的装饰器
    def check_filetype(function):
        def filetype(self,event):
            checkfilepath = os.path.join(event.path,event.name)
            print checkfilepath
            checkcommand = 'file -b --mime-type %s' % checkfilepath
            filetype = commands.getstatusoutput(checkcommand)
            if (filetype[1] != 'text/plain'):
                print "发邮件"
            function(self,event)
        return filetype


    #组装同步命令方法
    def rsync_command(self,source_path,des_ip,des_path):
        current_time = time.strftime("%Y-%m-%d_%H:%M:%S",time.localtime())
        command =  'rsync -ae "ssh -p 32768" --timeout=60   %s %s:%s  -b --suffix='  % (source_path,des_ip,des_path) + current_time
        return command

    @check_filetype
    @rsync_log
    def process_IN_CREATE(self, event):
        command = self.rsync_command(self.source_path,self.des_ip,self.des_path)
        os.system(command)

    @rsync_log
    def process_IN_DELETE(self, event):
        pass


    @check_filetype
    @rsync_log
    def process_IN_MODIFY(self, event):
        command = self.rsync_command(self.source_path,self.des_ip,self.des_path)
        os.system(command)





#主方法，执行调用监控
def do_monit(monit_path,log_file_path,source_path,des_ip,des_path):
    wm = WatchManager()  #create a watchmanager()
    mask = pyinotify.IN_DELETE | pyinotify.IN_MODIFY  # 需要监控的事件 
    notifier = Notifier(wm, EventHandler(log_file_path,source_path,des_ip,des_path))
    wdd = wm.add_watch(monit_path, mask, rec=True)  # 加入监控，mask，rec递归
    #notifier.loop()    #开始循环监控
    try:
        #防止启动多个的命令 设置进程号文件就可以防止启动多个
        notifier.loop(daemonize=True, pid_file='/tmp/pyinotify.pid')
    except pyinotify.NotifierError, err:
        print >> sys.stderr, err



if __name__ == "__main__":
    monit_path = "/home/frbaosftp"
    log_file_path = "/home/test.log"  #注意不要设置在监控目录下
    source_path = "/home/frbaosftp"
    des_ip = "192.168.2.94"
    des_path = "/home"      
    do_monit(monit_path,log_file_path,source_path,des_ip,des_path)
