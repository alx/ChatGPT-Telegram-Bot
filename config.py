import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

from utils.i18n import strings
from datetime import datetime
from ModelMerge.src.ModelMerge.utils import prompt
from ModelMerge.src.ModelMerge.models import chatgpt, claude, groq, claude3, gemini, PLUGINS, whisper
from ModelMerge.src.ModelMerge.models.base import BaseAPI

from telegram import InlineKeyboardButton

NICK = os.environ.get('NICK', None)
PORT = int(os.environ.get('PORT', '8080'))
BOT_TOKEN = os.environ.get('BOT_TOKEN', None)

GPT_ENGINE = os.environ.get('GPT_ENGINE', 'gpt-4o')
API_URL = os.environ.get('API_URL', 'https://api.openai.com/v1/chat/completions')
API = os.environ.get('API', None)
WEB_HOOK = os.environ.get('WEB_HOOK', None)
CHAT_MODE = os.environ.get('CHAT_MODE', "global")
GET_MODELS = (os.environ.get('GET_MODELS', "False") == "False") == False

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', None)
GOOGLE_AI_API_KEY = os.environ.get('GOOGLE_AI_API_KEY', None)

PREFERENCES = {
    "PASS_HISTORY"      : (os.environ.get('PASS_HISTORY', "True") == "False") == False,
    "IMAGEQA"             : (os.environ.get('IMAGEQA', "False") == "True") == False,
    "LONG_TEXT"         : (os.environ.get('LONG_TEXT', "True") == "False") == False,
    "LONG_TEXT_SPLIT"   : (os.environ.get('LONG_TEXT_SPLIT', "True") == "False") == False,
    "FILE_UPLOAD_MESS"  : (os.environ.get('FILE_UPLOAD_MESS', "True") == "False") == False,
    "FOLLOW_UP"         : (os.environ.get('FOLLOW_UP', "False") == "False") == False,
    "TITLE"             : (os.environ.get('TITLE', "False") == "False") == False,
    "TYPING"            : (os.environ.get('TYPING', "False") == "False") == False,
    "REPLY"             : (os.environ.get('REPLY', "False") == "False") == False,
}

LANGUAGE = os.environ.get('LANGUAGE', 'English')

LANGUAGES = {
    "English": False,
    "Simplified Chinese": False,
    "Traditional Chinese": False,
    "Russian": False,
}

LANGUAGES_TO_CODE = {
    "English": "en",
    "Simplified Chinese": "zh",
    "Traditional Chinese": "zh-hk",
    "Russian": "ru",
}

current_date = datetime.now()
Current_Date = current_date.strftime("%Y-%m-%d")
systemprompt = os.environ.get('SYSTEMPROMPT', prompt.system_prompt.format(LANGUAGE, Current_Date))
claude_systemprompt = os.environ.get('SYSTEMPROMPT', prompt.claude_system_prompt.format(LANGUAGE))

