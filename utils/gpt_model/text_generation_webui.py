import json, logging
import requests

from utils.common import Common
from utils.logger import Configure_logger

class TEXT_GENERATION_WEBUI:
    def __init__(self, data):
        self.common = Common()
        # 日志文件路径
        file_path = "./log/log-" + self.common.get_bj_time(1) + ".txt"
        Configure_logger(file_path)

        # 配置过多，点到为止，需要的请自行修改
        # http://127.0.0.1:5000
        self.api_ip_port = data["api_ip_port"]
        self.max_new_tokens = data["max_new_tokens"]
        self.mode = data["mode"]
        self.character = data["character"]
        self.instruction_template = data["instruction_template"]
        self.your_name = data["your_name"]

        self.history_enable = data["history_enable"]
        self.history_max_len = data["history_max_len"]

        self.history = {"internal": [], "visible": []}

    # 合并函数
    def merge_jsons(self, json_list):
        merged_json = {"internal": [], "visible": []}
        
        for json_obj in json_list:
            merged_json["internal"].extend(json_obj["internal"])
            merged_json["visible"].extend(json_obj["visible"])
        
        return merged_json
    
    def remove_first_group(self, json_obj):
        """
        删除 JSON 对象中 'internal' 和 'visible' 列表的第一组数据。
        """
        if json_obj["internal"]:
            json_obj["internal"].pop(0)
        if json_obj["visible"]:
            json_obj["visible"].pop(0)
        return json_obj

    def get_text_generation_webui_resp(self, user_input):
        request = {
            'user_input': user_input,
            'max_new_tokens': self.max_new_tokens,
            'history': self.history,
            'mode': self.mode,  # Valid options: 'chat', 'chat-instruct', 'instruct'
            'character': self.character, # 'TavernAI-Gawr Gura'
            'instruction_template': self.instruction_template,
            'your_name': self.your_name,

            'regenerate': False,
            '_continue': False,
            'stop_at_newline': False,
            'chat_generation_attempts': 1,
            'chat-instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',

            # Generation params. If 'preset' is set to different than 'None', the values
            # in presets/preset-name.yaml are used instead of the individual numbers.
            'preset': 'None',
            'do_sample': True,
            'temperature': 0.7,
            'top_p': 0.1,
            'typical_p': 1,
            'epsilon_cutoff': 0,  # In units of 1e-4
            'eta_cutoff': 0,  # In units of 1e-4
            'tfs': 1,
            'top_a': 0,
            'repetition_penalty': 1.18,
            'repetition_penalty_range': 0,
            'top_k': 40,
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'mirostat_mode': 0,
            'mirostat_tau': 5,
            'mirostat_eta': 0.1,

            'seed': -1,
            'add_bos_token': True,
            'truncation_length': 2048,
            'ban_eos_token': False,
            'skip_special_tokens': True,
            'stopping_strings': []
        }

        try:
            response = requests.post(self.api_ip_port + "/api/v1/chat", json=request)

            if response.status_code == 200:
                result = response.json()['results'][0]['history']
                # logging.info(json.dumps(result, indent=4))
                # print(result['visible'][-1][1])
                resp_content = result['visible'][-1][1]

                # 启用历史就给我记住！
                if self.history_enable:
                    while True:
                        # 统计字符数
                        total_chars = sum(len(item) for sublist in self.history['internal'] for item in sublist)
                        total_chars += sum(len(item) for sublist in self.history['visible'] for item in sublist)
                        logging.info(f"total_chars={total_chars}")
                        # 如果大于限定最大历史数，就剔除第一个元素
                        if total_chars > self.history_max_len:
                            self.history = self.remove_first_group(self.history)
                        else:
                            self.history = result
                            break

                return resp_content
            else:
                return None
        except Exception as e:
            logging.info(e)
            return None


    # 源于官方 api-example.py
    def get_text_generation_webui_resp2(self, prompt):
        request = {
            'prompt': prompt,
            'max_new_tokens': self.max_new_tokens,

            # Generation params. If 'preset' is set to different than 'None', the values
            # in presets/preset-name.yaml are used instead of the individual numbers.
            'preset': 'None',  
            'do_sample': True,
            'temperature': 0.7,
            'top_p': 0.1,
            'typical_p': 1,
            'epsilon_cutoff': 0,  # In units of 1e-4
            'eta_cutoff': 0,  # In units of 1e-4
            'tfs': 1,
            'top_a': 0,
            'repetition_penalty': 1.18,
            'repetition_penalty_range': 0,
            'top_k': 40,
            'min_length': 0,
            'no_repeat_ngram_size': 0,
            'num_beams': 1,
            'penalty_alpha': 0,
            'length_penalty': 1,
            'early_stopping': False,
            'mirostat_mode': 0,
            'mirostat_tau': 5,
            'mirostat_eta': 0.1,

            'seed': -1,
            'add_bos_token': True,
            'truncation_length': 2048,
            'ban_eos_token': False,
            'skip_special_tokens': True,
            'stopping_strings': []
        }

        response = requests.post(self.api_ip_port + "/api/v1/generate", json=request)

        try:
            if response.status_code == 200:
                result = response.json()['results'][0]['text']
                print(prompt + result)

                return result
            else:
                return None
        except Exception as e:
            logging.error(e)
            return None
