配置文件如下
```json
{
    #APP上的ip地址
    "ipAddress": "192.168.1.113",
    #第三方控制版本号
    "APPVersion":1,
    "oscSettings": [
        {
            #监控的模型参数
            "avatarParameter": "/avatar/parameters/MuteSelf",
            #判断模式（0：等于；1：大于 2：小于）
            "mode": 0,
            #在判断模式下参数触发值和触发的波形
            "judgeSettings": [
                {
                    "value": 0,#此处为当参数等于零时触发
                    "pattern": "default"
                }
            ]
        },
        {
            "avatarParameter": "/avatar/parameters/Voice",
            "mode": 2,
            #对于大于和小于多值，不用在乎顺序，程序会自动排序，如下方，当Voice=0.2时会触发"12312"
            "judgeSettings": [
                {
                    "value": 0.1,#此处为当参数大于0.1时触发
                    "pattern": "123"#下方 "patternSettings"中波形的名称
                },
                {
                    "value": 1,
                    "pattern": "123123"
                },
                {
                    "value": 0.3,
                    "pattern": "12312"
                }
            ]
        }
    ],
    "sleepTime": 0.1,
    #波形设置，详情见https://github.com/open-toys-controller/open-DGLAB-controller/blob/main/api.md
    "patternSettings": {
        "default": {
            "cmd": "set_pattern",#不需要修改
            "A_intensity": 100,#带A代表a通道强度，B代表B通道，不带代表双通道
            "A_ticks": 10 #持续时长0.1秒为单位，10为一秒
        },
        "123123": {
            "cmd": "set_pattern",
            "B_intensity": 100,
            "B_ticks": 10
        },
        "12312": {
            "cmd": "set_pattern",
            "B_intensity": 80,
            "B_ticks": 10
        },
        "123": {
            "cmd": "set_pattern",
            "B_intensity": 50,
            "B_ticks": 10
        }
    }
}
```