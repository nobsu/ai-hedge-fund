import logging
import os
from datetime import datetime
from colorama import Fore, Style

class LLMLogger:
    def __init__(self, console_output=False):
        # 创建logs目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # 设置日志文件名（使用时间戳）
        self.log_filename = f"logs/llm_calls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 创建logger
        self.logger = logging.getLogger('ai_hedge_fund')
        self.logger.setLevel(logging.INFO)
        
        # 清除现有的handlers
        self.logger.handlers = []
        
        # 添加文件handler
        file_handler = logging.FileHandler(self.log_filename)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
        # 如果开启控制台输出，添加StreamHandler
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(message)s'  # 控制台输出更简洁
            ))
            self.logger.addHandler(console_handler)
    
    def log_llm_call(self, model_name: str, model_provider: str, agent_name: str, prompt: str, response: str):
        """记录LLM调用的详细信息到日志文件"""
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"Agent: {agent_name}")
        self.logger.info(f"Model: {model_provider} - {model_name}")
        self.logger.info(f"\nPrompt:\n{prompt}")
        self.logger.info(f"\nResponse:\n{response}")
        self.logger.info(f"{'='*50}\n")
    
    def log_error(self, error_msg: str):
        """记录错误信息"""
        self.logger.error(error_msg)

# 创建默认logger实例（不输出到控制台）
llm_logger = LLMLogger(console_output=False)

# 导出便捷函数
def log_llm_call(model_name: str, model_provider: str, agent_name: str, prompt: str, response: str):
    llm_logger.log_llm_call(model_name, model_provider, agent_name, prompt, response)

def log_error(error_msg: str):
    llm_logger.log_error(error_msg)

# 允许外部配置是否输出到控制台
def configure_logger(console_output: bool = False):
    global llm_logger
    llm_logger = LLMLogger(console_output=console_output) 