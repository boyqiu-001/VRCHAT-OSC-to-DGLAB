import socket
import time
import qrcode
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
import asyncio
import json
import tkinter as tk
from tkinter import ttk 
from PIL import Image, ImageTk
from threading import Thread,Event
from pydglab_ws import FeedbackButton, Channel, RetCode, DGLabWSServer,StrengthData,StrengthOperationType



from defaultData import defaultConfig,defaultpatterns
from logger import logger
        


windowLog =logger("window")
serverLog =logger("OSCserver")
dglabLog = logger("dglabServer")












class App(tk.Frame):
    def __init__(self, master,config):
        
        super().__init__(master)

        self.config=config
        self.restartButton=ttk.Button(text="restart(重启服务)",command=self.restart_server)
        self.restartButton.place(x=150,y=600,width=150,height=50)
       
        self.saveButton=ttk.Button(text="save_config(保存配置)",command=self.save_config)
        self.saveButton.place(x=600,y=600,width=150,height=50)

        self.ipaddress = tk.StringVar(value=self.config["ipAddress"])
        self.ipaddress.trace_add(mode="write",callback=self._setIpaddress)
        self.APP_IP_Label=ttk.Label(text="local IP(本机局域网ip,无特殊情况无需填写)")
        self.APP_IP_Label.place(x=20,y=20,width=250,height=30)
        self.APP_IP_Entry = ttk.Entry(textvariable=self.ipaddress)
        self.APP_IP_Entry.place(x=270,y=20,width=150,height=30)


        self.sleepTime = tk.StringVar(value=self.config["sleepTime"])
        self.sleepTime.trace_add(mode="write",callback=self._setSleepTime)
        self.sleepTime_Label=ttk.Label(text="package interval time(数据包间隔时间)")
        self.sleepTime_Label.place(x=550,y=20,width=250,height=30)
        self.sleepTime_Entry = ttk.Entry(textvariable=self.sleepTime)
        self.sleepTime_Entry.place(x=800,y=20,width=50,height=30)



        self.tmp=tk.Label(text="界面都没完成,只能改ip和数据包间隔\n改监控的osc参数和响应强度等请修改配置文件")
        self.tmp.place(x=300,y=200,height=200)

        self.oscSettingsFrame=ttk.Labelframe(text="VRCHAT settings(VRC OSC参数监听设置)")
        self.avatarParameterFrame=ttk.Labelframe(master=self.oscSettingsFrame,text="avatarParameter(模型参数)")
        

        self.avatarParameter_Entry=ttk.Entry(master=self.avatarParameterFrame)
        self.avatarParameter=tk.StringVar(value=self._getAvatarParameter())
        self.avatarParameter_Scroll=tk.Scrollbar(master=self.avatarParameterFrame)
        self.avatarParameter_Listbox=tk.Listbox(master=self.avatarParameterFrame,listvariable=self.avatarParameter,width=25,yscrollcommand=self.avatarParameter_Scroll.set)
        self.avatarParameter_Scroll['command']=self.avatarParameter_Listbox.yview
        self.avatarParameter_Listbox.bind(sequence='<<ListboxSelect>>',func=self.avatarParameterListboxSelect)
        self.avatarParameterFrameRight=ttk.Frame(master=self.avatarParameterFrame)
        self.avatarParameter_change_buttom=ttk.Button(master=self.avatarParameterFrame,text='修改参数',command=self.changeAvatarParameterName,width=8)
        self.avatarParameter_Add_buttom=ttk.Button(master=self.avatarParameterFrame,text='增加参数',command=self.addAvatarParameterName,width=8)
        self.avatarParameter_remove_buttom=ttk.Button(master=self.avatarParameterFrame,text='删除参数',command=self.removeAvatarParameterName,width=8)
        
        self.oscSettingsFrame.place(x=50,y=60,height=200)

        self.avatarParameterFrame.pack(side="left",fill="y")
        self.avatarParameter_Entry.pack(side='top',fill='x')
        self.avatarParameter_Listbox.pack(side="left",fill='y')
        self.avatarParameter_Scroll.pack(side='left',fill='y')
        self.avatarParameter_change_buttom.pack()
        self.avatarParameter_Add_buttom.pack()
        self.avatarParameter_remove_buttom.pack()
        self.avatarParameterFrameRight.pack(side='right')

        self.judgeValueFrame=ttk.Labelframe(master=self.oscSettingsFrame,text="judgeValue(判断段参数)")

        self.judgeValue_Entry=ttk.Entry(master=self.judgeValueFrame)
        self.judgeValue=tk.StringVar(value=self._getJudgeValues(0))
        self.judgeValue_Scroll=tk.Scrollbar(master=self.judgeValueFrame)
        self.judgeValue_Listbox=tk.Listbox(master=self.judgeValueFrame,listvariable=self.judgeValue,width=25,yscrollcommand=self.judgeValue_Scroll.set)
        self.judgeValue_Scroll['command']=self.judgeValue_Listbox.yview
        self.judgeValue_Listbox.bind(sequence='<<ListboxSelect>>',func=self.judgeValueListboxSelect)
        self.judgeValueFrameRight=ttk.Frame(master=self.judgeValueFrame)
        self.judgeValueFrame_change_buttom=ttk.Button(master=self.judgeValueFrameRight,text='修改参数',command=self.changeJudgeValueName,width=8)
        self.judgeValueFrame_Add_buttom=ttk.Button(master=self.judgeValueFrameRight,text='增加参数',command=self.addJudgeValueName,width=8)
        self.judgeValueFrame_remove_buttom=ttk.Button(master=self.judgeValueFrameRight,text='删除参数',command=self.removeJudgeValueName,width=8)

        self.judgeValueFrame.pack(side="left",fill="y")
        self.judgeValue_Entry.pack(side='top',fill='x')
        self.judgeValue_Listbox.pack(side="left",fill='y')
        self.judgeValue_Scroll.pack(side='left',fill='y')
        self.judgeValueFrame_change_buttom.pack()
        self.judgeValueFrame_Add_buttom.pack()
        self.judgeValueFrame_remove_buttom.pack()
        self.judgeValueFrameRight.pack(side='right')


        self.judgeValue=tk.StringVar()
        self.judgePattern=tk.StringVar()

        self.judgePatternCombobox=ttk.Combobox(textvariable=self.judgePattern,values=['1','2','3'],state='readonly')
        self.judgePatternCombobox.place(x=400,y=400)

        self.qrImageLabel=tk.Label()
        self.qrImageLabel.place(x=50,y=400,height=400)

        self.osc_exit_event = Event()
        self.pack()
        self.dgserver=DGLabServerTread(self)
        self.dgserver.start()
        self.p=ServerTread(self,self.osc_exit_event,dgServer=self.dgserver)
        # self.p.start()

    def avatarParameterListboxSelect(self,event):
        widget:tk.Listbox=event.widget
        selectedId=widget.curselection()
        print(selectedId,selectedId[0])
        a=self._getJudgeValues(selectedId[0])
        print(a)
        self.judgeValue.set(a)
        # print(self.judgeValue.get(),self.judgeValue_Listbox.get())
        
        self.judgePatternCombobox.config(values=['3','4'])
        self.judgeValue_Listbox.config(listvariable=self.judgeValue)

        # self.judgeValue.set()
    def judgeValueListboxSelect(self,event):
        widget:tk.Listbox=event.widget
        selectedId=widget.curselection()

        self.judgeValue.set(self._getJudgeValues(selectedId[0]))
        # self.judgePatternCombobox.config(values=['3','4'])

        # self.judgeValue.set()
    def changeAvatarParameterName(self,event):
        pass
    def addAvatarParameterName(self,event):
        pass
    def removeAvatarParameterName(self,event):
        pass
    def changeJudgeValueName(self,event):
        pass
    def addJudgeValueName(self,event):
        pass
    def removeJudgeValueName(self,event):
        pass

    def _setIpaddress(self,name,index,traceMode):
        self.config["ipAddress"]=self.ipaddress.get()
    
    def _getAvatarParameter(self):
        avatarParameter=''
        for i in range(0,len(self.config["oscSettings"])):
            avatarParameter+=self.config["oscSettings"][i]["avatarParameter"].split('/')[-1]
            avatarParameter+=' '
        return avatarParameter
    def _getJudgeValues(self,index)->str:
        judgeValues=''
        for i in range(0,len(self.config["oscSettings"][index]["judgeSettings"])):
            judgeValues+=str(self.config["oscSettings"][index]["judgeSettings"][i]['value'])
            judgeValues+=' '
        return judgeValues
    def _getJudgePattern(self,index,valueIndex):
        judgeValues=''
        for i in range(0,len(self.config["oscSettings"][index]["judgeSettings"])):
            judgeValues+=str(self.config["oscSettings"][index]["judgeSettings"][i]['value'])
            judgeValues+=' '
        return judgeValues
    def _setSleepTime(self,name,index,traceMode):
        if self.sleepTime.get()!='':
            self.config["sleepTime"]=int(self.sleepTime.get())
    def print_contents(self, event):
        print(event.widget)
        print("self.APP_IP_Entry.get()",self.APP_IP_Entry.get())
        print("self.ipaddress.get",self.ipaddress.get())
        print('self.config["ipAddress"]',self.config["ipAddress"])
        print('self.config["APPVersion"]',self.config["APPVersion"],type(self.config["APPVersion"]))
    def restart_server(self):
        windowLog.info("start to close server")
        self.osc_exit_event.set()
        time.sleep(2)
        self.osc_exit_event.clear()
        windowLog.info("server closed")
        self.p=ServerTread(self,self.osc_exit_event)
        self.p.start()
    def close_server(self):
        self.osc_exit_event.set()
    def save_config(self):
        with open('config.json', 'w+', encoding="utf8") as f:
            f.write(json.dumps(self.config,ensure_ascii=False))
        self.restart_server()




class DGLabServerTread(Thread):
    def __init__(self,master:App) -> None:
        super().__init__()
        self.daemon=True
        self.frame=master
        self.bind_event=Event()
        self.bind_event.set()
        self.strengthData:StrengthData=None
        self.task=None

    def run(self):
        self.task=asyncio.run(self.serverStart())
        dglabLog.info('dglabServer stopped')
    def create_qrcode(self,data):
        time.sleep(10)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        return img
        
    def print_qrcode(self,data: str):
        """输出二维码到终端界面"""
        
        # qr = qrcode.make(data)
        # qr.save('qrcode.png')
        # image=qr.make_image(fill='black', back_color='white')
        image=self.create_qrcode(data)
        image.save('qrcode.png')
        image.show()
        

    async def serverStart(self):
        async with DGLabWSServer("0.0.0.0", 5678, 60) as server:
            self.client = server.new_local_client()

            url = self.client.get_qrcode(f"ws://{str(socket.gethostbyname(socket.getfqdn()))}:5678")
            dglabLog.info("请用 DG-Lab App 扫描二维码以连接")
            self.print_qrcode(url)

            # 等待绑定
            await self.client.bind()
            dglabLog.info(f"已与 App {self.client.target_id} 成功绑定")
            self.frame.p.start()

            # 从 App 接收数据更新，并进行远控操作
            # pulse_data_iterator = iter(self.patterns.values())
            async for data in self.client.data_generator(FeedbackButton, RetCode,StrengthData):

                if isinstance(data,StrengthData):
                    self.strengthData=data
                    self.strengthData

                    
                if isinstance(data, FeedbackButton):
                    dglabLog.info(f"App 触发了反馈按钮：{data.name}")

                    if data == FeedbackButton.A1:
                        # 顺序发送波形
                        dglabLog.info("对方按下了 A 通道圆圈按钮")

                # 接收 心跳 / App 断开通知
                elif data == RetCode.CLIENT_DISCONNECTED:
                    dglabLog.warning("App 已断开连接，你可以尝试重新扫码进行连接绑定")
                    self.bind_event.clear()
                    await self.client.rebind()
                    self.bind_event.set()
                    dglabLog.info("重新绑定成功")
    