class UserConfig:
    def __init__(self,
        user_id: str = None,
        language="English",
        api_url="https://api.openai.com/v1/chat/completions",
        api_key=None,
        engine="gpt-4o",
        mode="global",
        preferences=None,
        plugins=None,
        languages=None,
        systemprompt=None,
        claude_systemprompt=None
    ):
        self.user_id = user_id
        self.language = language
        self.languages = languages
        self.languages[self.language] = True
        self.api_url = api_url
        self.api_key = api_key
        self.engine = engine
        self.preferences = preferences
        self.plugins = plugins
        self.systemprompt = systemprompt
        self.claude_systemprompt = claude_systemprompt
        self.users = {
            "global": self.get_init_preferences()
        }
        self.users["global"].update(self.preferences)
        self.users["global"].update(self.plugins)
        self.users["global"].update(self.languages)
        self.mode = mode
        self.parameter_name_list = list(self.users["global"].keys())

    def get_init_preferences(self):
        return {
            "language": self.language,
            "engine": self.engine,
            "systemprompt": self.systemprompt,
            "claude_systemprompt": self.claude_systemprompt,
            "api_key": self.api_key,
            "api_url": self.api_url,
        }

    def user_init(self, user_id = None):
        if user_id == None or self.mode == "global":
            user_id = "global"
        self.user_id = user_id
        if self.user_id not in self.users.keys():
            self.users[self.user_id] = self.get_init_preferences()
            self.users[self.user_id].update(self.preferences)
            self.users[self.user_id].update(self.plugins)
            self.users[self.user_id].update(self.languages)

    def get_config(self, user_id = None, parameter_name = None):
        if parameter_name not in self.parameter_name_list:
            raise ValueError("parameter_name is not in the parameter_name_list")
        if self.mode == "global":
            return self.users["global"][parameter_name]
        if self.mode == "multiusers":
            self.user_init(user_id)
            return self.users[self.user_id][parameter_name]

    def set_config(self, user_id = None, parameter_name = None, value = None):
        if parameter_name not in self.parameter_name_list:
            raise ValueError("parameter_name is not in the parameter_name_list")
        if self.mode == "global":
            self.users["global"][parameter_name] = value
        if self.mode == "multiusers":
            self.user_init(user_id)
            self.users[self.user_id][parameter_name] = value

    def extract_plugins_config(self, user_id = None):
        self.user_init(user_id)
        user_data = self.users[self.user_id]
        plugins_config = {key: value for key, value in user_data.items() if key in self.plugins}
        return plugins_config

Users = UserConfig(mode=CHAT_MODE, api_key=API, api_url=API_URL, engine=GPT_ENGINE, preferences=PREFERENCES, plugins=PLUGINS, language=LANGUAGE, languages=LANGUAGES, systemprompt=systemprompt, claude_systemprompt=claude_systemprompt)

def get_ENGINE(user_id = None):
    return Users.get_config(user_id, "engine")

temperature = float(os.environ.get('temperature', '0.5'))
CLAUDE_API = os.environ.get('claude_api_key', None)

ChatGPTbot, SummaryBot, claudeBot, claude3Bot, groqBot, gemini_Bot, whisperBot = None, None, None, None, None, None, None
def update_ENGINE(data = None, chat_id=None):
    global Users, ChatGPTbot, SummaryBot, claudeBot, claude3Bot, groqBot, gemini_Bot, whisperBot
    if data:
        Users.set_config(chat_id, "engine", data)
    engine = Users.get_config(chat_id, "engine")
    systemprompt = Users.get_config(chat_id, "systemprompt")
    claude_systemprompt = Users.get_config(chat_id, "claude_systemprompt")
    api_key = Users.get_config(chat_id, "api_key")
    api_url = Users.get_config(chat_id, "api_url")
    if api_key:
        if "claude" in engine:
            ChatGPTbot = chatgpt(api_key=f"{api_key}", api_url=api_url, engine=engine, system_prompt=claude_systemprompt, temperature=temperature, convo_id=chat_id)
        else:
            ChatGPTbot = chatgpt(api_key=f"{api_key}", api_url=api_url, engine=engine, system_prompt=systemprompt, temperature=temperature, convo_id=chat_id)
        SummaryBot = chatgpt(api_key=f"{api_key}", api_url=api_url, engine="gpt-3.5-turbo", system_prompt=systemprompt, temperature=temperature, use_plugins=False, convo_id=chat_id)
        whisperBot = whisper(api_key=f"{api_key}", api_url=api_url)
    if CLAUDE_API and "claude-2.1" in engine:
        claudeBot = claude(api_key=f"{CLAUDE_API}", engine=engine, system_prompt=claude_systemprompt, temperature=temperature, convo_id=chat_id)
    if CLAUDE_API and "claude-3" in engine:
        claude3Bot = claude3(api_key=f"{CLAUDE_API}", engine=engine, system_prompt=claude_systemprompt, temperature=temperature, convo_id=chat_id)
    if GROQ_API_KEY and ("mixtral" in engine or "llama" in engine):
        groqBot = groq(api_key=f"{GROQ_API_KEY}", engine=engine, system_prompt=systemprompt, temperature=temperature, convo_id=chat_id)
    if GOOGLE_AI_API_KEY and "gemini" in engine:
        gemini_Bot = gemini(api_key=f"{GOOGLE_AI_API_KEY}", engine=engine, system_prompt=systemprompt, temperature=temperature, convo_id=chat_id)

