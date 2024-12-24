import logging
import logging.handlers
def logger(name):
    logger = logging.getLogger(name)

    # 创建一个handler，用于写入日志文件
 # 日志文件路径
    log_file = 'VRCTODGLAB.log'
    # 单个日志文件最大大小
    max_bytes = 1024 * 1024  # 1MB
    # 最多保留的日志文件数
    backup_count = 20
    # 创建 file handler 并设置日志级别
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
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
    # logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    return logger