class ServerTread(Thread):
    def __init__(self,master:tk.Frame,exit_event:Event,dgServer:DGLabServerTread=None) -> None:
        super().__init__()
        self.daemon=True
        self.exit_event=exit_event
        self.frame=master
        self.dgServer=dgServer
        self.OSCclient=None
        self.config=None
        self.patterns=None
        
        serverLog.info(f"server start")
        try:            
            with open('patterns.json', 'r', encoding="utf8") as f:
                self.patterns = json.load(f)
        except FileNotFoundError:
            with open('patterns.json', 'w+', encoding="utf8") as f:
                serverLog.info('正在创建波形文件')
                f.write(json.dumps(defaultpatterns,ensure_ascii=False))
                self.patterns = defaultpatterns
        try:
            with open('config.json', 'r', encoding="utf8") as f:
                self.config = json.load(f)

            browser = OSCQueryBrowser()
            time.sleep(2)
            self.configInit()
            service = browser.find_service_by_name("VRChat-Client")
            self.OSCclient = OSCQueryClient(service)
        except FileNotFoundError:
            with open('config.json', 'w+') as f:
                f.write(json.dumps(defaultConfig,ensure_ascii=False))
            serverLog.info("please restart exe")
            serverLog.info("请重启服务")
        except  Exception as e:
            serverLog.error("cannot Find OSC please open after VRCHAT started")
            serverLog.error(f"unexcepted error:{e}|type:{type(e)}")


    def run(self):
        self.task=asyncio.run(self.webSocketstart())
        serverLog.info('server closed')
                




    async def webSocketstart(self):
            last_id=list()
            for i in range(0,len(self.config["oscSettings"])):last_id.append(None)
            while not self.exit_event.is_set():
                self.dgServer.bind_event.wait(timeout=5)
                if not self.dgServer.bind_event.is_set(): continue
                maxtick=0
                try:
                    for i in range(0,len(self.config["oscSettings"])):
                        node = self.OSCclient.query_node(self.config["oscSettings"][i]["avatarParameter"])
                        id=self.judge(i,value=node.value[0])
                        # serverLog.info(id)
                        if id is not None :
                            ticks=int(self.config["oscSettings"][i]["judgeSettings"][id]["ticks"])
                            if self.config["oscSettings"][i]["mode"]in[0,1,2]:
                                
                                tickstime=await self.sendMessage(i,id,ticks)
                                if maxtick<tickstime:maxtick=tickstime
                            if self.config["oscSettings"][i]["mode"]==3:
                                if last_id[i]is None:
                                    last_id[i]==id
                                    time.sleep(1)
                                if last_id[i]is not None and last_id[i]!=id:
                                    last_id[i]==id
                                    tickstime=await self.sendMessage(i,id,ticks)
                                    if maxtick<tickstime:maxtick=tickstime  
                    time.sleep(self.config["sleepTime"]+maxtick/10)  
                except TimeoutError:  
                    serverLog.warning("Timeout,Sever cannot connect to APP,please check APP||连接超时,无法连接至APP请检查APP是否处于运行状态")
                    time.sleep(1)
                except AttributeError:
                    serverLog.warning("Server cannot get value,please check avatar parameters or VRCHAT||无法检测到指定的模型参数,请检查模型参数是否正确")
                    time.sleep(1)
                except ConnectionRefusedError:
                    serverLog.warning("ConnectionRefused,Server cannot to APP,please check APP||无法连接致手机APP,请检查手机APP是否开启")
                    time.sleep(1) 
                except  Exception as e:
                    serverLog.error(f"unexcepted error:{e}|type:{type(e)}")
                    time.sleep(1)
                    continue




    async def sendMessage(self,i,id,ticks):
            pattern_name=self.config["oscSettings"][i]["judgeSettings"][id]["pattern"]
            pattern=self.patterns[pattern_name]
            channel=self.getChannel(self.config["oscSettings"][i]["judgeSettings"][id]["channel"])

            looptime=self.getPatternLoopTime(pattern_name,ticks)
            inCorrectIntensity,expected_intensity=self.isInCorrectIntensity(i,id,channel)
            if inCorrectIntensity is None:
                serverLog.error(f"unexcepted intensity error")
                return None
            if not inCorrectIntensity: 
                serverLog.info(f"SetStrength:{expected_intensity}")
                await self.dgServer.client.set_strength(channel,StrengthOperationType.SET_TO,expected_intensity)
            await self.dgServer.client.add_pulses(channel,*(pattern*looptime))
            serverLog.info(f"Sent||name:{pattern_name}|strength Data:{self.dgServer.strengthData}|ticks:{ticks}|time:{len(pattern)/10*looptime} s")
            return len(pattern)*looptime
        


            
    
    def configInit(self):
        for i in range(0,len(self.config["oscSettings"])): 
            point=self.config["oscSettings"][i]
            if point["mode"]==1 and len(point["judgeSettings"])>1:
                point["judgeSettings"].sort(key=lambda value:value["value"], reverse=True)
            if point["mode"]==2 and len(point["judgeSettings"])>1:
                point["judgeSettings"].sort(key=lambda value:value["value"], reverse=False)
        
    def judge(self,i,value):

        mode=int(self.config["oscSettings"][i]["mode"])
        judgeValue=self.config["oscSettings"][i]["judgeSettings"]
        for index in range(0,len(judgeValue)):
            if mode==0:
                if value==judgeValue[index]["value"]:return index
            elif mode==1:
                if value>judgeValue[index]["value"]:return index
            elif mode==2:
                if value<judgeValue[index]["value"]:return index
            elif mode==4:
                if value==judgeValue[index]["value"]:return index
            else:
                serverLog.error(f"unexpected json 参数错误 mode{i} error ")
        return None

    def getChannel(self,value):
        if value=='A':return Channel.A
        if value=='B':return Channel.B
        serverLog.error(f"unexpected json 参数错误 channel error ") 

    def isInCorrectIntensity(self,i,id,channel:Channel):
        intensity=int(self.config["oscSettings"][i]["judgeSettings"][id]["intensity"])
        expected_intensity=None
        current_intensity=None
        if channel==Channel.A:
            expected_intensity=int(intensity/100*self.dgServer.strengthData.a_limit)
            current_intensity=self.dgServer.strengthData.a
        if channel==Channel.B:
            expected_intensity=int(intensity/100*self.dgServer.strengthData.b_limit)  
            current_intensity=self.dgServer.strengthData.b
        if expected_intensity is not None and current_intensity is not None:
            return expected_intensity==current_intensity,expected_intensity
        else:
            return None,None
    
    def getPatternLoopTime(self,pattern_name,ticks)->int:
        one_round_tick=len(self.patterns[pattern_name])
        num=int(ticks/one_round_tick)
        return num+1
    def getMessage(self,i,id):
        
        return self.config["patternSettings"][self.config["oscSettings"][i]["judgeSettings"][id]["pattern"]]

    def getParamaterValue(self,message,paramaterstring):
        if paramaterstring in message:return message[paramaterstring]
        if f"A_{paramaterstring}" in message:return message[f"A_{paramaterstring}"]
        if f"B_{paramaterstring}" in message:return message[f"B_{paramaterstring}"]


    async def webSocketSendMessage(self,websocket,message_name,message,sendType):
        sendMessage=json.dumps(message,ensure_ascii=False)
        if sendType == 1:
            await websocket.send(sendMessage)
            serverLog.info(f"Sent||name:{message_name}|intensity:{self.getParamaterValue(message,"intensity")}|time:{self.getParamaterValue(message,"ticks")/10} s")
        else: 
            response = await websocket.recv()
            serverLog.info(f"Received: {response}")
    





if __name__ == '__main__':
    try:
        with open('config.json', 'r', encoding="utf8") as f:
            config = json.load(f)
    except FileNotFoundError:
        with open('config.json', 'w+', encoding="utf8") as f:
            f.write(json.dumps(defaultConfig),ensure_ascii=False)
    
    windowLog.info("program start")
    root = tk.Tk()
    root.geometry('900x700')
    root.title('VRCHATosc To open-DGLAB-controller')
    root.resizable(0, 0)
    myapp = App(root,config=config)
    myapp.mainloop()
    myapp.osc_exit_event.set()
    time.sleep(3)