def update_language_status(language, chat_id=None):
    global Users, ChatGPTbot, SummaryBot, claudeBot, claude3Bot, groqBot, gemini_Bot, whisperBot
    systemprompt = Users.get_config(chat_id, "systemprompt")
    claude_systemprompt = Users.get_config(chat_id, "claude_systemprompt")
    LAST_LANGUAGE = Users.get_config(chat_id, "language")
    Users.set_config(chat_id, "language", language)
    for lang in LANGUAGES:
        Users.set_config(chat_id, lang, False)

    Users.set_config(chat_id, language, True)
    try:
        systemprompt = systemprompt.replace(LAST_LANGUAGE, Users.get_config(chat_id, "language"))
        claude_systemprompt = claude_systemprompt.replace(LAST_LANGUAGE, Users.get_config(chat_id, "language"))
        Users.set_config(chat_id, "systemprompt", systemprompt)
        Users.set_config(chat_id, "claude_systemprompt", claude_systemprompt)
        if ChatGPTbot == None:
            update_ENGINE(chat_id=chat_id)
        if ChatGPTbot:
            ChatGPTbot.system_prompt[chat_id] = systemprompt
        if claude3Bot:
            claude3Bot.system_prompt[chat_id] = claude_systemprompt
        if groqBot:
            groqBot.system_prompt[chat_id] = systemprompt
        if gemini_Bot:
            gemini_Bot.system_prompt[chat_id] = systemprompt
    except Exception as e:
        print("error:", e)
        pass

update_language_status(LANGUAGE)

