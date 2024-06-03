import copy
import socket
import time
import ast
import qrcode
from tinyoscquery.query import OSCQueryBrowser, OSCQueryClient
import asyncio
import json
import tkinter as tk
from tkinter import ttk 
from tkinter.scrolledtext import ScrolledText
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
        """
        子线程启动
        """
        self.osc_exit_event = Event()
        self.pack()
        self.dgserver=DGLabServerTread(self)

        self.p=ServerTread(self,self.osc_exit_event,dgServer=self.dgserver)

        self.pattern=self.p.patterns



        """
        qrCode和控制台输出
        """

        self.qrframe=ttk.LabelFrame(text="dglab socket qrcode(郊狼socket二维码)")
        self.qrcode=tk.Label(master=self.qrframe,height=220,width=220)
        self.qrcode.pack()
        self.qrframe.place(x=50,y=320,height=250,width=250)

        self.consoleFrame=ttk.LabelFrame(text="console(控制台输出)")
        self.console=ScrolledText(self.consoleFrame)
        self.console.pack(fill='both')
        self.consoleFrame.place(x=320,y=320,height=250,width=550)
   


        """
        底部按钮
        """
        
        self.config=config
        self.restartButton=ttk.Button(text="restart(重启服务)",command=self.restart_server)
        self.restartButton.place(x=450,y=600,width=150,height=50)
        self.closeButton=ttk.Button(text="close(关闭服务)",command=self.close_server)
        self.closeButton.place(x=250,y=600,width=150,height=50)
        self.startButton=ttk.Button(text="start(开启服务)",command=self.start_server)
        self.startButton.place(x=50,y=600,width=150,height=50)     
        self.saveButton=ttk.Button(text="save_config(保存配置)",command=self.save_config)
        self.saveButton.place(x=650,y=600,width=150,height=50)
        self.saveButton=ttk.Button(text="debug",command=self.debug)
        self.saveButton.place(x=650,y=650,width=50,height=30)
        """
        顶部全局配置输入框
        """
        self.ipaddress = tk.StringVar(value=self.config["ipAddress"])
        self.ipaddress.trace_add(mode="write",callback=self._setIpaddress)
        self.APP_IP_Label=ttk.Label(text="local IP(本机局域网ip,无特殊情况无需填写)")
        self.APP_IP_Label.place(x=50,y=20,width=250,height=30)
        self.APP_IP_Entry = ttk.Entry(textvariable=self.ipaddress)
        self.APP_IP_Entry.place(x=300,y=20,width=150,height=30)

        self.sleepTime = tk.StringVar(value=self.config["sleepTime"])
        self.sleepTime.trace_add(mode="write",callback=self._setSleepTime)
        self.sleepTime_Label=ttk.Label(text="package interval time(数据包间隔时间)")
        self.sleepTime_Label.place(x=550,y=20,width=250,height=30)
        self.sleepTime_Entry = ttk.Entry(textvariable=self.sleepTime)
        self.sleepTime_Entry.place(x=800,y=20,width=50,height=30)





        """
        osc参数设置
        """
        self.oscSettingsFrame=ttk.Labelframe(text="VRCHAT settings(VRC OSC参数监听设置)")
        self.oscSettingsFrame.place(x=50,y=60,height=250)


        """
        avatarParameter(模型参数)
        """
        self.avatarParameterFrame=ttk.Labelframe(master=self.oscSettingsFrame,text="avatarParameter(模型参数)")
        
        self.avatarParameterSelectedId=None
        self.avatarParameter_EntryText=tk.StringVar()
        self.avatarParameter=tk.StringVar(value=self._getAvatarParameter()) 

        self.avatarParameter_Entry=ttk.Entry(master=self.avatarParameterFrame,textvariable=self.avatarParameter_EntryText)
        self.avatarParameter_Scroll=tk.Scrollbar(master=self.avatarParameterFrame)
        self.avatarParameter_Listbox=tk.Listbox(master=self.avatarParameterFrame,listvariable=self.avatarParameter,width=25,yscrollcommand=self.avatarParameter_Scroll.set)
        self.avatarParameter_Scroll['command']=self.avatarParameter_Listbox.yview
        self.avatarParameter_Listbox.bind(sequence='<<ListboxSelect>>',func=self.avatarParameterListboxSelect)
        self.avatarParameter_change_buttom=ttk.Button(master=self.avatarParameterFrame,text='修改参数',command=self.changeAvatarParameterName,width=8)
        self.avatarParameter_Add_buttom=ttk.Button(master=self.avatarParameterFrame,text='增加参数',command=self.addAvatarParameterName,width=8)
        self.avatarParameter_remove_buttom=ttk.Button(master=self.avatarParameterFrame,text='删除参数',command=self.removeAvatarParameterName,width=8)

        self.avatarParameterFrame.pack(side="left",fill="y")
        self.avatarParameter_Entry.pack(side='top',fill='x')
        self.avatarParameter_Listbox.pack(side="left",fill='y')
        self.avatarParameter_Scroll.pack(side='left',fill='y')
        self.avatarParameter_change_buttom.pack()
        self.avatarParameter_Add_buttom.pack()
        self.avatarParameter_remove_buttom.pack()

        """
        judgeValue(判断段参数)
        """
        self.judgeValueFrame=ttk.Labelframe(master=self.oscSettingsFrame,text="judgeValue(判断段参数)")

        self.judgeValueSelectedId=None
        self.judgeValue_EntryText=tk.StringVar()
        self.judgeValue=tk.StringVar()
        self.judgeMode=tk.StringVar()
        self.judgeMode.trace_add(mode="write",callback=self._setJudgeMode)
        self.judgeModeFrame=ttk.Frame(master=self.judgeValueFrame)
        self.judgeModeLable=ttk.Label(master=self.judgeModeFrame,text="judgeMode(判断模式)")
        self.judgeMode_Combobox=ttk.Combobox(master=self.judgeModeFrame,textvariable=self.judgeMode,values=["等于","大于","小于"],state='readonly',width=15)

        self.judgeValue_Entry=ttk.Entry(master=self.judgeValueFrame,textvariable=self.judgeValue_EntryText,validate="key",validatecommand=(self.register(self.validate_Float_1),"%P"))
        
        self.judgeValue_Scroll=tk.Scrollbar(master=self.judgeValueFrame)
        self.judgeValue_Listbox=tk.Listbox(master=self.judgeValueFrame,listvariable=self.judgeValue,width=25,yscrollcommand=self.judgeValue_Scroll.set)
        self.judgeValue_Scroll['command']=self.judgeValue_Listbox.yview
        self.judgeValue_Listbox.bind(sequence='<<ListboxSelect>>',func=self.judgeValueListboxSelect)
        self.judgeValueFrame_change_buttom=ttk.Button(master=self.judgeValueFrame,text='修改参数',command=self.changeJudgeValueName,width=8)
        self.judgeValueFrame_Add_buttom=ttk.Button(master=self.judgeValueFrame,text='增加参数',command=self.addJudgeValueName,width=8)
        self.judgeValueFrame_remove_buttom=ttk.Button(master=self.judgeValueFrame,text='删除参数',command=self.removeJudgeValueName,width=8)

        self.judgeValueFrame.pack(side="left",fill="y")
        self.judgeModeLable.pack(side="left")
        self.judgeMode_Combobox.pack(side="right")
        self.judgeModeFrame.pack(side="top",fill='x')
        self.judgeValue_Entry.pack(side='top',fill='x')
        self.judgeValue_Listbox.pack(side="left",fill='y')
        self.judgeValue_Scroll.pack(side='left',fill='y')
        self.judgeValueFrame_change_buttom.pack()
        self.judgeValueFrame_Add_buttom.pack()
        self.judgeValueFrame_remove_buttom.pack()

        """
        judgeSettings(判断条件)
        """
        self.judegeSettingFrame=ttk.Labelframe(master=self.oscSettingsFrame,text="judgeSettings(判断条件)")
        
        self.judgePattern=tk.StringVar()
        self.judgeChannel=tk.StringVar()
        self.judgeIntensity=tk.StringVar()
        self.judgeTicks=tk.StringVar()


        self.judgePatternFrame=ttk.Frame(master= self.judegeSettingFrame)
        self.judgePattern_Label=ttk.Label(master=self.judgePatternFrame,text="pattern(波形)")
        self.judgePattern_Combobox=ttk.Combobox(master=self.judgePatternFrame,textvariable=self.judgePattern,values=self._getPatterns(),state='readonly')

        self.judgeChannelFrame=ttk.Frame(master= self.judegeSettingFrame)
        self.judgeChannel_Label=ttk.Label(master=self.judgeChannelFrame,text="Channel(通道)")
        self.judgeChannel_Combobox=ttk.Combobox(master=self.judgeChannelFrame,textvariable=self.judgeChannel,values=["A","B"],state='readonly')

        self.judgeIntensityFrame=ttk.Frame(master= self.judegeSettingFrame)
        self.judgeIntensity_Label=ttk.Label(master=self.judgeIntensityFrame,text='Intensity(通道强度) 0%-100%')
        self.judgeIntensity_Entry=ttk.Entry(master= self.judgeIntensityFrame,textvariable=self.judgeIntensity,validate="key",validatecommand=(self.register(self.validate_Int_100),"%P"))

        self.judgeTicksFrame=ttk.Frame(master= self.judegeSettingFrame)
        self.judgeTicks_Label=ttk.Label(master=self.judgeTicksFrame,text="Ticks(单次输出时间) 0-100 0.1s为单位")
        self.judgeTicks_Entry=ttk.Entry(master= self.judgeTicksFrame,textvariable=self.judgeTicks,validate="key",validatecommand=(self.register(self.validate_Int_100),"%P"))

        self.judgeSettingSaveButton=ttk.Button(master=self.judegeSettingFrame,text="save(保存判断条件)",command=self.saveJudgeSettings)

        self.judegeSettingFrame.pack(side="left",fill="y")
        self.judgePattern_Label.pack(side="left")
        self.judgePattern_Combobox.pack(side="right")
        self.judgePatternFrame.pack(fill="x")
        self.judgeChannel_Label.pack(side="left")
        self.judgeChannel_Combobox.pack(side="right")
        self.judgeChannelFrame.pack(fill="x")
        self.judgeIntensity_Label.pack(anchor="w")
        self.judgeIntensity_Entry.pack(fill="x")
        self.judgeIntensityFrame.pack(fill="x")
        self.judgeTicks_Label.pack(anchor="w")
        self.judgeTicks_Entry.pack(fill="x")
        self.judgeTicksFrame.pack(fill="x")
        self.judgeSettingSaveButton.pack()
        self.after(1000,self.start_Tread)



    def start_Tread(self):
        self.dgserver.start()
        self.p.start()
        self.after(2000,self.update_image)




    def update_image(self):

        image_path = "qrcode.png"
        image = Image.open(image_path)
        image_tk=image.resize((200,200))

        img=ImageTk.PhotoImage(image_tk)
        self.qrcode.img=img
        self.qrcode.configure(image=img)

    def validate_Int_100(self,value):
        if value == "":return True
        if value.isdigit():
            if int(value)<=100:
                return True
            
        return False
    def validate_Float_1(self,value):
        if value =='':return True
        if value =='-':return True
        try:
            f=float(value)
            if f>1.1:return False
            return True
        except ValueError:
            return False
        
    def avatarParameterListboxSelect(self,event):
        selectedId=self.avatarParameter_Listbox.curselection()
        if len(selectedId)!=0:
            self.avatarParameterSelectedId=selectedId[0]
            tuple_str=self.avatarParameter.get()
            selectedValue=ast.literal_eval(tuple_str)
            # print(type(data),data)

            # selectedValue=tuple(str(item[1:-1]) for item in self.avatarParameter.get()[1:-1].split(', '))
            self.avatarParameter_EntryText.set(selectedValue[self.avatarParameterSelectedId])
            judgeValues=self._getJudgeValues(self.avatarParameterSelectedId)
            self.judgeValue.set(judgeValues)
            self.judgeMode_Combobox.current(self._getJudgeMode(self.avatarParameterSelectedId))
            self.judgeValue_EntryText.set("")
            self.judgePattern.set("")
            self.judgeChannel.set("")
            self.judgeIntensity.set("")
            self.judgeTicks.set("")
        
    

    def judgeValueListboxSelect(self,event):
        selectedId=self.judgeValue_Listbox.curselection()
        if len(selectedId)!=0:
            self.judgeValueSelectedId=selectedId[0]
            selectedValue=ast.literal_eval(self.judgeValue.get())
            # selectedValue=tuple(str(item[1:-1]) for item in self.judgeValue.get()[1:-1].split(', '))
            self.judgeValue_EntryText.set(selectedValue[self.judgeValueSelectedId])
            self.judgePattern_Combobox.current(self._getJudgePatternindex(self._getJudgeSettingValue("pattern")))
            self.judgeChannel_Combobox.current(self._getJudgeChannelindex(self._getJudgeSettingValue("channel")))
            self.judgeIntensity.set(self._getJudgeSettingValue("intensity"))
            self.judgeTicks.set(self._getJudgeSettingValue("ticks"))

    def changeAvatarParameterName(self):
        name=self.avatarParameter_EntryText.get()
        if name!='' and self.avatarParameterSelectedId is not None:
            self.config["oscSettings"][self.avatarParameterSelectedId]["avatarParameter"]="/avatar/parameters/"+name
            self.avatarParameter.set(self._getAvatarParameter())
            

    def addAvatarParameterName(self):
        name=self.avatarParameter_EntryText.get()
        if name!='':
            data=copy.deepcopy(defaultConfig["oscSettings"][0])
            data["avatarParameter"]="/avatar/parameters/"+name
            self.config["oscSettings"].append(data)
            self.avatarParameter.set(self._getAvatarParameter())
            self.avatarParameter_Listbox.selection_set(self.avatarParameter_Listbox.size()-1)
            self.avatarParameterListboxSelect(None)

    def removeAvatarParameterName(self):
        if self.avatarParameterSelectedId is not None and self.avatarParameterSelectedId<self.avatarParameter_Listbox.size():
            del self.config["oscSettings"][self.avatarParameterSelectedId]
            self.avatarParameter.set(self._getAvatarParameter())
            self.avatarParameter_EntryText.set('')
            self.clearJudgeValues()
            self.clearJudgeSettings()

    def changeJudgeValueName(self):
        name=self.judgeValue_EntryText.get()
        if name !='' and self.avatarParameterSelectedId is not None and self.judgeValueSelectedId is not None:
            self.config["oscSettings"][self.avatarParameterSelectedId]["judgeSettings"][self.judgeValueSelectedId]["value"]=float(name)
            self.judgeValue.set(self._getJudgeValues(self.avatarParameterSelectedId))

    def addJudgeValueName(self):
        name=self.judgeValue_EntryText.get()
        if name !='' and self.avatarParameterSelectedId is not None :
            data=copy.deepcopy(defaultConfig["oscSettings"][0]["judgeSettings"][0])
            data["value"]=float(name)
            self.config["oscSettings"][self.avatarParameterSelectedId]["judgeSettings"].append(data)
            self.judgeValue.set(self._getJudgeValues(self.avatarParameterSelectedId))

    def removeJudgeValueName(self):
        if self.avatarParameterSelectedId is not None and self.judgeValueSelectedId is not None and self.judgeValueSelectedId<self.judgeValue_Listbox.size():
            del self.config["oscSettings"][self.avatarParameterSelectedId]["judgeSettings"][self.judgeValueSelectedId]
            self.judgeValue.set(self._getJudgeValues(self.avatarParameterSelectedId))
            self.clearJudgeSettings()
    def saveJudgeSettings(self):
        if self.avatarParameterSelectedId is not None and self.judgeValueSelectedId is not None:
            base=self.config["oscSettings"][self.avatarParameterSelectedId]["judgeSettings"][self.judgeValueSelectedId]
            base["pattern"]=self.judgePattern.get()
            base["channel"]=self.judgeChannel.get()
            base["intensity"]=int(self.judgeIntensity.get())
            base["ticks"]=float(self.judgeTicks.get())
            self.write_local_log("save Judge Settings,已保存判断条件")

    def clearJudgeValues(self):
        self.judgeMode.set('')
        self.judgeValue_EntryText.set('')
        self.judgeValue.set('')

    def clearJudgeSettings(self):
        self.judgePattern.set("")
        self.judgeChannel.set("")
        self.judgeIntensity.set('')
        self.judgeTicks.set('')
    def _setIpaddress(self,name,index,traceMode):
        self.config["ipAddress"]=self.ipaddress.get()
    def _setJudgeMode(self,name,index,traceMode):
        if self.avatarParameterSelectedId is not None and self.judgeMode.get()!='':
            self.config["oscSettings"][self.avatarParameterSelectedId]["mode"]=["等于","大于","小于"].index(self.judgeMode.get())
    def _getAvatarParameter(self):
        avatarParameter=''
        i=0
        for i in range(0,len(self.config["oscSettings"])):
            avatarParameter+=self.config["oscSettings"][i]["avatarParameter"].split('/',3)[3]
            avatarParameter+=' '
        return avatarParameter
    def _getJudgeMode(self,index)->int:
        return int(self.config["oscSettings"][index]["mode"])
    def _getJudgeValues(self,index)->str:
        judgeValues=''
        for i in range(0,len(self.config["oscSettings"][index]["judgeSettings"])):
            judgeValues+=str(float(self.config["oscSettings"][index]["judgeSettings"][i]['value']))
            judgeValues+=' '
        return judgeValues
    def _getJudgePattern(self,index,valueIndex):
        judgeValues=''
        for i in range(0,len(self.config["oscSettings"][index]["judgeSettings"])):
            judgeValues+=str(self.config["oscSettings"][index]["judgeSettings"][i]['value'])
            judgeValues+=' '
        return judgeValues
    def _getPatterns(self):
        return list(self.pattern.keys())
    def _getJudgeSettingValue(self,item):
        return self.config["oscSettings"][self.avatarParameterSelectedId]["judgeSettings"][self.judgeValueSelectedId][item]
    def _getJudgePatternindex(self,value):
        return self._getPatterns().index(value)
    def _getJudgeChannelindex(self,value):
        return ["A","B"].index(value)
        
    def _setSleepTime(self,name,index,traceMode):
        if self.sleepTime.get()!='':
            self.config["sleepTime"]=int(self.sleepTime.get())

    def restart_server(self):
        self.write_local_log("start to close server")
        self.close_server()
        time.sleep(2)
        self.write_local_log("server closed")
        self.start_server()

    def start_server(self):
        self.osc_exit_event.clear()
        self.p=ServerTread(self,self.osc_exit_event,dgServer=self.dgserver)
        self.p.start()
        self.write_local_log("server start")
        time.sleep(1)
    def close_server(self):
        self.osc_exit_event.set()
        self.write_local_log("server close")
        time.sleep(1)
    def save_config(self):
        with open('config.json', 'w+', encoding="utf8") as f:
            f.write(json.dumps(self.config,ensure_ascii=False))
            self.write_local_log("config saved,已保存配置文件")
        self.restart_server()
    def write_console(self,text):
        self.console.insert('end',text+'\n')
        self.console.see('end')
    def write_local_log(self,text:str):
        windowLog.info(text)
        self.write_console(text)
    def debug(self):
        print(self.judgeValue_Listbox.size())
        print(self.config["ipAddress"])
        print(self.avatarParameter_Listbox.curselection())
        print(self.config)



