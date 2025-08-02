# -*- coding: utf-8 -*-

from psychopy.experiment import Experiment
from psychopy.experiment.loops import TrialHandler,LoopTerminator, LoopInitiator
from psychopy.experiment.routines import Routine
from psychopy.data.utils import importConditions
import tkinter as tk
import json
import base64
from tkinter import ttk, filedialog, messagebox
import threading
import shutil
import os
import requests
import tkinter.font as tkfont
from psychopy.experiment.components import getComponents
from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript


uploaded_files = [] 

def get_all_components_text():
    all_comps = getComponents(fetchIcons=False)
    texts=""
    for comp in all_comps:
        if comp not in ["SettingsComponent", "VariableComponent", "UnknownComponent","StaticComponent"]:
            texts+=f"{comp}: {all_comps[comp].tooltip}\n"
    return texts
def get_all_components_list():
    all_comps = getComponents(fetchIcons=False)
    list_i=[]
    for comp in all_comps:
        if comp not in ["SettingsComponent", "VariableComponent", "UnknownComponent","StaticComponent"]:
            list_i.append(comp)
    return list_i

def get_loop_params():
    myexp=Experiment()
    loop = TrialHandler(myexp, "loop")
    texts=""
    
    for param in loop.params:
        allowed=""
        allowed_up=""
        if param in ["conditions","endPoints","random seed"]:
            continue
        defult_value = loop.params[param].val
        if defult_value is None or defult_value == "":
            defult_value = ""
        else:
            defult_value=f",defult={defult_value}"
        #print(param)
        if len(loop.params[param].allowedVals) > 0:
            allowed= f"Allowed values: {loop.params[param].allowedVals}. "
        if loop.params[param].allowedUpdates:
            if len(loop.params[param].allowedUpdates) > 0:
                allowed_up= f"Allowed updates: {loop.params[param].allowedUpdates}. "
        
        texts+=f"{param}({loop.params[param].valType}{defult_value}): {loop.params[param].hint}. {allowed}{allowed_up}\n"
    return texts

def get_components_params(names):
    import inspect
    try:
        myexp=Experiment()
        all_comps = getComponents(fetchIcons=False)
        texts=""
        for name in names:
            if name not in all_comps and name not in ["LoopStart","LoopEnd"]:
                texts+=f"Component {name} not exist.\n"
                continue
            if name in ["LoopStart","LoopEnd"]:
                if name=="LoopEnd":
                     texts+="LoopEnd dosen't need any param.\n"
                else:
                    texts+=f"{name}:\n"
                    texts+=get_loop_params()
            else:
                comp = all_comps[name]
                comp_instance = comp(exp=myexp,parentName= "parentName") 
                allowed_up=""
                sig = inspect.signature(comp_instance.__init__)
                texts+=f"{name}:\n"
                for param in comp_instance.params:
                    allowed=""
                    defult_value= ""
                    if param in ['startEstim', 'durationEstim']:
                        continue
                    else:
                        defult_value = comp_instance.params[param].val
                        if defult_value is None or defult_value == "":
                            defult_value = ""
                        else:
                            defult_value=f",defult={defult_value}"
                    #print(param)
                    if len(comp_instance.params[param].allowedVals) > 0:
                        allowed= f"Allowed values: {comp_instance.params[param].allowedVals}. "
                    if comp_instance.params[param].allowedUpdates:
                        if len(comp_instance.params[param].allowedUpdates) > 0:
                            allowed_up= f"Allowed updates: {comp_instance.params[param].allowedUpdates}. "
                    
                    texts+=f"{param}({comp_instance.params[param].valType}{defult_value}): {comp_instance.params[param].hint}. {allowed}{allowed_up}\n"
            texts+="\n"
        return texts
    except Exception as e:
        #显示错误位置
        import traceback
        error_info = traceback.format_exc()
        print(f"Error in get_components_params: {error_info}")
        return f"Error in get_components_params: {str(e)}"

def get_experiment_params():
        myexp=Experiment()
        all_comps = getComponents(fetchIcons=False)
        texts=""
        
        comp = all_comps["SettingsComponent"]
        comp_instance = comp(exp=myexp,parentName= "parentName") 
        allowed_up=""
        for param in comp_instance.params:
            allowed=""
            defult_value= ""
            if param in ['expName',"color","colorSpace","Units"]:
                defult_value = comp_instance.params[param].val
                if defult_value is None or defult_value == "":
                    defult_value = ""
                else:
                    defult_value=f",defult={defult_value}"
                if len(comp_instance.params[param].allowedVals) > 0:
                    allowed= f"Allowed values: {comp_instance.params[param].allowedVals}. "
                if comp_instance.params[param].allowedUpdates:
                    if len(comp_instance.params[param].allowedUpdates) > 0:
                        allowed_up= f"Allowed updates: {comp_instance.params[param].allowedUpdates}. "
                
                texts+=f"{param}({comp_instance.params[param].valType}{defult_value}): {comp_instance.params[param].hint}. {allowed}{allowed_up}\n"
        return texts

def files_to_text():
    global uploaded_files
    if not uploaded_files:
        return False,"No files uploaded."
    texts=""
    for file in uploaded_files:
        if ".psyexp" in file:
            exp_settings,flow=load_flow(file["filepath"])
            file_info = f"{file['filename']}: {file['desc']}\n exp_settings:{exp_settings}\nflow:{flow}\n\n"
            texts += file_info
        elif file.get("desc"):
            if file.get("desc"):
                file_info = f"{file['filename']}: {file['desc']}\n"
                texts += file_info
    return True,texts

def files_to_work_Folder(work_Folder="GPTExp"):
    global uploaded_files

    if not os.path.exists(work_Folder):
        os.makedirs(work_Folder)
    #清空工作文件夹
    for filename in os.listdir(work_Folder):
        if filename!= "gpt_exp.psyexp":
            file_path = os.path.join(work_Folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                return False, f"Error clearing work folder: {str(e)}"
    for file in uploaded_files:
        filepath = file.get("filepath")
        if filepath and os.path.exists(filepath):
            filename = file.get("filename", os.path.basename(filepath))
            dest_path = os.path.join(work_Folder, filename)
            try:
                with open(filepath, 'rb') as src_file:
                    with open(dest_path, 'wb') as dest_file:
                        dest_file.write(src_file.read())
            except Exception as e:
                return False, f"Error saving file {filename}: {str(e)}"
    return True, "Files saved successfully."
#print(get_all_components_text())
#print(get_loop_params())
#print(get_experiment_params())
#print(get_components_params(["TextComponent", "CodeComponent", "KeyboardComponent"]))
def load_flow(file):
    expObject = Experiment()
    myexp=Experiment()
    expObject.loadFromXML(file)
    settings={}
    for param in ['expName',"color","colorSpace","Units"]:
        if expObject.settings.params[param].val!=myexp.settings.params[param].val:
            settings[param]=expObject.settings.params[param].val

    flow_list=[]
    routines_have={}
    for part in expObject.flow:
        if type(part) == LoopInitiator:
            loop = part.loop
            loop_params = []
            loop_defult=TrialHandler(myexp,"")
            for param in loop.params:
                val = loop.params[param].val
                # 只保存非默认值
                if val not in [loop_defult.params[param].val,str(loop_defult.params[param].val)] and param not in ["conditions"]:
                    loop_params.append({
                    "name": param,
                    "val": str(val),
                    "update": ""
                    })
            flow_item = {
            "name": loop.name,
            "type": "LoopStart",
            "components": [{
                "type": "LoopStart",
                "params": loop_params
            }]
            }
            flow_list.append(flow_item)
        elif type(part) == LoopTerminator:
            flow_item = {
            "name": part.name,
            "type": "LoopEnd",
            "components": [{
                "type": "LoopEnd",
                "params": []
            }]
            }
            flow_list.append(flow_item)
        else:
            # Routine
            routine = part
            comps = []
            if routine.name in routines_have:
                pass
            else:
                routines_have[routine.name]=routine
                for comp in routine:
                    comp_defult=comp.__class__(myexp,"")
                    params = []
                    for param in comp.params:
                        if comp.__class__.__name__=="CodeComponent":
                            if comp.params["Code Type"].val=="Auto->JS":
                                if "JS" in param:
                                    continue
                        val = comp.params[param].val
                        # 只保存非默认值
                        if val not in [str(comp_defult.params[param].val),comp_defult.params[param].val]:
                            update = comp.params[param].updates if hasattr(comp.params[param], "updates") else ""
                            if update=="None":
                                update=""
                            params.append({
                                "name": param,
                                "val": str(val),
                                "update": update if update and update!='constant' else ""
                            })
                    comps.append({
                        "type": comp.__class__.__name__,
                        "params": params
                    })
            flow_item = {
            "name": routine.name,
            "type": "Routine",
            "components": comps
            }
            flow_list.append(flow_item)
    return settings,flow_list

def build_flow(exp_settings,flow, work_Folder="GPTExp"):
    print("build_flow Start...")
    #保存exp_settings,flow字段到工作目录下的build_flow.json文件
    try:
        save_path = os.path.join(work_Folder, "build_flow.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump({"exp_settings": exp_settings, "flow": flow}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving build_flow.json: {str(e)}")
    try:
        missing_message=""
        myexp = Experiment()
        #更新myexp.settings
        for param, value in exp_settings.items():
            if param in myexp.settings.params and param:
                myexp.settings.params[param].val = value
            else:
                print(f"Warning: 参数 {param} 在实验设置中不存在")
                missing_message+=f"Error: 参数 {param} 在实验设置中不存在\n"
        # 解析 JSON 数据并构建实验流程
        i= 0
        routines_have={}
        loops_have={}
        
        for flow_data in flow:
            if flow_data['name'] in routines_have:
                myexp.flow.addRoutine(routines_have[flow_data['name']], i)
            else:
                if flow_data["type"]=="Routine":
                    routine = Routine(flow_data['name'], myexp)
                    for component_data in flow_data.get('components', []):
                        if component_data['type'] not in getComponents():
                            print(f"Warning: 组件 {component_data['type']} 不存在")
                            missing_message+=f"Error: 组件 {component_data['type']} 不存在\n"
                            continue
                        comp_class = getComponents().get(component_data['type'])
                        if comp_class:
                            component = comp_class(myexp, routine.name)
                            # 设置组件参数
                            for param in component_data.get('params', []):
                                if param["name"] in component.params:
                                    if (param["val"] == "true" or param["val"] == "false") and component.params[param["name"]].valType == "bool":
                                        param["val"] = param["val"].capitalize()
                                        
                                    component.params[param["name"]].val=param["val"]
                                    if "update" in param and param["update"]!="":
                                        component.params[param["name"]].updates = param["update"]
                                else:
                                    print(f"Warning: 参数 {param['name']} 在组件 {component_data['type']} 设置中不存在")
                                    missing_message+=f"Error: 参数 {param['name']} 在组件 {component_data['type']} 设置中不存在\n"
                            #如果是code组件，且Code Type为Auto->JS，则自动translatePythonToJavaScript到相应的JS部分，例如Begin Experiment 转换后设置为Begin JS Experiment，如果translatePythonToJavaScript返回False,则设置为/* Syntax Error: Fix Python code */
                            if component_data['type'] == "CodeComponent":
                                if component.params["Code Type"] == "Auto->JS":
                                    # 遍历所有 code 参数
                                    for param in component_data.get('params', []):
                                        if param["name"] not in ["name","Code Type","disabled"] and "JS" not in param["name"] :
                                            py_code = param["val"]
                                            if py_code:
                                                js_code = translatePythonToJavaScript(py_code)
                                                if not js_code:
                                                    js_code = "/* Syntax Error: Fix Python code */"
                                                # 设置 JS 代码到对应 JS 参数
                                                js_param_name = param["name"].replace(" ", " JS ")
                                                if js_param_name in component.params:
                                                    component.params[js_param_name].val = js_code
                            routine.append(component)
                    myexp.addRoutine(routine.name, routine)
                    myexp.flow.addRoutine(routine, i)
                    routines_have[flow_data['name']] = routine
                elif flow_data["type"]=="LoopStart":
                    loop = TrialHandler(myexp, flow_data['name'])
                    loop_data=flow_data["components"][0]
                    codition_file_have=False
                    codition_file_name=""
                    for param in loop_data.get('params', []):
                        
                        if param["name"]=='conditionsFile':
                            if param["val"]:
                                codition_file_have=True
                                codition_file_name=param["val"]
                        if param["name"] in loop.params:
                            if (param["val"] == "true" or param["val"] == "false") and loop.params[param["name"]].valType == "bool":
                                param["val"] = param["val"].capitalize()
                            loop.params[param["name"]].val=param["val"]
                        else:
                            print(f"Warning: 参数 {param['name']} 在循环设置中不存在")
                            missing_message+=f"Error: 参数 {param['name']} 在循环设置中不存在\n"
                    if codition_file_have:
                        #检查是否存在
                        if os.path.exists(work_Folder+'\\'+codition_file_name):
                            condition=importConditions(work_Folder+'\\'+codition_file_name)
                            loop.params['conditions'].val= condition
                        else:
                            print(f"Warning: 条件文件 {codition_file_name} 不存在")
                            missing_message+=f"Error: 条件文件 {codition_file_name} 不存在\n"
                    loops_have[flow_data['name']]=loop
                    myexp.flow.append(LoopInitiator(loop))
                elif flow_data["type"]=="LoopEnd":
                    if flow_data['name'] not in loops_have:
                        missing_message+=f"Loop {flow_data['name']} end before start!"
                        print(f"Loop {flow_data['name']} end before start!")
                        return False, missing_message
                    myexp.flow.append(LoopTerminator(loops_have[flow_data['name']]))
                    myexp.requirePsychopyLibs(['data'])
            i += 1
        myexp.saveToXML(work_Folder+'\\gpt_exp')
        if missing_message!="": 
            return True, missing_message
        print("Build success.")
        return True,"Experiment flow built successfully."  
    except Exception as e:
        print(f"Error building experiment flow: {str(e)}")
        return False, f"Error building experiment flow: {str(e)}"

functions = [
    {
        "type": "function",
        "function": {
        "name": "get_components_param",
        "description": "Obtain parameter information for one or multiple components as well as LoopStart.",
        "parameters": {
            "type": "object",
            "properties": {
                "names": {
                    "type": "array",
                    "items": {"type": "string", "description": "Component Name", "enum": ["LoopStart"]+get_all_components_list()},
                    "description": "Component name list. It is not supported to query the parameters of experiment (provided). Please try to query all Component at once.",
                }
            },
            "required": ["names"],"additionalProperties": False
        },"strict":True
    }},


    { "type": "function",
     "function":
    {
        "name": "build_flow",
        "description": "Constructing Experimental Flow from Structural Data",
        "parameters": {
            "type": "object",
            "properties": {
                "exp_settings": {
                    "type": "object",
                    "description": "Experiment setting parameters. Set '' to use defult value",
                    "properties": {
                        "expName": {"type": "string"},
                        "color": {"type": "string"},
                        "colorSpace": {"type": "string"},
                        "Units": {"type": "string"}
                    },"additionalProperties": False,"required": ["expName","color","colorSpace","Units"]
                },

                "flow": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "description": "The list of each routine, loopstart and loopend should be listed in the order of the process.",
                        "properties": {
                            "name": {"type": "string", "description": "Name of experimental stage"},
                            "type": {"type": "string", "description": "Type of experimental stage", "enum": ["LoopStart","LoopEnd","Routine"]},
                            "components": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "description": "Parameter setting",
                                    "properties": {
                                        "type": {"type": "string", "description": "Specific component types","enum":  ["LoopStart","LoopEnd"]+get_all_components_list()},
                                        "params": {
                                            "type": "array",
                                            "description": "Component parameters. Do not provide fields with default values. For stopval, startval except code and the size, pos and units parameters of visual stimulation in some components, the default values cannot be maintained, and specific values must be provided. If stopval is an empty string, it means it is displayed Without stopping.",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string", "description": "Parameter name"},
                                                    "val": {"type": "string", "description": "Parameter value"},
                                                    "update": {"type": "string","enum":  ["","set every repeat","set every frame"] ,"description": "Update method, default to constant and set it '' if use default value. Not applicable to LoopStart and some Component parameters, set it ''"}
                                                },
                                                "required": ["name", "val","update"],"additionalProperties": False
                                            }
                                        }
                                    },
                                    "required": ["type","params"],"additionalProperties": False
                                }
                            }
                        },
                        "required": ["name","type", "components"],"additionalProperties": False
                    }
                },
            },
            "required": ["exp_settings", "flow"],"additionalProperties": False
        },"strict": True
    }}
]

def build_system_prompt():
    prompt = ""
    prompt += f"""You are an expert in psychopy and an experimental design assistant who helps users build experiment. Your main task is to construct PsychoPy experiment flows according to user requirements, operating within the PsychoPy Builder.
A complete PsychoPy experiment essentially consists of the following two parts:
1. Experiment Settings: Overall settings for the experiment.
    You can modify the following parameters:
    {get_experiment_params()}

2. Flow: The flow is composed of Routine, LoopStart, and LoopEnd, connected according to a specific experimental procedure. Each Routine contains multiple components (such as text, images, keyboard, etc.) for presenting stimuli and collecting responses. LoopStart and LoopEnd control the repeated presentation of all Routines and Loops (nested Loops) between them.
    For components of the Routine, you can use the following components:
    {get_all_components_text()}

You can use tow functions to fulfill user requests:

1. get_components_param: Use this function to find any components and LoopStart parameters you need. Try to find all the components and LoopStart you need at once. LoopEnd has no parameters.
2. build_flow: use this function to build a flow from the list of process components. You need to provide exp_settings and flow parameters.
    For exp_settings, you specify the overall settings of the experiment. Unless it is necessary to modify the default value, you only need to provide the expname parameter.
    For flow, you need to provide a list in order by the experimental stage, including multiple LoopStart, LoopEnd or Routine ".
        Each list element needs to provide three parts: name, type (select one from LoopStart/LoopEnd/Routine) and components.
            For a Routine, components is a list of single or multiple components, indicating that they are in the same Routine. The type of each element can be any component except LoopStart and LoopEnd. Params of each element is the list of attribute dictionaries of each component, providing the parameter name and val to be modified.
            For a LoopStart, components is a single element list, and the type of its unique element must also be LoopStart. The params of this element is the attribute dictionary list of LoopStart.
            For a LoopEnd, components is a single element list, and the type of its unique element must also be LoopEnd. There is no need to provide any parameters for LoopEnd, so params should be an empty list. However, LoopEnd must have the same name as its corresponding LoopStart.
    
When fulfilling user requests, communicate carefully and clarify their needs. But the questions should be reasonable and not overly detailed. For functions that the user did not explicitly mention, do not ask whether they need to be added or not. All questions should be limited to clarifying the experimental functions proposed by the user. For some parameter settings, such as position and size, if the user does not provide them, you need to evaluate and set them yourself, and do not ask for all of them. Then, consider which components are required to complete the experiment flow and how many loops are required. 
Then, use the get_components_param to find the parameters of the required components and LoopStart at once.
Next, carefully consider the logical sequence of the entire experiment flow. How to connect the Routines to form the main experimental process. What components are there in each Routine. How to set the parameters of these components. Where and what does the stimulus component present, and for how long? Is key press or other forms of feedback required? How many Loops are needed, where do their starts and ends lie, and how to set their parameters?
Finally, once you are certain the design meets the user's requirements, you must use the build_flow function to construct the experiment flow. 
For all components, the name cannot remain at the default setting. Additionally, for some components, the stopVal, startVal, and for visual stimuli, the size, pos, and units parameters must be provided with specific values and cannot be left at their default settings.
For other optional parameters (from experiment settings, component settings, or LoopStart settings), if you do not need to set them or want to keep default values, you do not need to include them in the parameter list.
After build the flow successly, do not explain too much, only indicate that the experiment is complete.

Tips:
- When constructing the flow, ensure each routine name is unique to avoid duplication. Unless you want to reuse an existing routine, in which case just provide the Routine with same name but no parameters.
- For all component and LoopStart names, ensure they are not duplicated; components must not be reused.
- For some string-type parameter settings, PsychoPy allows code settings by prefixing the code text with a $ symbol, e.g., $target (from a variable in the loop's condition file, which can be used directly with $). You can use these code settings to dynamically modify parameter values, but don't forget to set the update method (updates) to "set every repeat" or "set every frame" to ensure it takes effect each repeat or frame. Note: code-type parameters do not need the $ symbol, as they are written as code.
- The update parameter for components defaults to "constant". If you need to modify a parameter every repeat or frame, explicitly set its update method.
- If design details are unclear, ask the user for more information to ensure your design meets their needs.
- Users may provide file resources (such as instruction images, condition tables, stimuli materials) for use in the experiment flow. If necessary files are missing, first consider how to achieving the requirements without these files. Unless you believe there is no way to bypass these files, you can ask the user for them, or assume certain files and use them, but explain this before construction and get user approval.
- For all types of visual stimuli, pay attention to the unit parameter, which can not be defaults. It is best to explicitly set it to "norm" (normalized coordinates, screen size from -1 to 1, center at [0,0], top-left at [-1,1]) to ensure consistent display across different screen resolutions, unless the user specifies otherwise. After the unit is determined, the positions and sizes of all components as well as the font size should change accordingly.
- You can use code components to implement complex user requirements, but ensure their position and logic are correct. Common code includes setting parameters for subsequent components and calling them with $, storing data with trials.addData(key, value), checking keyresponse.keys == 'k', etc. trials and keyresponse are specific to the flow and component names, so modify them accordingly.
- Please confirm that the text and pattern stimulus color is different from the experimental background color. The color set in the experiment remains the default unless required by the user.

Warning! 
- All names for components, loopStart,LoopEnd, experiments, and routines must not contain spaces or special characters (such as Chinese); only letters, numbers(not in the first), and underscores are allowed.
- Some data recording for components, such as reaction time and key presses, will be performed automatically and does not require manual addition or a code component. Unless the user specifically requests it, or if some data needs to be calculated and stored, then a code component is needed to implement it.
- Properties from components and loops, such as thisN, cannot be used directly, and must be extracted from 'loopname.thisN'.
"""
    return prompt

class ChatApp:
    def __init__(self, root):
        self.root = root
        root.title("PsychoPy GPT Builder")
        root.geometry("520x650")
        root.minsize(400, 450)
        root.configure(bg="#f0f0f0")

        self.settings = {
            "base_url": "https://api.openai.com",
            "api_key": "",
            "model": "gpt-4.1",
            "work_folder": "GPTExp"
        }
        self.load_settings()  # 加载设置
        menu_bar = tk.Menu(root)
        #settings_menu = tk.Menu(menu_bar, tearoff=0)
        #settings_menu.add_command(label="Settings", command=self.open_settings_window)
        menu_bar.add_cascade(label="Settings", command=self.open_settings_window)
        root.config(menu=menu_bar)

        self.check_and_create_work_folder()


        #设置图标
        icon_path = os.path.join(os.path.dirname(__file__), r"Lib\site-packages\psychopy\app\Resources\builder.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
        else:
            print(f"Icon file not found: {icon_path}")
        self.messages=[]
        self.messages.append({"role": "system", "content": build_system_prompt()})

        # ----- 聊天区 -----
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill="both", expand=True)

        self.chat_canvas = tk.Canvas(self.main_frame, bg="#f0f0f0", highlightthickness=0)
        self.chat_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.chat_canvas.yview)

        self.chat_inner = tk.Frame(self.chat_canvas, bg="#f0f0f0")
        self.chat_inner_id = self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")

        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_scrollbar.pack(side="right", fill="y")

        self.chat_inner.bind("<Configure>", self.on_frame_configure)
        self.chat_canvas.bind("<Configure>", self.on_canvas_configure)

        # ----- 输入区 -----
        self.input_frame = tk.Frame(root, bg="#e0e0e0")
        self.input_frame.pack(fill="x", side="bottom", padx=10, pady=5)

        self.input_frame.columnconfigure(0, weight=1)  # 输入框左侧
        self.input_frame.columnconfigure(1, weight=0)  # 右侧按钮区

        self.user_input = tk.Text(self.input_frame, height=4, font=("Arial", 12), wrap="word")
        self.user_input.grid(row=0, column=0, rowspan=2, sticky="nsew", pady=5, padx=(0,10))

        self.button_frame = tk.Frame(self.input_frame, bg="#e0e0e0")
        self.button_frame.grid(row=0, column=1, rowspan=2, sticky="ns")

        self.resource_button = tk.Button(self.button_frame, text="Source", width=8, font=("Arial", 11), command=self.open_resource_window)
        self.resource_button.pack(side="top", fill="x", pady=(8,10))

        self.send_button = tk.Button(self.button_frame, text="Send", width=8, font=("Arial", 11), bg="#4CAF50", fg="white", command=self.send_message)
        self.send_button.pack(side="top", fill="x")

        self.status_label = tk.Label(root, text="", fg="blue", bg="#f0f0f0", font=("Arial", 10))
        self.status_label.pack(side="bottom", pady=(0,5))

        self.user_input.bind("<Return>", self.on_enter)
        self.chat_canvas.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows
        self.chat_canvas.bind_all("<Button-4>", self._on_mousewheel)    # Linux
        self.chat_canvas.bind_all("<Button-5>", self._on_mousewheel)    # Linux

    def check_and_create_work_folder(self):
        if not os.path.exists(self.settings["work_folder"]):
            os.makedirs(self.settings["work_folder"])
    def center_window(self,parent, window, width, height):
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # 计算弹窗的位置，使其居中于父窗口
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2-50

        # 设置弹窗位置
        window.geometry(f"{width}x{height}+{x}+{y}")
    def load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                #逐个更改
                for key in self.settings.keys():
                    if key in settings:
                        self.settings[key] = settings[key]
                # 解密 API Key
                if self.settings.get("api_key"):
                    self.settings["api_key"] = base64.b64decode(self.settings["api_key"]).decode("utf-8")
        except FileNotFoundError:
            print("未找到设置文件，使用默认设置。")
        except Exception as e:
            print(f"加载设置时出错: {e}")

    def save_settings(self):
        try:
            settings_to_save = self.settings.copy()
            # 加密 API Key
            if settings_to_save.get("api_key"):
                settings_to_save["api_key"] = base64.b64encode(settings_to_save["api_key"].encode("utf-8")).decode("utf-8")
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
            print("设置已保存。")
        except Exception as e:
            print(f"保存设置时出错: {e}")

    def open_settings_window(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Settings")
        self.center_window(self.root, settings_win, 400, 200)
        settings_win.grab_set()  # 模态窗口
        icon_path = os.path.join(os.path.dirname(__file__), r"Lib\site-packages\psychopy\app\Resources\builder.ico")
        if os.path.exists(icon_path):
            settings_win.iconbitmap(icon_path)
        # Base URL
        # 调用 center_window 函数，将窗口定位到主界面附近
        

        tk.Label(settings_win, text="Base URL:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        base_url_entry = tk.Entry(settings_win, font=("Arial", 11), width=40)
        base_url_entry.grid(row=0, column=1, padx=10, pady=5)
        base_url_entry.insert(0, self.settings["base_url"])

        # API Key
        tk.Label(settings_win, text="API Key:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        api_key_entry = tk.Entry(settings_win, font=("Arial", 11), width=40, show="*")  # 隐藏输入
        api_key_entry.grid(row=1, column=1, padx=10, pady=5)
        api_key_entry.insert(0, self.settings["api_key"])

        tk.Label(settings_win, text="Model:", font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        model_entry = tk.Entry(settings_win, font=("Arial", 11), width=40) 
        model_entry.grid(row=2, column=1, padx=10, pady=5)
        model_entry.insert(0, self.settings["model"])

        # 工作目录
        tk.Label(settings_win, text="Work Folder:", font=("Arial", 11)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        work_folder_entry = tk.Entry(settings_win, font=("Arial", 11), width=40)
        work_folder_entry.grid(row=3, column=1, padx=10, pady=5)
        work_folder_entry.insert(0, self.settings["work_folder"])

        # 保存按钮
        def save_and_apply():
            self.settings["base_url"] = base_url_entry.get().strip()
            self.settings["api_key"] = api_key_entry.get().strip()
            self.settings["model"] = model_entry.get().strip()
            self.settings["work_folder"] = work_folder_entry.get().strip()
            self.save_settings()
            self.check_and_create_work_folder()  # 检查并创建工作目录
            settings_win.destroy()

        save_button = tk.Button(settings_win, width=15,text="Save", bg="#4CAF50", fg="white", font=("Arial", 11), command=save_and_apply)
        save_button.grid(row=4, column=0, columnspan=2, pady=10)

        # 布局调整
        settings_win.grid_columnconfigure(1, weight=1)

    def _on_mousewheel(self, event):
        # Windows滚轮
        if event.num == 5 or event.delta < 0:
            self.chat_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.chat_canvas.yview_scroll(-1, "units")
    def _on_mousewheels(self, event):
        # Windows滚轮
        if event.num == 5 or event.delta < 0:
            self.canvas_files.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0:
            self.canvas_files.yview_scroll(-1, "units")

    def on_enter(self, event):
        self.send_message()
        return "break"

    def on_frame_configure(self, event=None):
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
        canvas_width = self.chat_canvas.winfo_width()
        self.chat_canvas.itemconfig(self.chat_inner_id, width=canvas_width)

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.chat_canvas.itemconfig(self.chat_inner_id, width=canvas_width)

    def add_message(self, message, sender, with_button=False):
        # 创建消息框架
        msg_frame = tk.Frame(self.chat_inner, bg="#f0f0f0")
        msg_frame.pack(fill="x", pady=3, padx=10)

        max_bubble_width = int(self.chat_inner.winfo_width() * 0.7)
        if max_bubble_width <= 0:
            max_bubble_width = 350

        bubble_bg = "#dcf8c6" if sender == "user" else "#ffffff"

        # 左侧 Label
        bubble = tk.Label(
            msg_frame,
            text=message,
            bg=bubble_bg,
            font=("Arial", 11),
            wraplength=max_bubble_width,
            justify="left",
            padx=10,
            pady=5,
            bd=1,
            relief="solid"
        )
        if sender == "user":
            bubble.pack(side="right", anchor="e")
        else:
            bubble.pack(side="left", anchor="w")

        # 如果需要按钮且是 AI 消息
        if with_button and sender == "ai":
            # 右侧按钮框架
            button_frame = tk.Frame(msg_frame, bg="#f0f0f0")
            button_frame.pack(side="left", anchor="w", padx=10)  # 右侧对齐

            # 上按钮：打开实验文件
            def open_file():
                import os
                file_path = os.path.abspath(os.path.join(self.settings["work_folder"], "gpt_exp.psyexp"))
                if os.path.exists(file_path):
                    os.startfile(file_path)  # Windows 下用默认程序打开
                else:
                    messagebox.showerror("File does not exist", f"Cannot find {file_path}")

            btn = tk.Button(button_frame, text="Open Exp", command=open_file, bg="#4CAF50", fg="white", font=("Arial", 10))
            btn.pack(side="top", fill="x", pady=(0, 5))  # 上按钮，向下留间距

            # 下按钮：打开工作目录
            def open_work_folder():
                import os
                folder_path = os.path.abspath(self.settings["work_folder"])
                if os.path.exists(folder_path):
                    os.startfile(folder_path)  # Windows 下用资源管理器打开
                else:
                    messagebox.showerror("Folder does not exist", f"Cannot find {folder_path}")

            btn_folder = tk.Button(button_frame, text="Open Folder", command=open_work_folder, bg="#2196F3", fg="white", font=("Arial", 10))
            btn_folder.pack(side="top", fill="x")  # 下按钮
        #绑定右键菜单，复制全部文本
        # 右键菜单：复制文本
        def copy_message():
            self.root.clipboard_clear()
            self.root.clipboard_append(message)
            self.root.update()  # 保证剪贴板内容可用

        def show_context_menu(event):
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Copy", command=copy_message)
            menu.tk_popup(event.x_root, event.y_root)

        bubble.bind("<Button-3>", show_context_menu)


        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    def call_openai_chat(self,
        messages,
        functions=None,
        function_call="auto",  # 或 "none" 或 {"name": "function_name"}
        temperature=0.7,
        top_p=1.0,
        response_format=None
    ):

        headers = {
            "Authorization": f"Bearer {self.settings['api_key'] or os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.settings["model"],
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "parallel_tool_calls": False,  
        }

        if functions:
            payload["tools"] = functions
            if function_call:
                payload["tool_choice"] = function_call

        if response_format:
            payload["response_format"] = response_format
        if self.settings["base_url"]=="https://open.bigmodel.cn":
            url = self.settings["base_url"] + "/api/paas/v4/chat/completions"
        else:
            url = self.settings["base_url"] + "/v1/chat/completions"
        response = requests.post(url, headers=headers, json=payload)
        if not response.ok:
            #删除上一条不是文件上传的user消息
            if self.messages:
                #到着检查
                for i in range(len(self.messages)-1, -1, -1):
                    if self.messages[i]["role"] == "user" and "content" in self.messages[i] and not self.messages[i]["content"].startswith("Files may be used:"):
                        del self.messages[i]
                        break
            raise Exception(f"API Error {response.status_code}: {response.text}")
        print(f"API Response: {response.text}")
        result = response.json()
        choice = result["choices"][0]["message"]
        return choice
    def generate_ai_response(self, user_msg=None,with_button=False,times=0):
        
        if user_msg:
            self.messages.append({"role": "user", "content": user_msg})
        try:
            response = self.call_openai_chat(
                messages=self.messages,
                functions=functions,
                function_call="auto",
                temperature=0.7
            )
            self.messages.append(response)
            if isinstance(response, dict) and "content" in response and response["content"]:
                self.root.after(0, lambda: self.add_message(response["content"], sender="ai",with_button=with_button))
            if isinstance(response, dict) and "tool_calls" in response:
                function_name = response["tool_calls"][0]["function"]["name"]
                arguments = json.loads(response["tool_calls"][0]["function"]["arguments"])
                if function_name == "get_components_param":
                    names = arguments.get("names", [])
                    function_response = get_components_params(names)
                elif function_name == "build_flow":
                    self.status_label.config(text="AI is building...")
                    exp_settings = arguments.get("exp_settings", {})
                    flow = arguments.get("flow", [])
                    success, message = build_flow(exp_settings, flow, self.settings["work_folder"])
                    if times>3 and not success:
                        return f"To many times..."
                    times+=1
                    if success:
                        with_button = True
                    function_response= message
                self.messages.append({"role": "tool", "tool_call_id": response["tool_calls"][0]["id"],"content": function_response})
                
                
                self.generate_ai_response(with_button=with_button,times=times)
        except Exception as e:
            return f"AI Error: {str(e)}"
        

    def send_message(self):
        msg = self.user_input.get("1.0", "end").strip()
        if not msg:
            return
        # 检查是否有API Key
        if not self.settings["api_key"]:
            messagebox.showerror("API Key Missing", "Set your API Key in Menu.")
            return
        self.user_input.delete("1.0", "end")
        self.add_message(msg, sender="user")
        self.send_button.config(state="disabled")
        self.resource_button.config(state="disabled")
        self.status_label.config(text="AI is thinking...")

        def worker():
            reply = self.generate_ai_response(msg)
            if reply:
                self.root.after(0, lambda: self.handle_ai_reply(reply))
            self.send_button.config(state="normal")
            self.resource_button.config(state="normal")
            self.status_label.config(text="")

        threading.Thread(target=worker, daemon=True).start()

    def handle_ai_reply(self, reply):
        self.add_message(reply, sender="ai")

    # -------- 资源上传窗口功能 --------
    def open_resource_window(self):
        # 如果已有窗口则激活，避免多开
        if hasattr(self, 'resource_win') and self.resource_win.winfo_exists():
            self.resource_win.lift()
            return

        self.resource_win = tk.Toplevel(self.root)
        self.resource_win.title("Source Select and Comment")
        self.center_window(self.root, self.resource_win, 520, 450)
        self.resource_win.grab_set()  # 模态窗口
        #绑定滚轮
        

        icon_path = os.path.join(os.path.dirname(__file__), r"Lib\site-packages\psychopy\app\Resources\builder.ico")
        if os.path.exists(icon_path):
            self.resource_win.iconbitmap(icon_path)
        
        frame_files = tk.Frame(self.resource_win)
        frame_files.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas_files = tk.Canvas(frame_files)
        scrollbar_files = ttk.Scrollbar(frame_files, orient="vertical", command=self.canvas_files.yview)
        self.files_inner = tk.Frame(self.canvas_files)

        self.canvas_files.bind_all("<MouseWheel>", self._on_mousewheels)  # Windows
        self.canvas_files.bind_all("<Button-4>", self._on_mousewheels)    # Linux
        self.canvas_files.bind_all("<Button-5>", self._on_mousewheels)    # Linux

        self.files_inner_id = self.canvas_files.create_window((0,0), window=self.files_inner, anchor="nw")
        self.canvas_files.configure(yscrollcommand=scrollbar_files.set)

        self.canvas_files.pack(side="left", fill="both", expand=True)
        scrollbar_files.pack(side="right", fill="y")

        self.files_inner.bind("<Configure>", lambda e: self.canvas_files.configure(scrollregion=self.canvas_files.bbox("all")))
        self.canvas_files.bind("<Configure>", lambda e: self.canvas_files.itemconfig(self.files_inner_id, width=e.width))

        # 底部三个按钮，左右分布
        btn_frame = tk.Frame(self.resource_win)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))

        btn_add_files = tk.Button(btn_frame, text="Add", command=self.add_files)
        btn_add_files.pack(side="left")

        btn_clear = tk.Button(btn_frame, text="Clear", command=self.clear_files)
        btn_clear.pack(side="left", padx=10)

        btn_confirm = tk.Button(btn_frame, text="Confirm", bg="#4CAF50", fg="white", command=self.confirm_files)
        btn_confirm.pack(side="right")

        self.file_entries = {}
        self.load_saved_files()

    def add_files(self):
        filepaths = filedialog.askopenfilenames(title="Select Files")
        if not filepaths:
            return
        for path in filepaths:
            if path in self.file_entries:
                continue  # 避免重复添加
            self._add_file_row(path)


    def _add_file_row(self, filepath):

        filename = os.path.basename(filepath)
        max_pixel_width = 200  # 最大显示宽度（像素）

        row_frame = tk.Frame(self.files_inner)
        row_frame.pack(fill="x", pady=2, padx=5)

        # 创建字体对象
        font_obj = tkfont.Font(family="Arial", size=11)

        # 安全截断显示文本，确保右侧可见
        display_text = filename
        if font_obj.measure(display_text) > max_pixel_width:
            # 保留结尾部分
            suffix = ""
            base = filename
            while font_obj.measure("..." + suffix) < max_pixel_width and base:
                suffix = base[-1] + suffix
                base = base[:-1]
            display_text = "..." + suffix

        # 文件名 Label
        lbl_name = tk.Label(row_frame, text=display_text, anchor="w", font=font_obj)
        lbl_name.grid(row=0, column=0, sticky="w", padx=(0, 10))

        # 说明输入框
        ent_desc = tk.Entry(row_frame, font=font_obj)
        ent_desc.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # 删除按钮
        btn_del = tk.Button(row_frame, text="Delete", fg="red", width=6,
                            command=lambda p=filepath: self.delete_file(p))
        btn_del.grid(row=0, column=2, sticky="e")
        


        # 控制列扩展：Entry 自动拉伸，其他固定
        row_frame.columnconfigure(0, weight=0, minsize=150)
        row_frame.columnconfigure(1, weight=1)
        row_frame.columnconfigure(2, weight=0)

        # 存储引用
        self.file_entries[filepath] = {
            "desc_entry": ent_desc,
            "frame": row_frame
        }


    def delete_file(self, filepath):
        if filepath in self.file_entries:
            self.file_entries[filepath]["frame"].destroy()
            del self.file_entries[filepath]

    def clear_files(self):
        for filepath in list(self.file_entries.keys()):
            self.delete_file(filepath)

    def confirm_files(self):
        global uploaded_files
        old_uploaded_files = uploaded_files.copy() 
        uploaded_files.clear()
        for path, widgets in self.file_entries.items():
            desc = widgets["desc_entry"].get().strip()
            filename = os.path.basename(path)
            uploaded_files.append({
                "filepath": path,
                "filename": filename,
                "desc": desc
            })
        # 关闭资源窗口，不弹窗提示
        self.resource_win.destroy()
        print(files_to_text())
        print(files_to_work_Folder(self.settings["work_folder"]))
        if old_uploaded_files != uploaded_files and len(uploaded_files) > 0:
            #如果上一条信息就是文件，则先删除
            if self.messages and self.messages[-1].get("role") == "user" and self.messages[-1].get("content", "").startswith("Files may be used:"):
                self.messages.pop()
            self.messages.append({"role": "user", "content": "Files may be used:\n" + files_to_text()[1]})

    def load_saved_files(self):
        # 清空旧显示
        self.clear_files()
        # 载入之前保存的全局变量中的文件和说明，重新生成界面
        for fileinfo in uploaded_files:
            path = fileinfo["filepath"]
            self._add_file_row(path)
            # 填写说明
            self.file_entries[path]["desc_entry"].insert(0, fileinfo.get("desc", ""))


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()