def get_local_version_info():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(['git', '-C', current_directory, 'log', '-1'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    return output.split('\n')[0].split(' ')[1]  # 获取本地最新提交的哈希值

def get_remote_version_info():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    result = subprocess.run(['git', '-C', current_directory, 'ls-remote', 'origin', 'HEAD'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    return output.split('\t')[0]  # 获取远程最新提交的哈希值

def check_for_updates():
    local_version = get_local_version_info()
    remote_version = get_remote_version_info()

    if local_version == remote_version:
        return "Up to date."
    else:
        return "A new version is available! Please redeploy."

def replace_with_asterisk(string, start=10, end=45):
    if string:
        return string[:start] + '*' * (end - start - 8) + string[end:]
    else:
        return None

def update_info_message(user_id = None):
    api_key = Users.get_config(user_id, "api_key")
    api_url = Users.get_config(user_id, "api_url")
    return "".join([
        f"**🤖 Model:** `{get_ENGINE(user_id)}`\n\n",
        f"**🔑 API:** `{replace_with_asterisk(api_key)}`\n\n" if api_key else "",
        f"**🔗 API URL:** `{api_url}`\n\n" if api_url else "",
        f"**🛜 WEB HOOK:** `{WEB_HOOK}`\n\n" if WEB_HOOK else "",
        f"**🚰 Tokens usage:** `{get_robot(user_id)[0].tokens_usage[str(user_id)]}`\n\n" if get_robot(user_id)[0] else "",
        f"**🃏 NICK:** `{NICK}`\n\n" if NICK else "",
        f"**📖 Version:** `{check_for_updates()}`\n\n",
    ])

def reset_ENGINE(chat_id, message=None):
    global ChatGPTbot, claudeBot, claude3Bot, groqBot, gemini_Bot
    api_key = Users.get_config(chat_id, "api_key")
    api_url = Users.get_config(chat_id, "api_url")
    engine = Users.get_config(chat_id, "engine")
    if message:
        if "claude" in engine:
            Users.set_config(chat_id, "claude_systemprompt", message)
        else:
            Users.set_config(chat_id, "systemprompt", message)
    systemprompt = Users.get_config(chat_id, "systemprompt")
    claude_systemprompt = Users.get_config(chat_id, "claude_systemprompt")
    if api_key and ChatGPTbot:
        if "claude" in engine:
            ChatGPTbot.reset(convo_id=str(chat_id), system_prompt=claude_systemprompt)
        else:
            ChatGPTbot.reset(convo_id=str(chat_id), system_prompt=systemprompt)
    if CLAUDE_API and claudeBot:
        claudeBot.reset(convo_id=str(chat_id), system_prompt=claude_systemprompt)
    if CLAUDE_API and claude3Bot:
        claude3Bot.reset(convo_id=str(chat_id), system_prompt=claude_systemprompt)
    if GROQ_API_KEY and groqBot:
        groqBot.reset(convo_id=str(chat_id), system_prompt=systemprompt)
    if GOOGLE_AI_API_KEY and gemini_Bot:
        gemini_Bot.reset(convo_id=str(chat_id), system_prompt=systemprompt)

def get_robot(chat_id = None):
    global ChatGPTbot, claudeBot, claude3Bot, groqBot, gemini_Bot
    engine = Users.get_config(chat_id, "engine")
    if CLAUDE_API and "claude-2.1" in engine:
        robot = claudeBot
        role = "Human"
    elif CLAUDE_API and "claude-3" in engine:
        robot = claude3Bot
        role = "user"
    elif ("mixtral" in engine or "llama" in engine) and GROQ_API_KEY:
        robot = groqBot
        role = "user"
    elif GOOGLE_AI_API_KEY and "gemini" in engine:
        robot = gemini_Bot
        role = "user"
    else:
        robot = ChatGPTbot
        role = "user"

    return robot, role

whitelist = os.environ.get('whitelist', None)
if whitelist:
    whitelist = [int(id) for id in whitelist.split(",")]
ADMIN_LIST = os.environ.get('ADMIN_LIST', None)
if ADMIN_LIST:
    ADMIN_LIST = [int(id) for id in ADMIN_LIST.split(",")]
GROUP_LIST = os.environ.get('GROUP_LIST', None)
if GROUP_LIST:
    GROUP_LIST = [id for id in GROUP_LIST.split(",")]

def delete_model_digit_tail(lst):
    if len(lst) == 2:
        return "-".join(lst)
    for i in range(len(lst) - 1, -1, -1):
        if not lst[i].isdigit():
            if i == len(lst) - 1:
                return "-".join(lst)
            else:
                return "-".join(lst[:i + 1])

def get_status(chatid = None, item = None):
    return "✅ " if Users.get_config(chatid, item) else "☑️ "

def create_buttons(strings, plugins_status=False, lang="English", button_text=None, Suffix="", chatid=None):
    if plugins_status:
        strings_array = {kv:kv for kv in strings}
    else:
        # 过滤出长度小于15的字符串
        abbreviation_strings = [delete_model_digit_tail(s.split("-")) for s in strings]
        from collections import Counter
        counter = Counter(abbreviation_strings)
        filtered_counter = {key: count for key, count in counter.items() if count > 1}
        # print(filtered_counter)

        strings_array = {}
        for s in strings:
            if delete_model_digit_tail(s.split("-")) in filtered_counter:
                strings_array[s] = s
            else:
                strings_array[delete_model_digit_tail(s.split('-'))] = s

    filtered_strings1 = {k:v for k, v in strings_array.items() if len(k) <= 14}
    # print(filtered_strings1)
    filtered_strings2 = {k:v for k, v in strings_array.items() if len(k) > 14}
    # print(filtered_strings2)

    buttons = []
    temp = []

    for k, v in filtered_strings1.items():
        if plugins_status:
            button = InlineKeyboardButton(f"{get_status(chatid, k)}{button_text[k][lang]}", callback_data=k + Suffix)
        else:
            button = InlineKeyboardButton(k, callback_data=v + Suffix)
        temp.append(button)

        # 每两个按钮一组
        if len(temp) == 2:
            buttons.append(temp)
            temp = []

    # 如果最后一组不足两个，也添加进去
    if temp:
        buttons.append(temp)

    for k, v in filtered_strings2.items():
        if plugins_status:
            button = InlineKeyboardButton(f"{get_status(chatid, k)}{button_text[k][lang]}", callback_data=k + Suffix)
        else:
            button = InlineKeyboardButton(k, callback_data=v + Suffix)
        buttons.append([button])

    return buttons

initial_model = [
    "gpt-4o",
    "gpt-4o-mini",
    "claude-3-opus-20240229",
    "claude-3-5-sonnet-20240620",
    # "gpt-4-turbo-2024-04-09",
    # "gpt-3.5-turbo",
    # "claude-3-haiku-20240307",
]

if GROQ_API_KEY:
    initial_model.extend([
        "mixtral-8x7b-32768",
        "llama3-70b-8192",
    ])
if GOOGLE_AI_API_KEY:
    initial_model.extend([
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ])

if GET_MODELS:
    try:
        endpoint = BaseAPI(api_url=API_URL)
        endpoint_models_url = endpoint.v1_models
        import requests
        response = requests.post(
            endpoint_models_url,
            headers={"Authorization": f"Bearer {API}"},
        )
        # response = requests.get(endpoint_models_url)
        models = response.json()
        models_list = models["data"]
        models_id = [model["id"] for model in models_list]
        set_models = set()
        for model_item in models_id:
            set_models.add(delete_model_digit_tail(model_item.split("-")))
        models_id = list(set_models)
        # print(models_id)
        initial_model = models_id
    except Exception as e:
        print("error:", e)
        pass

CUSTOM_MODELS = os.environ.get('CUSTOM_MODELS', None)
if CUSTOM_MODELS:
    CUSTOM_MODELS_LIST = [id for id in CUSTOM_MODELS.split(",")]
    # print("CUSTOM_MODELS_LIST", CUSTOM_MODELS_LIST)
else:
    CUSTOM_MODELS_LIST = None
if CUSTOM_MODELS_LIST:
    delete_models = [model[1:] for model in CUSTOM_MODELS_LIST if model[0] == "-"]
    for target in delete_models:
        for model in initial_model:
            if target in model:
                initial_model.remove(model)

    initial_model.extend([model for model in CUSTOM_MODELS_LIST if model not in initial_model and model[0] != "-"])

def get_current_lang(chatid=None):
    current_lang = Users.get_config(chatid, "language")
    return LANGUAGES_TO_CODE[current_lang]

def update_models_buttons(chatid=None):
    lang = get_current_lang(chatid)
    buttons = create_buttons(initial_model, Suffix="_MODELS")
    buttons.append(
        [
            InlineKeyboardButton(strings['button_back'][lang], callback_data="BACK"),
        ],
    )
    return buttons

def update_first_buttons_message(chatid=None):
    lang = get_current_lang(chatid)
    first_buttons = [
        [
            InlineKeyboardButton(strings["button_change_model"][lang], callback_data="MODELS"),
            InlineKeyboardButton(strings['button_preferences'][lang], callback_data="PREFERENCES"),
        ],
        [
            InlineKeyboardButton(strings['button_language'][lang], callback_data="LANGUAGE"),
            InlineKeyboardButton(strings['button_plugins'][lang], callback_data="PLUGINS"),
        ],
    ]
    return first_buttons

def update_menu_buttons(setting, _strings, chatid):
    lang = get_current_lang(chatid)
    setting_list = list(setting.keys())
    buttons = create_buttons(setting_list, plugins_status=True, lang=lang, button_text=strings, chatid=chatid, Suffix=_strings)
    buttons.append(
        [
            InlineKeyboardButton(strings['button_back'][lang], callback_data="BACK"),
        ],
    )
    return buttons