import os, sys
import json
from groq import Groq
import openai, anthropic, mistralai 

# Default key
default_key = ""

def extract_json_from_end(text):
    try:
        return extract_json_from_end_backup(text)
    except:
        pass
    
    json_start = text.find("{")
    if json_start == -1:
        raise ValueError("No JSON object found in the text.")
    
    json_text = text[json_start:]
    json_text = json_text.replace("\\", "")

    ind = len(json_text) - 1
    while json_text[ind] != "}":
        ind -= 1
    json_text = json_text[: ind + 1]

    ind -= 1
    cnt = 1
    while cnt > 0 and ind >= 0:
        if json_text[ind] == "}":
            cnt += 1
        elif json_text[ind] == "{":
            cnt -= 1
        ind -= 1

    json_text = json_text[ind + 1:]

    try:
        jj = json.loads(json_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")

    return jj

def extract_json_from_end_backup(text):
    if "```json" in text:
        text = text.split("```json")[1]
        text = text.split("```")[0]
    ind = len(text) - 1
    while text[ind] != "}":
        ind -= 1
    text = text[: ind + 1]

    ind -= 1
    cnt = 1
    while cnt > 0:
        if text[ind] == "}":
            cnt += 1
        elif text[ind] == "{":
            cnt -= 1
        ind -= 1

    while True:
        ind_comment = text.find("//")
        if ind_comment == -1:
            break
        ind_end = text.find("\n", ind_comment)
        text = text[:ind_comment] + text[ind_end + 1 :]

    jj = json.loads(text[ind + 1 :])
    return jj

def extract_list_from_end(text):
    ind = len(text) - 1
    while text[ind] != "]":
        ind -= 1
    text = text[: ind + 1]

    ind -= 1
    cnt = 1
    while cnt > 0:
        if text[ind] == "]":
            cnt += 1
        elif text[ind] == "[":
            cnt -= 1
        ind -= 1

    jj = json.loads(text[ind + 1 :])
    return jj

def get_response(prompt, model, api_key = None, client=None, max_tokens = 4000, temp=0):
    if not client:
        if api_key is None:
            print("No API Key or Client was given. Reverting to default (llama3-70b-8192)")
            client = Groq(api_key=default_key)
            model = "llama3"
        elif api_key.startswith("gsk_"):
            client = Groq(api_key=api_key)
            # model = model if "llama" in model else "llama3"
        elif api_key.startswith("sk-proj"):
            client = openai.Client(api_key=api_key)
            # model = model if "gpt" in model else "gpt-3.5-turbo"

        elif api_key.startswith("sk-ant-"):
            client = anthropic.Anthropic(api_key=api_key)
            # model = model if "cloude" in model.lower() else "CloudeAI"

        elif api_key.startswith("mkd"):
            client = mistralai.Mistral(api_key=api_key)
            # model = model if model else "mistral-small-latest"

        # Here add diferent api clients
        else:
            print(f"API key not recognized. You can add models API in the {os.path.abspath(__file__)}\ndefoulting to llama3-70b")
            client = Groq(api_key=default_key)
            model = "llama3"

    if client is None:
        raise ValueError("Client Failed to initialize")
    

    if isinstance(client, anthropic.Anthropic) or "claude" in model.lower() or "anthropic" in model.lower():
        chat_completion = client.messages.create(
            model = model if "claude-" in model else "claude-3-5-sonnet-20240620",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temp,
        )
        # print(type(chat_completion.content), "\t", type(chat_completion.content[0].text), flush=True)
        return [chat_completion.content[0].text, client]
    
    elif isinstance(client, mistralai.Mistral) or "mistral" in model.lower():
        chat_completion = client.chat.complete_async(
            model = model if "mistral-" in model else "mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temp,
        )
        # print(type(chat_completion.content), "\t", type(chat_completion.content[0].text), flush=True)
        return [chat_completion.choices[0].message.content, client]
    
    elif isinstance(client, openai.Client) or "gpt" in model.lower():
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model = model if "gpt-" in model else "gpt-3.5-turbo",
            max_tokens=max_tokens,
            temperature=temp,
        )
        return [chat_completion.choices[0].message.content, client]
    else:
        # print(model, "\t", model.lower())
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            max_tokens=max_tokens,
            temperature=temp,
        )
    # print("Not Claude : ", chat_completion.choices[0].message.content)
    return [chat_completion.choices[0].message.content, client]
   

def load_state(state_file):
    with open(state_file, "r") as f:
        state = json.load(f)
    return state

def save_state(state, dir):
    with open(dir, "w") as f:
        json.dump(state, f, indent=4)

def shape_string_to_list(shape_string):
    if type(shape_string) == list:
        return shape_string
    shape_string = shape_string.strip()
    shape_string = shape_string[1:-1]
    shape_list = shape_string.split(",")
    shape_list = [x.strip() for x in shape_list]
    shape_list = [int(x) if x.isdigit() else x for x in shape_list]
    if len(shape_list) == 1 and shape_list[0] == "":
        shape_list = []
    return shape_list

def extract_equal_sign_closed(text):
    ind_1 = text.find("=====")
    ind_2 = text.find("=====", ind_1 + 1)
    obj = text[ind_1 + 6 : ind_2].strip()
    return obj

class Logger:
    def __init__(self, file):
        self.file = file

    def log(self, text):
        with open(self.file, "a") as f:
            f.write(text + "\n")

    def reset(self):
        with open(self.file, "w") as f:
            f.write("")

def create_state(parent_dir, run_dir):
    with open(os.path.join(parent_dir, "params.json"), "r") as f:
        params = json.load(f)

    data = {}
    for key in params:
        data[key] = params[key]["value"]
        del params[key]["value"]

    with open(os.path.join(run_dir, "data.json"), "w") as f:
        json.dump(data, f, indent=4)

    with open(os.path.join(parent_dir, "desc.txt"), "r") as f:
        desc = f.read()

    state = {"description": desc, "parameters": params}
    return state

def get_labels(dir):
    with open(os.path.join(dir, "labels.json"), "r") as f:
        labels = json.load(f)
    return labels
