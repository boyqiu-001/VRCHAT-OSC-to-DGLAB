import logging

def logger(name):
    logger = logging.getLogger(name)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler('test.log')
    fh.setLevel(logging.INFO)
    # 再创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #设置日志打印格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #fh ch还有添加打印格式
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger