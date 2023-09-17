# 导入所需的库
import re, random, requests, json
import time
import os
import logging
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import traceback

from urllib.parse import urlparse

import langid

from profanity import profanity
import ahocorasick

import difflib

import shutil
from send2trash import send2trash

from pypinyin import pinyin, Style


class Common:
    # 获取北京时间
    def get_bj_time(self, type=0):
        """获取北京时间

        Args:
            type (int, str): 返回时间类型. 默认为 0.
                0 返回数据：年-月-日 时:分:秒
                1 返回数据：年-月-日
                2 返回数据：当前时间的秒
                3 返回数据：自1970年1月1日以来的秒数
                4 返回数据：返回自1970年1月1日以来的毫秒数 % 100
                5 返回数据：当前 时点分
                6 返回数据：当前时间的 时, 分

        Returns:
            str: 返回指定格式的时间字符串
            int, int
        """
        if type == 0:
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)  # 获取当前 UTC 时间
            SHA_TZ = timezone(
                timedelta(hours=8),
                name='Asia/Shanghai',
            )
            beijing_now = utc_now.astimezone(SHA_TZ)  # 将 UTC 时间转换为北京时间
            fmt = '%Y-%m-%d %H:%M:%S'
            now_fmt = beijing_now.strftime(fmt)
            return now_fmt
        elif type == 1:
            now = datetime.now()  # 获取当前时间
            year = now.year  # 获取当前年份
            month = now.month  # 获取当前月份
            day = now.day  # 获取当前日期

            return str(year) + "-" + str(month) + "-" + str(day)
        elif type == 2:
            now = time.localtime()  # 获取当前时间

            # hour = now.tm_hour   # 获取当前小时
            # minute = now.tm_min  # 获取当前分钟 
            second = now.tm_sec  # 获取当前秒数

            return str(second)
        elif type == 3:
            current_time = time.time()  # 返回自1970年1月1日以来的秒数

            return str(current_time)
        elif type == 4:
            current_time = time.time()  # 返回自1970年1月1日以来的秒数
            current_milliseconds = int(current_time * 1000) # 毫秒为单位
            tgt_time = current_milliseconds % 100 # 用于生成音频文件名

            return str(tgt_time)
        elif type == 5:
            now = time.localtime()  # 获取当前时间

            hour = now.tm_hour   # 获取当前小时
            minute = now.tm_min  # 获取当前分钟

            return str(hour) + "点" + str(minute) + "分"
        elif type == 6:
            now = time.localtime()  # 获取当前时间

            hour = now.tm_hour   # 获取当前小时
            minute = now.tm_min  # 获取当前分钟 

            return hour, minute
    
    # 删除多余单词
    def remove_extra_words(self, text="", max_len=30, max_char_len=50):
        words = text.split()
        if len(words) > max_len:
            words = words[:max_len]  # 列表切片，保留前30个单词
            text = ' '.join(words) + '...'  # 使用join()函数将单词列表重新组合为字符串，并在末尾添加省略号
        return text[:max_char_len]


    # 本地敏感词检测 传入敏感词库文件路径和待检查的文本
    def check_sensitive_words(self, file_path, text):
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = [line.strip() for line in file.readlines()]

        for word in sensitive_words:
            if word in text:
                return True

        return False
    

    # 本地敏感词检测 Aho-Corasick 算法 传入敏感词库文件路径和待检查的文本
    def check_sensitive_words2(self, file_path, text):
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = [line.strip() for line in file.readlines()]

        # 创建 Aho-Corasick 自动机
        automaton = ahocorasick.Automaton()

        # 添加违禁词到自动机中
        for word in sensitive_words:
            automaton.add_word(word, word)

        # 构建自动机的转移函数和失效函数
        automaton.make_automaton()

        # 在文本中搜索违禁词
        for _, found_word in automaton.iter(text):
            logging.warning(f"命中本地违禁词：{found_word}")
            return True

        return False


    # 本地敏感词转拼音检测 传入敏感词库文件路径和待检查的文本
    def check_sensitive_words3(self, file_path, text):
        with open(file_path, 'r', encoding='utf-8') as file:
            sensitive_words = [line.strip() for line in file.readlines()]

        pinyin_text = self.text2pinyin(text)
        # logging.info(f"pinyin_text={pinyin_text}")

        for word in sensitive_words:
            pinyin_word = self.text2pinyin(word)
            pattern = r'\b' + re.escape(pinyin_word) + r'\b'
            if re.search(pattern, pinyin_text):
                logging.warning(f"同音违禁拼音：{pinyin_word}")
                return True

        return False


    # 链接检测
    def is_url_check(self, text):
        parsed_url = urlparse(text)
        return all([parsed_url.scheme, parsed_url.netloc])

        # url_pattern = re.compile(r'(?i)((?:(?:https?|ftp):\/\/)?[^\s/$.?#]+\.[^\s>]+)')

        # if url_pattern.search(text):
        #     return True
        # else:
        #     return False


    # 语言检测
    def lang_check(self, text, need="none"):
        # 语言检测 一个是语言，一个是概率
        language, score = langid.classify(text)

        if need == "none":
            return language
        else:
            if language != need:
                return None
            else:
                return language


    # 判断字符串是否全为标点符号
    def is_punctuation_string(self, string):
        # 使用正则表达式匹配标点符号
        pattern = r'^[^\w\s]+$'
        return re.match(pattern, string) is not None
    

    # 违禁词校验
    def profanity_content(self, content):
        return profanity.contains_profanity(content)


    # 中文语句切分(只根据特定符号切分)
    def split_sentences1(self, text):
        # 使用正则表达式切分句子
        # .的过滤可能会导致 序号类的回复被切分
        sentences = re.split('([。！？!?])', text)
        result = []
        for sentence in sentences:
            if sentence not in ["。", "！", "？", ".", "!", "?", ""]:
                result.append(sentence)
        
        # 替换换行
        result = [s.replace('\n', '。') for s in result]

        # print(result)
        return result
    

    # 文本切分算法 旧算法，有最大长度限制
    def split_sentences2(self, text):
        # 最大长度限制，超过后会强制切分
        max_limit_len = 40

        # 使用正则表达式切分句子
        sentences = re.split('([。！？!?])', text)
        result = []
        current_sentence = ""
        for i in range(len(sentences)):
            if sentences[i] not in ["。", "！", "？", ".", "!", "?", ""]:
                # 去除换行和空格
                sentence = sentences[i].replace('\n', '。')
                # 如果句子长度小于10个字，则与下一句合并
                if len(current_sentence) < 10:
                    current_sentence += sentence
                    # 如果合并后的句子长度超过max_limit_len个字，则进行二次切分
                    if len(current_sentence) > max_limit_len:
                        # 判断是否有分隔符可用于二次切分
                        if i+1 < len(sentences) and len(sentences[i+1]) > 0 and sentences[i+1][0] not in ["。", "！", "？", ".", "!", "?"]:
                            next_sentence = sentences[i+1].replace('\n', '。')
                            # 寻找常用分隔符进行二次切分
                            for separator in [",", "，", ";", "；"]:
                                if separator in next_sentence:
                                    split_index = next_sentence.index(separator) + 1
                                    current_sentence += next_sentence[:split_index]
                                    result.append(current_sentence)
                                    current_sentence = next_sentence[split_index:]
                                    break
                        else:
                            # 如果合并后的句子长度超过max_limit_len个字，进行二次切分
                            while len(current_sentence) > max_limit_len:
                                result.append(current_sentence[:max_limit_len])
                                current_sentence = current_sentence[max_limit_len:]
                else:
                    result.append(current_sentence)
                    current_sentence = sentence

        # 添加最后一句
        if current_sentence:
            result.append(current_sentence)

        # 2次切分长字符串
        result2 = []
        for string in result:
            if len(string) > max_limit_len:
                split_strings = re.split(r"[,，;；。！!]", string)
                result2.extend(split_strings)
            else:
                result2.append(string)

        return result2


    # 文本切分算法
    def split_sentences(self, text):
        # 使用正则表达式切分句子
        sentences = re.split(r'(?<=[。！？!?])', text)
        result = []
        current_sentence = ""
        
        for sentence in sentences:
            # 去除换行和空格
            sentence = sentence.replace('\n', '')
            
            # 如果句子为空则跳过
            if not sentence:
                continue
            
            # 如果句子长度小于10个字，则与下一句合并
            if len(current_sentence) < 10:
                current_sentence += sentence
            else:
                # 判断当前句子是否以标点符号结尾
                if current_sentence[-1] in ["。", "！", "？", ".", "!", "?"]:
                    result.append(current_sentence)
                    current_sentence = sentence
                else:
                    # 如果当前句子不以标点符号结尾，则进行二次切分
                    split_sentences = re.split(r'(?<=[,，;；])', current_sentence)
                    if len(split_sentences) > 1:
                        result.extend(split_sentences[:-1])
                        current_sentence = split_sentences[-1] + sentence
                    else:
                        current_sentence += sentence
        
        # 添加最后一句
        if current_sentence:
            result.append(current_sentence)
        
        return result


    # 字符串匹配算法来计算字符串之间的相似度，并选择匹配度最高的字符串作为结果
    def find_best_match(self, substring, string_list, similarity=0.5):
        """字符串匹配算法来计算字符串之间的相似度，并选择匹配度最高的字符串作为结果

        Args:
            substring (str): 要搜索的子串
            string_list (list): 字符串列表
            similarity (float): 最低相似度

        Returns:
            _type_: 匹配到的字符串 或 None
        """
        best_match = None
        best_ratio = 0
        
        for string in string_list:
            ratio = difflib.SequenceMatcher(None, substring, string).ratio()
            # print(f"String: {string}, Ratio: {ratio}")  # 添加调试语句，输出每个字符串的相似度
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = string
        
        # 如果相似度不到similarity，则认为匹配不成功
        if best_ratio < similarity:
            return None

        return best_match
    

    # 读取指定文件中所有文本内容并返回 如果文件不存在则创建
    def read_file_return_content(self, file_path):
        try:
            if not os.path.exists(file_path):
                logging.warning(f"文件不存在，将创建新文件: {file_path}")
                # 创建文件
                with open(file_path, 'w', encoding='utf-8') as file:
                    content = ""
                return content
        
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except IOError as e:
            logging.error(f"无法写入文件:{file_path}\n{e}")
            return None


    # 写入内容到指定文件中 返回T/F
    def write_content_to_file(self, file_path, content, write_log=True):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            logging.info(f"内容已成功写入文件:{file_path}")

            return True
        except IOError as e:
            logging.error(f"无法写入文件:{file_path}\n{e}")
            return False


    # 将一个文件路径的字符串切分成路径和文件名
    def split_path_and_filename(self, file_path):
        folder_path, file_name = os.path.split(file_path)
        # 检查路径末尾是否已经包含了'/'，如果没有，则添加
        if not folder_path.endswith('/'):
            folder_path += '/'
        
        return folder_path, file_name


    # 移动文件到指定路径 src dest
    def move_file(self, source_path, destination_path, rename=None, format="wav"):
        # if os.path.exists(destination_path):
        #     # 如果目标位置已存在同名文件，则先将其移动到回收站
        #     send2trash(destination_path)
        
        # if rename is not None:
        #     destination_path = os.path.join(os.path.dirname(destination_path), rename)
        
        # shutil.move(source_path, destination_path)
        # logging.info(f"文件移动成功：{source_path} -> {destination_path}")
        destination_directory = os.path.dirname(destination_path)
        destination_filename = os.path.basename(source_path)

        if rename is not None:
            destination_filename = rename + "." + format
        
        destination_path = os.path.join(destination_directory, destination_filename)
        
        if os.path.exists(destination_path):
            # 如果目标位置已存在同名文件，则先删除
            os.remove(destination_path)

        shutil.move(source_path, destination_path)
        print(f"文件移动成功：{source_path} -> {destination_path}")


    # 从文件路径中提取出带有扩展名的文件名
    # 返回：str
    def extract_filename(self, file_path):
        file_name_with_extension = os.path.basename(file_path)
        file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
        return file_name_without_extension


    # 获取指定文件夹下的所有文件夹的名称
    def get_folder_names(self, path):
        folder_names = next(os.walk(path))[1]
        return folder_names


    def get_all_file_paths(self, folder_path):
        """返回指定文件夹内所有文件的文件绝对路径，包括文件扩展名

        Args:
            folder_path (str): 文件夹路径

        Returns:
            list: 文件绝对路径列表
        """
        file_paths = []  # 用于存储文件绝对路径的列表

        # 使用 os.walk 遍历文件夹内所有文件和子文件夹
        for root, directories, files in os.walk(folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)  # 获取文件的绝对路径
                file_paths.append(file_path)

        return file_paths


    # 获取Live2D模型名
    def get_live2d_model_name(self, path):
        content = self.read_file_return_content(path)
        if content is None:
            logging.error(f"读取Live2D模型名失败")
            return None
        
        pattern = r'"(.*?)"'
        result = re.search(pattern, content)

        if result:
            content = result.group(1)
            return content
        else:
            return None


    def text2pinyin(self, text):
        """文本转拼音

        Args:
            text (str): 传入待转换的文本

        Returns:
            str: 拼音字符串
        """
        pinyin_list = []
        for char in text:
            # 把每个汉字转为拼音
            char_pinyin_list = pinyin(char, style=Style.NORMAL)
            if char_pinyin_list:
                _pinyin = char_pinyin_list[0][0]
            else:
                _pinyin = char
            
            # 将ü等转换为v
            _pinyin = re.sub(r"ü", "v", _pinyin)
            
            pinyin_list.append(_pinyin)

        return " ".join(pinyin_list)


    def get_random_value(self, lower_limit, upper_limit):
        """获得2个数之间的随机值

        Args:
            lower_limit (float): 随机数下限
            upper_limit (float): 随机数上限

        Returns:
            float: 2个数之间的随机值
        """
        if lower_limit == upper_limit:
            return round(lower_limit, 2)

        if lower_limit > upper_limit:
            lower_limit, upper_limit = upper_limit, lower_limit

        random_float = round(random.uniform(lower_limit, upper_limit), 2)
        return random_float
    

    def merge_consecutive_asterisks(self, s):
        """合并字符串末尾连续的*

        Args:
            s (str): 待处理的字符串

        Returns:
            str: 处理完后的字符串
        """
        # 从字符串末尾开始遍历，找到连续的*的起始索引
        idx = len(s) - 1
        while idx >= 0 and s[idx] == '*':
            idx -= 1

        # 如果找到了超过3个连续的*，则进行替换
        if len(s) - 1 - idx > 3:
            s = s[:idx + 1] + '*' + s[len(s) - 1:]

        return s


    def remove_extension_from_list(self, file_name_list):
        """
        将包含多个带有拓展名的文件名的列表中的拓展名去掉，只返回文件名部分组成的新列表

        Args:
            file_name_list (list): 包含多个带有拓展名的文件名的列表

        Returns:
            list: 文件名组成的新列表
        """
        # 使用列表推导来处理整个列表，去掉每个文件名的拓展名
        file_name_without_extension_list = [file_name.split('.')[0] for file_name in file_name_list]
        return file_name_without_extension_list


    def is_audio_file(self, file_path):
        """判断文件是否是音频文件

        Args:
            file_path (str): 文件路径

        Returns:
            bool: True / False
        """
        # List of supported audio file extensions
        SUPPORTED_AUDIO_EXTENSIONS = ['.mp3', '.wav', '.MP3', '.WAV', '.ogg']

        _, extension = os.path.splitext(file_path)
        return extension.lower() in SUPPORTED_AUDIO_EXTENSIONS


    def random_search_a_audio_file(self, root_dir):
        """搜索指定文件夹内所有的音频文件，并随机返回一个音频文件路径

        Args:
            root_dir (str): 搜索的文件夹路径

        Returns:
            str: 随机返回一个音频文件路径
        """
        audio_files = []

        for root, dirs, files in os.walk(root_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_dir)
                relative_path = relative_path.replace("\\", "/")

                logging.debug(file_path)

                # 判断文件是否是音频文件
                if self.is_audio_file(relative_path):
                    audio_files.append(file_path)

        if audio_files:
            # 随机返回一个音频文件路径
            return random.choice(audio_files)
        else:
            return None


    # 请求web字幕打印机
    def send_to_web_captions_printer(self, api_ip_port, data):
        """请求web字幕打印机

        Args:
            api_ip_port (str): api请求地址
            data (dict): 包含用户名,弹幕内容

        Returns:
            bool: True/False
        """

        # user_name = data["username"]
        content = data["content"]

        # 记录数据库):
        try:
            response = requests.get(url=api_ip_port + f'/send_message?content={content}')
            response.raise_for_status()  # 检查响应的状态码

            result = response.content
            ret = json.loads(result)

            logging.debug(ret)

            if ret['code'] == 200:
                logging.debug(ret['message'])
                return True
            else:
                logging.error(ret['message'])
                return False
        except Exception as e:
            logging.error('web字幕打印机请求失败！请确认配置是否正确或者服务端是否运行！')
            logging.error(traceback.format_exc())
            return False


    def replace_special_characters(self, input_string, special_characters):
        """
        将指定的特殊字符替换为空字符。

        Args:
            input_string (str): 要替换特殊字符的输入字符串。
            special_characters (str): 包含要替换的特殊字符的字符串。

        Returns:
            str: 替换后的字符串。
        """
        for char in special_characters:
            input_string = input_string.replace(char, "")
        
        return input_string


    # 将cookie数据字符串分割成键值对列表
    def parse_cookie_data(self, data_str, field_name):
        """将cookie数据字符串分割成键值对列表

        Args:
            data_str (str): 待提取数据的cookie字符串
            field_name (str): 要提取的键名

        Returns:
            str: 键所对应的值
        """
        # 将数据字符串分割成键值对列表
        key_value_pairs = data_str.split(';')

        # print(key_value_pairs)

        # 遍历键值对列表，查找指定字段名
        for pair in key_value_pairs:
            key, value = pair.strip().split('=')
            if key == field_name:
                return value

        # 如果未找到指定字段，返回空字符串
        return ""


    # 动态变量替换
    def dynamic_variable_replacement(self, template, data_json):
        """动态变量替换

        Args:
            template (str): 待替换变量的字符串
            data_json (dict): 用于替换的变量json数据

        Returns:
            str: 替换完成后的字符串
        """
        pattern = r"{(\w+)}"
        var_names = re.findall(pattern, template)

        for var_name in var_names:
            if var_name in data_json:
                template = template.replace("{"+var_name+"}", str(data_json[var_name]))
            else:
                # 变量不存在,保留原样
                pass

        logging.debug(f"template={template}")

        return template