class DGLabServerTread(Thread):
    def __init__(self,master:App) -> None:
        super().__init__()
        self.daemon=True
        self.frame=master
        self.bind_event=Event()
        self.strengthData:StrengthData=None
        self.task=None

    def run(self):
        self.task=asyncio.run(self.serverStart())
        dglabLog.info('dglabServer stopped')
    def create_qrcode(self,data):
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
        image=self.create_qrcode(data)

        image.save('qrcode.png')
        # image.show()

    def wirte_log(self,text:str):
        dglabLog.warning(text)
        self.frame.write_console(text)


        

    async def serverStart(self):
        async with DGLabWSServer("0.0.0.0", 5678, 60) as server:
            self.client = server.new_local_client()
            if self.frame.config["ipAddress"]=="":ip=str(socket.gethostbyname(socket.getfqdn()))
            else: ip=self.frame.config["ipAddress"]
            url = self.client.get_qrcode(f"ws://{ip}:5678")
            self.wirte_log("请用 DG-Lab App 扫描二维码以连接")
            
            self.print_qrcode(url)
            

            # 等待绑定
            await self.client.bind()
            self.wirte_log(f"已与 App {self.client.target_id} 成功绑定")
            self.bind_event.set()

            async for data in self.client.data_generator(FeedbackButton, RetCode,StrengthData):
                if isinstance(data,StrengthData):
                    self.strengthData=data
                    self.strengthData

                    
                # if isinstance(data, FeedbackButton):
                #     dglabLog.info(f"App 触发了反馈按钮：{data.name}")

                #     if data == FeedbackButton.A1:
                #         # 顺序发送波形
                #         dglabLog.info("对方按下了 A 通道圆圈按钮")

                # 接收 心跳 / App 断开通知
                elif data == RetCode.CLIENT_DISCONNECTED:
                    self.wirte_log("App 已断开连接，你可以尝试重新扫码进行连接绑定")
                    self.bind_event.clear()
                    await self.client.rebind()
                    self.bind_event.set()
                    self.wirte_log("重新绑定成功")
    


