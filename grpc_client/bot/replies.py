REPLIES = {
    "set":  {
        "chat":    "请设置机器人的工作位置。使用群聊中的消息链接（如 https://t.me/c/1234/567 ）作为参数使机器人在群里工作，"
                   "或者'no'仅在该私聊中使用",
        "address": "请设置执行端gRPC服务器地址"
    },
    "done": {
        "first":        "欢迎使用，启动之前您还需要完成一些必要的配置项目",
        "welcome":      "机器人已启动",
        "private":      "工作位置设置为仅私聊",
        "chat":         "工作位置设置为群组 {}",
        "chat_topic":   "工作位置设置为群组 {} 中的话题 {}",
        "start":        "服务器启动成功",
        "stop":         "服务器已停止",
        "restart":      "服务器已重新启动",
        "command":      "命令已发送",
        "running":      "服务器正在运行",
        "not_running":  "服务器未在运行",
        "grpc_connect": "已连接到位于 {} 的gRPC服务器：{}",
        "extra_args":   "Factorial的启动参数从\n{}\n更改为\n{}",
        "all_conf":     "机器人配置数据如下：\n{}",
        "savelist":     "服务器有以下存档（时间为游戏内时间）：\n{}"
    },
    "err":  {
        # "admin_not_user": "请将管理员设置为用户而不是群组，否则机器人将不会工作",
        "no_manager":     "未设置执行端gRPC服务器",
        "bad_manager":    "位于 {} 的gRPC服务器异常或无法连接， 具体信息已记录到日志",
        "id_invalid":     "无法获取群聊信息，请首先将bot加入群组",
        "not_channel":    "不是有效的群聊",
        "no_savename":    "请在参数中指定存档名称",
        "started":        "服务器正在运行，请先停止服务器或重新启动服务器",
        "stopped":        "服务器未在运行，命令无效",
        "unknown_failed": "执行失败，具体原因已记录到日志",
        "env_notfound":   "环境不对"
    },
    "game": {
        "chat":  "{} 说: {}",
        "join":  "{} 加入了游戏",
        "leave": "{} 离开了游戏"
    }
}