class ServerTread(Thread):
    def __init__(self,master:App,exit_event:Event,dgServer:DGLabServerTread=None) -> None:
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
            serverLog.info("please restart exe||请重启服务")
        except  Exception as e:
            serverLog.error("cannot Find OSC please open after VRCHAT started")
            serverLog.error(f"unexcepted error:{e}|type:{type(e)}")

    def run(self):
        self.task=asyncio.run(self.webSocketstart())
        self.write_log_info('oscserver closed')
                
    async def webSocketstart(self):
        last_id=list()
        for i in range(0,len(self.config["oscSettings"])):last_id.append(None)
        while not self.exit_event.is_set():
            self.dgServer.bind_event.wait(timeout=5)
            if not self.dgServer.bind_event.is_set(): 
                self.write_log_info("waiting for dgserver bind 等待dglab socket扫码绑定")
                continue
            maxtick=0
            try:
                for i in range(0,len(self.config["oscSettings"])):
                    node = self.OSCclient.query_node(self.config["oscSettings"][i]["avatarParameter"])
                    id=self.judge(i,value=node.value[0])
                    if id is not None :
                        ticks=int(self.config["oscSettings"][i]["judgeSettings"][id]["ticks"])
                        if self.config["oscSettings"][i]["mode"]in[0,1,2]:
                            
                            tickstime=await self.sendMessage(i,id,ticks)
                            if maxtick<tickstime:maxtick=tickstime
                        if self.config["oscSettings"][i]["mode"]==3 and id==-1:
                            tickstime=await self.sendMessage(i,id,ticks)
                            if maxtick<tickstime:maxtick=tickstime
                        if self.config["oscSettings"][i]["mode"]==4:
                            if last_id[i]is None:
                                last_id[i]==id
                                time.sleep(1)
                            if last_id[i]is not None and last_id[i]!=id:
                                last_id[i]==id
                                tickstime=await self.sendMessage(i,id,ticks)
                                if maxtick<tickstime:maxtick=tickstime  
                time.sleep(self.config["sleepTime"]+maxtick/10)  
            except TimeoutError:  
                self.write_log_warning("Timeout,Sever cannot connect to APP,please check APP||连接超时,无法连接至APP请检查APP是否处于运行状态")
                time.sleep(1)
            except AttributeError:
                self.write_log_warning("Server cannot get value,please check avatar parameters or VRCHAT||无法检测到指定的模型参数,请检查模型参数是否正确")
                time.sleep(1)
            except ConnectionRefusedError:
                self.write_log_warning("ConnectionRefused,Server cannot to APP,please check APP||无法连接致手机APP,请检查手机APP是否开启")
                time.sleep(1) 
            except  Exception as e:
                self.write_log_error(f"unexcepted error:{e}|type:{type(e)}")
                time.sleep(1)
                continue


    def write_log_info(self,text:str):
        serverLog.info(text)
        self.frame.write_console(text)
    
    def write_log_warning(self,text:str):
        serverLog.warning(text)
        self.frame.write_console(text)
        
    def write_log_error(self,text:str):
        serverLog.error(text)
        self.frame.write_console(text)

    async def sendMessage(self,i,id,ticks):
            pattern_name=self.config["oscSettings"][i]["judgeSettings"][id]["pattern"]
            pattern=self.patterns[pattern_name]
            channel=self.getChannel(self.config["oscSettings"][i]["judgeSettings"][id]["channel"])

            looptime=self.getPatternLoopTime(pattern_name,ticks)
            inCorrectIntensity,expected_intensity=self.isInCorrectIntensity(i,id,channel)
            if inCorrectIntensity is None:
                self.write_log_error(f"unexcepted intensity error")
                return None
            if not inCorrectIntensity: 
                self.write_log_info(f"SetStrength:{expected_intensity}")
                await self.dgServer.client.set_strength(channel,StrengthOperationType.SET_TO,expected_intensity)
            await self.dgServer.client.add_pulses(channel,*(pattern*looptime))
            self.write_log_info(f"Sent|channel:{channel}|name:{pattern_name}|intensity:{expected_intensity}|strength Data:{self.dgServer.strengthData}|ticks:{ticks}|time:{len(pattern)/10*looptime} s")
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
                if value>=judgeValue[index]["value"]:return index
            elif mode==2:
                if value<=judgeValue[index]["value"]:return index
            elif mode==3:
                return -1
            elif mode==4:
                if value==judgeValue[index]["value"]:return index
            else:
                serverLog.error(f"unexpected json 参数错误 mode{i} error ")
        return None

    def getChannel(self,value):
        if value=='A':return Channel.A
        if value=='B':return Channel.B
        self.write_log_error(f"unexpected json 参数错误 channel error ") 

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

    





if __name__ == '__main__':
    try:
        with open('config.json', 'r', encoding="utf8") as f:
            config = json.load(f)
    except FileNotFoundError:
        with open('config.json', 'w+', encoding="utf8") as f:
            f.write(json.dumps(defaultConfig,ensure_ascii=False))
            config=defaultConfig
    
    windowLog.info("program start")
    root = tk.Tk()
    root.geometry('900x700')
    root.title('VRCHATosc To DGLAB')
    root.resizable(0, 0)
    myapp = App(root,config=config)
    myapp.mainloop()
    myapp.osc_exit_event.set()
    time.sleep(3)

