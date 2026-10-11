#!/usr/bin/env python3
"""
Llama.cpp AI Assistant with Tool Calls & Visual Scripting
Requires: pip install PySide6 llama-cpp-python
"""

import sys, os, json, math, re, time, traceback, platform, ast
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════
#  CONSTANTS & THEME
# ═══════════════════════════════════════════════════════════════════

DARK_STYLE = """
QMainWindow, QDialog { background-color: #0d1117; color: #c9d1d9; }
QDockWidget { color: #c9d1d9; background-color: #161b22; border: none; font-size: 13px; }
QDockWidget::title { background-color: #21262d; padding: 8px 12px; border-top: 1px solid #30363d; }
QTextEdit, QTextBrowser { background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
    border-radius: 6px; padding: 8px; font-size: 14px; selection-background-color: #1f6feb; }
QLineEdit, QSpinBox, QDoubleSpinBox, QPlainTextEdit { background-color: #21262d; color: #c9d1d9;
    border: 1px solid #30363d; padding: 6px 10px; border-radius: 6px; font-size: 13px; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QPlainTextEdit:focus {
    border-color: #58a6ff; }
QPushButton { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d;
    padding: 8px 18px; border-radius: 6px; font-size: 13px; font-weight: 500; }
QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
QPushButton:pressed { background-color: #1f6feb; color: #ffffff; }
QPushButton:disabled { color: #484f58; border-color: #21262d; }
QPushButton#accentBtn { background-color: #238636; border-color: #2ea043; color: #ffffff; }
QPushButton#accentBtn:hover { background-color: #2ea043; }
QPushButton#dangerBtn { background-color: #da3633; border-color: #f85149; color: #ffffff; }
QPushButton#dangerBtn:hover { background-color: #f85149; }
QTabWidget::pane { border: 1px solid #30363d; background-color: #0d1117; border-radius: 6px; }
QTabBar::tab { background-color: #161b22; color: #8b949e; padding: 8px 20px;
    border: 1px solid #30363d; border-bottom: none; margin-right: 2px;
    border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 13px; }
QTabBar::tab:selected { background-color: #0d1117; color: #c9d1d9; }
QListWidget { background-color: #0d1117; color: #c9d1d9; border: 1px solid #30363d;
    border-radius: 6px; padding: 4px; font-size: 13px; }
QListWidget::item { padding: 6px 8px; border-radius: 4px; margin: 1px 0; }
QListWidget::item:selected { background-color: #1f6feb; color: #ffffff; }
QListWidget::item:hover:!selected { background-color: #161b22; }
QComboBox { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d;
    padding: 6px 10px; border-radius: 6px; font-size: 13px; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #21262d; color: #c9d1d9;
    border: 1px solid #30363d; selection-background-color: #1f6feb; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background-color: #30363d; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #484f58; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background-color: #30363d; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QMenuBar { background-color: #161b22; color: #c9d1d9; border-bottom: 1px solid #30363d; font-size: 13px; }
QMenuBar::item:selected { background-color: #21262d; border-radius: 4px; }
QMenu { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d;
    border-radius: 6px; padding: 4px; font-size: 13px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; }
QMenu::item:selected { background-color: #1f6feb; color: #ffffff; }
QMenu::separator { height: 1px; background-color: #30363d; margin: 4px 8px; }
QStatusBar { background-color: #161b22; color: #8b949e; border-top: 1px solid #30363d; font-size: 12px; }
QLabel { color: #c9d1d9; font-size: 13px; }
QGroupBox { color: #c9d1d9; border: 1px solid #30363d; border-radius: 6px;
    margin-top: 14px; padding: 16px 12px 12px 12px; font-size: 13px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px;
    color: #58a6ff; font-weight: 600; }
QToolTip { background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d;
    padding: 4px 8px; border-radius: 4px; font-size: 12px; }
QSplitter::handle { background-color: #21262d; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical { height: 2px; }
QGraphicsView { border: none; background-color: #0d1117; }
"""

class PortDataType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    JSON = "json"
    ANY = "any"

class PortDirection(Enum):
    INPUT = "input"
    OUTPUT = "output"

class NodeType(Enum):
    SCRIPT_INPUT = "Script Input"
    TOOL_CALL = "Tool Call"
    TRANSFORM = "Transform"
    SCRIPT_OUTPUT = "Script Output"

PORT_COLORS = {
    PortDataType.STRING: "#58a6ff", PortDataType.NUMBER: "#3fb950",
    PortDataType.BOOLEAN: "#d29922", PortDataType.JSON: "#bc8cff",
    PortDataType.ANY: "#8b949e",
}
NODE_COLORS = {
    NodeType.SCRIPT_INPUT: "#238636", NodeType.TOOL_CALL: "#1f6feb",
    NodeType.TRANSFORM: "#8957e5", NodeType.SCRIPT_OUTPUT: "#da3633",
}
COMPATIBLE = {
    PortDataType.ANY: {PortDataType.STRING, PortDataType.NUMBER, PortDataType.BOOLEAN, PortDataType.JSON, PortDataType.ANY},
    PortDataType.STRING: {PortDataType.STRING, PortDataType.ANY},
    PortDataType.NUMBER: {PortDataType.NUMBER, PortDataType.STRING, PortDataType.ANY},
    PortDataType.BOOLEAN: {PortDataType.BOOLEAN, PortDataType.STRING, PortDataType.ANY},
    PortDataType.JSON: {PortDataType.JSON, PortDataType.STRING, PortDataType.ANY},
}

# ═══════════════════════════════════════════════════════════════════
#  TOOL SYSTEM
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""

class ToolManager:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_builtins()

    def _register_builtins(self):
        self.register(ToolDefinition(
            name="calculator",
            description="Evaluate a mathematical expression and return the result.",
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string",
                    "description": "Math expression, e.g. '(2+3)*4.5 - 1.2'"}},
                "required": ["expression"]
            },
            handler=self._calc
        ))
        self.register(ToolDefinition(
            name="get_system_info",
            description="Get information about the system: OS, CPU, memory, Python version.",
            parameters={
                "type": "object",
                "properties": {"info_type": {"type": "string", "enum": ["os","cpu","memory","python","all"],
                    "description": "Which type of system info to retrieve"}},
                "required": ["info_type"]
            },
            handler=self._sysinfo
        ))
        self.register(ToolDefinition(
            name="read_file",
            description="Read the contents of a text file.",
            parameters={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Absolute or relative path"}},
                "required": ["file_path"]
            },
            handler=self._read_file
        ))
        self.register(ToolDefinition(
            name="write_file",
            description="Write content to a file. Creates parent directories if needed.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to write to"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["file_path", "content"]
            },
            handler=self._write_file
        ))
        self.register(ToolDefinition(
            name="list_directory",
            description="List files and directories at a given path.",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Directory path"}},
                "required": ["path"]
            },
            handler=self._list_dir
        ))
        self.register(ToolDefinition(
            name="current_datetime",
            description="Get the current date and time, optionally formatted.",
            parameters={
                "type": "object",
                "properties": {"fmt": {"type": "string",
                    "description": "strftime format, e.g. '%%Y-%%m-%%d %%H:%%M:%%S'. Default: ISO format."}}
            },
            handler=self._datetime
        ))
        self.register(ToolDefinition(
            name="string_transform",
            description="Apply string operations: upper, lower, reverse, length, strip, split, replace.",
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["upper","lower","reverse","length","strip","split","replace"]},
                    "text": {"type": "string"},
                    "parameter": {"type": "string", "description": "For split: delimiter. For replace: 'old,new'"}}
                ,
                "required": ["operation", "text"]
            },
            handler=self._str_op
        ))

    def _calc(self, **kw):
        try:
            expr = kw["expression"]
            safe = re.sub(r'[^0-9+\-*/.()%\s]', '', expr)
            result = eval(safe, {"__builtins__": {}}, {"abs": abs, "round": round,
                "min": min, "max": max, "pow": pow, "sqrt": math.sqrt})
            return ToolResult(True, str(result))
        except Exception as e:
            return ToolResult(False, "", str(e))

    def _sysinfo(self, **kw):
        t = kw["info_type"]
        parts = []
        if t in ("os", "all"):
            parts.append(f"OS: {platform.system()} {platform.release()} ({platform.machine()})")
        if t in ("cpu", "all"):
            parts.append(f"CPU: {platform.processor() or 'N/A'}")
        if t in ("memory", "all"):
            import psutil; m = psutil.virtual_memory()
            parts.append(f"Memory: {m.total//(1024**2)} MB total, {m.available//(1024**2)} MB available")
        except_import = False
        if t in ("python", "all"):
            parts.append(f"Python: {platform.python_version()}")
        return ToolResult(True, "\n".join(parts) if parts else "Unknown info type")

    def _read_file(self, **kw):
        try:
            with open(kw["file_path"], "r", encoding="utf-8") as f:
                return ToolResult(True, f.read()[:10000])
        except Exception as e:
            return ToolResult(False, "", str(e))

    def _write_file(self, **kw):
        try:
            p = kw["file_path"]
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(kw["content"])
            return ToolResult(True, f"Written {len(kw['content'])} chars to {p}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def _list_dir(self, **kw):
        try:
            items = os.listdir(kw["path"])
            out = []
            for i in sorted(items):
                full = os.path.join(kw["path"], i)
                out.append(f"{'[DIR]' if os.path.isdir(full) else '[FILE]'} {i}")
            return ToolResult(True, "\n".join(out))
        except Exception as e:
            return ToolResult(False, "", str(e))

    def _datetime(self, **kw):
        fmt = kw.get("fmt", "%Y-%m-%dT%H:%M:%S")
        return ToolResult(True, datetime.now().strftime(fmt))

    def _str_op(self, **kw):
        try:
            op, text = kw["operation"], kw["text"]
            param = kw.get("parameter", "")
            if op == "upper": return ToolResult(True, text.upper())
            if op == "lower": return ToolResult(True, text.lower())
            if op == "reverse": return ToolResult(True, text[::-1])
            if op == "length": return ToolResult(True, str(len(text)))
            if op == "strip": return ToolResult(True, text.strip())
            if op == "split": return ToolResult(True, json.dumps(text.split(param or None)))
            if op == "replace":
                parts = param.split(",", 1)
                if len(parts) == 2: return ToolResult(True, text.replace(parts[0], parts[1]))
                return ToolResult(False, "", "Replace needs 'old,new' in parameter")
            return ToolResult(False, "", f"Unknown operation: {op}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def execute(self, name: str, arguments: Dict) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(False, "", f"Tool '{name}' not found")
        try:
            return tool.handler(**arguments)
        except TypeError as e:
            return ToolResult(False, "", f"Invalid arguments: {e}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def to_openai_tools(self) -> List[Dict]:
        return [{"type": "function", "function": {
            "name": t.name, "description": t.description, "parameters": t.parameters
        }} for t in self._tools.values()]

# ═══════════════════════════════════════════════════════════════════
#  LLAMA BACKEND
# ═══════════════════════════════════════════════════════════════════

class ModelLoader(QThread):
    progress = Signal(str)
    loaded = Signal(object)
    error = Signal(str)

    def __init__(self, path, n_ctx, n_gpu_layers):
        super().__init__()
        self.path = path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers

    def run(self):
        try:
            self.progress.emit(f"Loading {os.path.basename(self.path)}...")
            model = Llama(model_path=self.path, n_ctx=self.n_ctx,
                          n_gpu_layers=self.n_gpu_layers, verbose=False)
            self.loaded.emit(model)
        except Exception as e:
            self.error.emit(str(e))

class LlamaWorker(QThread):
    stream_token = Signal(str)
    tool_call_start = Signal(list)
    tool_result_signal = Signal(str, str, bool)
    response_complete = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, model, messages, tools, tool_mgr, **kwargs):
        super().__init__()
        self.model = model
        self.messages = [m for m in messages]
        self.tools = tools
        self.tool_mgr = tool_mgr
        self.kwargs = kwargs
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        for _ in range(8):
            if self._stop:
                return
            try:
                content = ""
                tc_accum = {}
                for chunk in self.model.create_chat_completion(
                    messages=self.messages,
                    tools=self.tools or None,
                    stream=True, **self.kwargs
                ):
                    if self._stop: return
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta and delta["content"]:
                        content += delta["content"]
                        self.stream_token.emit(delta["content"])
                    if "tool_calls" in delta:
                        for tcd in delta["tool_calls"]:
                            idx = tcd["index"]
                            if idx not in tc_accum:
                                tc_accum[idx] = {"id":"","type":"function",
                                    "function":{"name":"","arguments":""}}
                            tc = tc_accum[idx]
                            if "id" in tcd: tc["id"] = tcd["id"]
                            if "function" in tcd:
                                fn = tcd["function"]
                                if "name" in fn: tc["function"]["name"] += fn["name"]
                                if "arguments" in fn: tc["function"]["arguments"] += fn["arguments"]

                tool_calls = [tc_accum[i] for i in sorted(tc_accum.keys())] if tc_accum else []
                msg = {"role": "assistant", "content": content or None}
                if tool_calls:
                    msg["tool_calls"] = tool_calls
                self.messages.append(msg)

                if not tool_calls:
                    self.response_complete.emit(content)
                    return

                self.tool_call_start.emit(tool_calls)
                for tc in tool_calls:
                    if self._stop: return
                    fname = tc["function"]["name"]
                    try:
                        args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        args = {}
                    result = self.tool_mgr.execute(fname, args)
                    self.tool_result_signal.emit(fname, result.output if result.success else f"Error: {result.error}", result.success)
                    self.messages.append({"role": "tool", "tool_call_id": tc["id"],
                        "content": result.output if result.success else f"Error: {result.error}"})

            except Exception as e:
                self.error_occurred.emit(str(e))
                return
        self.error_occurred.emit("Max tool call rounds exceeded")

class LlamaBackend:
    def __init__(self, tool_mgr: ToolManager):
        self.tool_mgr = tool_mgr
        self.model = None
        self.loader = None
        self.worker = None
        self.settings = {"n_ctx": 4096, "n_gpu_layers": 0, "temperature": 0.7,
                         "top_p": 0.9, "max_tokens": 1024}

    def load_model(self, path: str, callback_progress, callback_done, callback_error):
        if self.loader and self.loader.isRunning():
            self.loader.terminate()
        self.loader = ModelLoader(path, self.settings["n_ctx"], self.settings["n_gpu_layers"])
        self.loader.progress.connect(callback_progress)
        self.loader.loaded.connect(self._on_loaded)
        self.loader.loaded.connect(callback_done)
        self.loader.error.connect(callback_error)
        self.loader.start()

    def _on_loaded(self, model):
        self.model = model

    def is_loaded(self):
        return self.model is not None

    def stop_generation(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)

    def chat(self, messages, stream_cb, tool_call_cb, tool_result_cb, complete_cb, error_cb):
        if not self.model:
            error_cb("No model loaded")
            return
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(2000)
        self.worker = LlamaWorker(self.model, messages, self.tool_mgr.to_openai_tools(),
                                  self.tool_mgr, temperature=self.settings["temperature"],
                                  top_p=self.settings["top_p"], max_tokens=self.settings["max_tokens"])
        self.worker.stream_token.connect(stream_cb)
        self.worker.tool_call_start.connect(tool_call_cb)
        self.worker.tool_result_signal.connect(tool_result_cb)
        self.worker.response_complete.connect(complete_cb)
        self.worker.error_occurred.connect(error_cb)
        self.worker.start()

# ═══════════════════════════════════════════════════════════════════
#  VISUAL SCRIPT ENGINE
# ═══════════════════════════════════════════════════════════════════

class ScriptEngine:
    def __init__(self, tool_mgr: ToolManager):
        self.tool_mgr = tool_mgr

    def execute(self, nodes: List[Dict], connections: List[Dict], inputs: Dict) -> Dict:
        node_map = {n["id"]: n for n in nodes}
        in_degree = defaultdict(int)
        adj = defaultdict(list)
        for c in connections:
            adj[c["from_node"]].append(c)
            in_degree[c["to_node"]] += 1

        queue = deque()
        for n in nodes:
            if n["type"] == "SCRIPT_INPUT":
                queue.append(n["id"])

        port_values = {}
        while queue:
            nid = queue.popleft()
            node = node_map[nid]
            ninputs = {}
            for c in connections:
                if c["to_node"] == nid:
                    ninputs[c["to_port"]] = port_values.get((c["from_node"], c["from_port"]))

            if node["type"] == "SCRIPT_INPUT":
                pname = node.get("param_name", "input")
                port_values[(nid, "value")] = inputs.get(pname, node.get("default_value", ""))
            elif node["type"] == "TOOL_CALL":
                tool_name = node.get("tool_name", "")
                args = {}
                params = node.get("params", {})
                for pk, pv in params.items():
                    mapped = pv
                    if isinstance(pv, str) and pv.startswith("port:"):
                        port_ref = pv[5:]
                        mapped = ninputs.get(port_ref, "")
                    args[pk] = mapped
                result = self.tool_mgr.execute(tool_name, args)
                port_values[(nid, "result")] = result.output if result.success else f"Error: {result.error}"
            elif node["type"] == "TRANSFORM":
                expr = node.get("expression", "")
                local_vars = {}
                for pn, pv in ninputs.items():
                    safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', pn)
                    local_vars[safe_name] = pv
                try:
                    port_values[(nid, "result")] = str(eval(expr, {"__builtins__": {
                        "int": int, "float": float, "str": str, "len": len, "json": json,
                        "upper": lambda s: str(s).upper(), "lower": lambda s: str(s).lower(),
                        "strip": lambda s: str(s).strip(), "split": lambda s, d=None: str(s).split(d),
                        "join": lambda d, s: d.join(s), "replace": lambda s, o, n: str(s).replace(o, n),
                        "abs": abs, "round": round, "min": min, "max": max, "math": math,
                    }}, local_vars))
                except Exception as e:
                    port_values[(nid, "result")] = f"Error: {e}"
            elif node["type"] == "SCRIPT_OUTPUT":
                port_values[(nid, "value")] = ninputs.get("value", "")

            for c in adj[nid]:
                in_degree[c["to_node"]] -= 1
                if in_degree[c["to_node"]] == 0:
                    queue.append(c["to_node"])

        outputs = {}
        for n in nodes:
            if n["type"] == "SCRIPT_OUTPUT":
                oname = n.get("output_name", "output")
                outputs[oname] = port_values.get((n["id"], "value"), "")
        return outputs

    def to_tool_definition(self, name: str, desc: str, nodes: List[Dict]) -> Optional[ToolDefinition]:
        input_nodes = [n for n in nodes if n["type"] == "SCRIPT_INPUT"]
        output_nodes = [n for n in nodes if n["type"] == "SCRIPT_OUTPUT"]
        if not input_nodes or not output_nodes:
            return None
        props = {}
        required = []
        for n in input_nodes:
            pn = n.get("param_name", "input")
            ptype = n.get("data_type", "string")
            props[pn] = {"type": ptype, "description": n.get("description", f"Parameter {pn}")}
            if not n.get("default_value"):
                required.append(pn)
        params = {"type": "object", "properties": props}
        if required:
            params["required"] = required

        engine = self
        conn_list = []  # Will be filled at registration time

        def handler(**kwargs):
            return ToolResult(True, json.dumps(engine.execute(nodes, conn_list, kwargs)))

        td = ToolDefinition(name=name, description=desc, parameters=params, handler=handler)
        td._nodes = nodes
        td._conn_list = conn_list
        return td

# ═══════════════════════════════════════════════════════════════════
#  NODE EDITOR GRAPHICS ITEMS
# ═══════════════════════════════════════════════════════════════════

class PortItem(QGraphicsEllipseItem):
    def __init__(self, name: str, direction: PortDirection, data_type: PortDataType,
                 parent_node, index: int):
        r = 7
        super().__init__(-r, -r, r*2, r*2, parent_node)
        self.port_name = name
        self.direction = direction
        self.data_type = data_type
        self.parent_node = parent_node
        self.index = index
        self.setAcceptHoverEvents(True)
        self.setZValue(10)
        self._hovered = False
        self._update_color()

    def _update_color(self):
        c = PORT_COLORS.get(self.data_type, "#8b949e")
        if self._hovered:
            self.setBrush(QColor(c))
            self.setPen(QPen(QColor(c), 2))
        else:
            self.setBrush(QColor(c).darker(130))
            self.setPen(QPen(QColor(c).darker(160), 1.5))

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._update_color()
        self.setToolTip(f"{self.port_name} ({self.data_type.value})")
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._update_color()
        super().hoverLeaveEvent(event)

    def scenePosCenter(self):
        return self.mapToScene(0, 0)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = PORT_COLORS.get(self.data_type, "#8b949e")
        if self._hovered:
            glow = QRadialGradient(0, 0, 14)
            glow.setColorAt(0, QColor(c, 80))
            glow.setColorAt(1, QColor(c, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(-14, -14, 28, 28)
        super().paint(painter, option, widget)


class ConnectionItem(QGraphicsPathItem):
    def __init__(self, source: PortItem, target: PortItem):
        super().__init__()
        self.source = source
        self.target = target
        self.setZValue(-1)
        self.setAcceptHoverEvents(True)
        self._hovered = False
        self._update_path()
        self._update_style()

    def _update_path(self):
        sp = self.source.scenePosCenter()
        tp = self.target.scenePosCenter()
        dx = abs(tp.x() - sp.x())
        offset = max(60, dx * 0.5)
        path = QPainterPath()
        path.moveTo(sp)
        path.cubicTo(sp.x() + offset, sp.y(), tp.x() - offset, tp.y(), tp)
        self.setPath(path)

    def _update_style(self):
        c = PORT_COLORS.get(self.source.data_type, "#8b949e")
        w = 3 if self._hovered else 2
        self.setPen(QPen(QColor(c), w))
        self.setBrush(Qt.BrushStyle.NoBrush)

    def update_position(self):
        self._update_path()

    def hoverEnterEvent(self, event):
        self._hovered = True
        self._update_style()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self._update_style()
        super().hoverLeaveEvent(event)

    def to_dict(self):
        return {"from_node": self.source.parent_node.node_id,
                "from_port": self.source.port_name,
                "to_node": self.target.parent_node.node_id,
                "to_port": self.target.port_name}


class NodeItem(QGraphicsWidget):
    def __init__(self, node_type: NodeType, node_id: str, x=0, y=0):
        super().__init__()
        self.node_type = node_type
        self.node_id = node_id
        self.inputs: List[PortItem] = []
        self.outputs: List[PortItem] = []
        self._data: Dict[str, Any] = {"param_name": "", "data_type": "string",
            "description": "", "default_value": "", "tool_name": "",
            "params": {}, "expression": "", "output_name": ""}
        self.setZValue(1)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self._width = 200
        self._title_h = 30
        self._row_h = 26
        self._setup_ports()
        self.setPos(x, y)
        self._hovered = False

    def _setup_ports(self):
        if self.node_type == NodeType.SCRIPT_INPUT:
            self.outputs.append(PortItem("value", PortDirection.OUTPUT, PortDataType.ANY, self, 0))
        elif self.node_type == NodeType.TOOL_CALL:
            self.inputs.append(PortItem("tool_args", PortDirection.INPUT, PortDataType.JSON, self, 0))
            self.outputs.append(PortItem("result", PortDirection.OUTPUT, PortDataType.ANY, self, 0))
        elif self.node_type == NodeType.TRANSFORM:
            self.inputs.append(PortItem("input", PortDirection.INPUT, PortDataType.ANY, self, 0))
            self.outputs.append(PortItem("result", PortDirection.OUTPUT, PortDataType.ANY, self, 0))
        elif self.node_type == NodeType.SCRIPT_OUTPUT:
            self.inputs.append(PortItem("value", PortDirection.INPUT, PortDataType.ANY, self, 0))

    def _total_height(self):
        n = max(len(self.inputs), len(self.outputs), 1)
        return self._title_h + n * self._row_h + 10

    def set_data(self, key, value):
        self._data[key] = value
        self.update()

    def get_data(self, key, default=None):
        return self._data.get(key, default)

    def to_dict(self):
        d = {"id": self.node_id, "type": self.node_type.value,
             "x": self.pos().x(), "y": self.pos().y()}
        d.update(self._data)
        return d

    def boundingRect(self):
        return QRectF(0, 0, self._width, self._total_height())

    def sizeHint(self, which, constraint=QSizeF()):
        return QSizeF(self._width, self._total_height())

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self._total_height()
        w = self._width

        # Shadow
        if self.isSelected():
            shadow = QGraphicsDropShadowEffect()
            shadow.setColor(QColor("#58a6ff"))
            shadow.setBlurRadius(16)
            shadow.setOffset(0, 0)
            self.setGraphicsEffect(shadow)

        # Body
        body_rect = QRectF(0, 0, w, h)
        painter.setBrush(QColor("#161b22"))
        painter.setPen(QPen(QColor("#30363d") if not self.isSelected() else QColor("#58a6ff"), 1.5))
        painter.drawRoundedRect(body_rect, 8, 8)

        # Title bar
        title_color = NODE_COLORS.get(self.node_type, "#30363d")
        title_rect = QRectF(0, 0, w, self._title_h)
        painter.setBrush(QColor(title_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(title_rect, 8, 8)
        painter.setRect(QRectF(0, self._title_h - 8, w, 8))
        painter.drawRect(QRectF(0, self._title_h - 8, w, 8))

        # Title text
        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(font)
        title_text = self.node_type.value
        if self.node_type == NodeType.SCRIPT_INPUT and self._data.get("param_name"):
            title_text = f"▶ {self._data['param_name']}"
        elif self.node_type == NodeType.TOOL_CALL and self._data.get("tool_name"):
            title_text = f"⚙ {self._data['tool_name']}"
        elif self.node_type == NodeType.TRANSFORM:
            expr = self._data.get("expression", "")
            title_text = f"λ {expr[:18]}" if expr else "Transform"
        elif self.node_type == NodeType.SCRIPT_OUTPUT and self._data.get("output_name"):
            title_text = f"■ {self._data['output_name']}"
        painter.drawText(QRectF(10, 0, w - 20, self._title_h), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title_text)

        # Port labels
        font.setWeight(QFont.Weight.Normal)
        font.setPointSize(9)
        painter.setFont(font)
        for i, port in enumerate(self.inputs):
            y = self._title_h + i * self._row_h + self._row_h / 2
            port.setPos(0, y)
            c = PORT_COLORS.get(port.data_type, "#8b949e")
            painter.setPen(QColor(c))
            painter.drawText(QRectF(18, y - 8, w / 2 - 20, 16), Qt.AlignmentFlag.AlignVCenter, port.port_name)

        for i, port in enumerate(self.outputs):
            y = self._title_h + i * self._row_h + self._row_h / 2
            port.setPos(w, y)
            c = PORT_COLORS.get(port.data_type, "#8b949e")
            painter.setPen(QColor(c))
            painter.drawText(QRectF(w / 2, y - 8, w / 2 - 18, 16),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, port.port_name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if scene:
                for item in scene.items():
                    if isinstance(item, ConnectionItem):
                        if item.source.parent_node == self or item.target.parent_node == self:
                            item.update_position()
        return super().itemChange(change, value)

# ═══════════════════════════════════════════════════════════════════
#  NODE EDITOR SCENE & VIEW
# ═══════════════════════════════════════════════════════════════════

class NodeEditorScene(QGraphicsScene):
    node_selected = Signal(object)
    connection_added = Signal(object)
    connection_removed = Signal(object)
    items_removed = Signal()

    def __init__(self):
        super().__init__()
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self._connecting_from: Optional[PortItem] = None
        self._temp_line: Optional[QGraphicsPathItem] = None
        self._connections: List[ConnectionItem] = []

    def add_node(self, node_type: NodeType, x=0, y=0) -> NodeItem:
        nid = f"node_{id(node_type)}_{int(time.time()*1000)%100000}"
        node = NodeItem(node_type, nid, x, y)
        self.addItem(node)
        return node

    def add_connection(self, source: PortItem, target: PortItem) -> Optional[ConnectionItem]:
        if source.direction != PortDirection.OUTPUT or target.direction != PortDirection.INPUT:
            return None
        if source.parent_node == target.parent_node:
            return None
        compat = COMPATIBLE.get(source.data_type, set())
        if target.data_type not in compat:
            return None
        # Remove existing connections to target input
        for c in self._connections[:]:
            if c.target == target:
                self.remove_connection(c)
        conn = ConnectionItem(source, target)
        self.addItem(conn)
        self._connections.append(conn)
        self.connection_added.emit(conn)
        return conn

    def remove_connection(self, conn: ConnectionItem):
        if conn in self._connections:
            self._connections.remove(conn)
        self.removeItem(conn)
        self.connection_removed.emit(conn)

    def start_connecting(self, port: PortItem):
        self._connecting_from = port
        path = QPainterPath(port.scenePosCenter())
        self._temp_line = QGraphicsPathItem(path)
        self._temp_line.setPen(QPen(QColor("#58a6ff"), 2, Qt.PenStyle.DashLine))
        self._temp_line.setZValue(100)
        self.addItem(self._temp_line)

    def update_connecting(self, scene_pos: QPointF):
        if not self._temp_line or not self._connecting_from:
            return
        sp = self._connecting_from.scenePosCenter()
        dx = abs(scene_pos.x() - sp.x())
        offset = max(40, dx * 0.4)
        path = QPainterPath(sp)
        if self._connecting_from.direction == PortDirection.OUTPUT:
            path.cubicTo(sp.x() + offset, sp.y(), scene_pos.x() - offset, scene_pos.y(), scene_pos)
        else:
            path.cubicTo(sp.x() - offset, sp.y(), scene_pos.x() + offset, scene_pos.y(), scene_pos)
        self._temp_line.setPath(path)

    def finish_connecting(self, port: Optional[PortItem]):
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None
        if self._connecting_from and port and port != self._connecting_from:
            if self._connecting_from.direction == PortDirection.OUTPUT:
                self.add_connection(self._connecting_from, port)
            else:
                self.add_connection(port, self._connecting_from)
        self._connecting_from = None

    def cancel_connecting(self):
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None
        self._connecting_from = None

    def get_all_data(self) -> Tuple[List[Dict], List[Dict]]:
        nodes = []
        connections = []
        for item in self.items():
            if isinstance(item, NodeItem):
                nodes.append(item.to_dict())
            elif isinstance(item, ConnectionItem):
                connections.append(item.to_dict())
        return nodes, connections

    def clear_all(self):
        for c in self._connections[:]:
            self.removeItem(c)
        self._connections.clear()
        for item in self.items():
            if isinstance(item, NodeItem):
                self.removeItem(item)
        self.items_removed.emit()

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor("#0d1117"))
        grid_size = 30
        left = int(rect.left()) - int(rect.left()) % grid_size
        top = int(rect.top()) - int(rect.top()) % grid_size
        painter.setPen(QPen(QColor("#161b22"), 1))
        lines = []
        x = left
        while x < rect.right():
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
            x += grid_size
        y = top
        while y < rect.bottom():
            lines.append(QLineF(rect.left(), y, rect.right(), y))
            y += grid_size
        painter.drawLines(lines)
        # Major grid
        major = grid_size * 5
        left2 = int(rect.left()) - int(rect.left()) % major
        top2 = int(rect.top()) - int(rect.top()) % major
        painter.setPen(QPen(QColor("#1c2333"), 1))
        lines2 = []
        x = left2
        while x < rect.right():
            lines2.append(QLineF(x, rect.top(), x, rect.bottom()))
            x += major
        y = top2
        while y < rect.bottom():
            lines2.append(QLineF(rect.left(), y, rect.right(), y))
            y += major
        painter.drawLines(lines2)


class NodeEditorView(QGraphicsView):
    def __init__(self, scene: NodeEditorScene):
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self._panning = False
        self._pan_start = QPoint()
        self._dragging_port = False
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1/1.15
        self.scale(factor, factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.position().toPoint())
            if isinstance(item, PortItem):
                self._dragging_port = True
                self.scene().start_connecting(item)
                event.accept()
                return
        super().mousePressEvent(event)
        # Emit node selected
        for item in self.scene().selectedItems():
            if isinstance(item, NodeItem):
                self.scene().node_selected.emit(item)
                break

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self._dragging_port:
            self.scene().update_connecting(self.mapToScene(event.position().toPoint()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._dragging_port:
            item = self.itemAt(event.position().toPoint())
            port = None
            while item:
                if isinstance(item, PortItem):
                    port = item
                    break
                item = item.parentItem() if hasattr(item, 'parentItem') else None
            self.scene().finish_connecting(port)
            self._dragging_port = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene().selectedItems():
                if isinstance(item, ConnectionItem):
                    self.scene().remove_connection(item)
                elif isinstance(item, NodeItem):
                    for c in self.scene()._connections[:]:
                        if c.source.parent_node == item or c.target.parent_node == item:
                            self.scene().remove_connection(c)
                    self.scene().removeItem(item)
            self.scene().items_removed.emit()
        elif event.key() == Qt.Key.Key_Escape:
            self.scene().cancel_connecting()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        sp = self.mapToScene(event.position().toPoint())
        for nt in NodeType:
            action = menu.addAction(f"Add {nt.value}")
            action.setData((nt, sp.x(), sp.y()))
        menu.addSeparator()
        clear_action = menu.addAction("Clear All")
        clear_action.setData("clear")

        chosen = menu.exec(event.globalPosition().toPoint())
        if chosen:
            data = chosen.data()
            if data == "clear":
                self.scene().clear_all()
            elif isinstance(data, tuple):
                nt, x, y = data
                node = self.scene().add_node(nt, x, y)
                node.setSelected(True)
                self.scene().node_selected.emit(node)

# ═══════════════════════════════════════════════════════════════════
#  CHAT WIDGET
# ═══════════════════════════════════════════════════════════════════

class ChatWidget(QWidget):
    send_requested = Signal(str)
    stop_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.messages_view = QTextBrowser()
        self.messages_view.setOpenLinks(False)
        layout.addWidget(self.messages_view, 1)

        input_bar = QWidget()
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message... (Enter to send, Shift+Enter for newline)")
        self.input_field.setMinimumHeight(44)
        self.input_field.returnPressed.connect(self._on_return)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("accentBtn")
        self.send_btn.setFixedWidth(90)
        self.send_btn.setMinimumHeight(44)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        input_layout.addWidget(self.stop_btn)

        layout.addWidget(input_bar)
        self._assistant_html = ""
        self._streaming = False

    def _on_return(self):
        if self.input_field.text().strip():
            self._on_send()

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.send_requested.emit(text)

    def set_generating(self, generating: bool):
        self._streaming = generating
        self.send_btn.setVisible(not generating)
        self.stop_btn.setVisible(generating)
        self.input_field.setEnabled(not generating)

    def append_user_message(self, text: str):
        self._append_message("You", text, "#c9d1d9", "#161b22", align_right=True)

    def append_assistant_token(self, token: str):
        if not self._streaming:
            self._assistant_html = ""
            self._streaming = True
        self._assistant_html += self._escape(token)
        self._update_assistant_display()

    def finalize_assistant_message(self):
        if self._assistant_html:
            self._append_message("Assistant", self._assistant_html, "#58a6ff", "#0d1117",
                                 is_html=True, pre_html=self._assistant_html)
        self._assistant_html = ""
        self._streaming = False

    def append_tool_call(self, tool_calls: list):
        for tc in tool_calls:
            fname = tc["function"]["name"]
            args = tc["function"].get("arguments", "{}")
            try:
                args_fmt = json.dumps(json.loads(args), indent=2)
            except:
                args_fmt = args
            html = f'<div style="color:#d29922;font-weight:600;">⚙ {self._escape(fname)}</div>'
            html += f'<pre style="color:#8b949e;margin:4px 0;font-size:12px;">{self._escape(args_fmt)}</pre>'
            self._append_message("Tool Call", html, "#d29922", "#1a1500", is_html=True, pre_html=html)

    def append_tool_result(self, name: str, result: str, success: bool):
        color = "#3fb950" if success else "#f85149"
        icon = "✓" if success else "✗"
        html = f'<span style="color:{color};font-weight:600;">{icon} {self._escape(name)}</span><br>'
        html += f'<pre style="color:#8b949e;margin:4px 0;font-size:12px;max-height:200px;overflow:auto;">{self._escape(result[:2000])}</pre>'
        self._append_message("Tool Result", html, color, "#0d1117", is_html=True, pre_html=html)

    def append_system_message(self, text: str):
        self._append_message("System", text, "#8b949e", "#161b22")

    def _append_message(self, role: str, content: str, color: str, bg: str,
                        align_right=False, is_html=False, pre_html=""):
        doc = self.messages_view.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)

        table = cursor.insertTable(1, 1)
        table_format = table.format()
        table_format.setMargin(0)
        table_format.setPadding(8)
        table_format.setBorder(0)
        table_format.setWidth(QTextLength(QTextLength.Type.PercentageWidth, 85))
        if align_right:
            table_format.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            table_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        table.setFormat(table_format)

        cell = table.cellAt(0, 0)
        cell_format = cell.format()
        cell_format.setBottomPadding(4)
        cell_format.setTopPadding(2)
        bg_color = QColor(bg)
        bg_color.setAlpha(200)
        cell_format.setBackground(bg_color)
        cell.setFormat(cell_format)

        cell_cursor = cell.firstCursorPosition()
        # Role label
        char_format = cell_cursor.charFormat()
        char_format.setFontWeight(QFont.Weight.Bold)
        char_format.setFontPointSize(11)
        char_format.setForeground(QColor(color))
        cell_cursor.insertText(role, char_format)

        # Content
        if is_html and pre_html:
            cell_cursor.insertHtml(f"<div style='margin-top:4px;font-size:13px;font-weight:normal;color:#c9d1d9;'>{pre_html}</div>")
        else:
            char_format.setFontWeight(QFont.Weight.Normal)
            char_format.setFontPointSize(13)
            char_format.setForeground(QColor("#c9d1d9"))
            cell_cursor.insertText(content, char_format)

        # Spacer
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText("\n")
        self.messages_view.setTextCursor(cursor)
        self.messages_view.ensureCursorVisible()

    def _update_assistant_display(self):
        doc = self.messages_view.document()
        block = doc.lastBlock()
        if block.text().startswith("Assistant"):
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            # Remove old and re-add
        # Simpler: just append a new block showing current state
        # We'll use a simpler approach for streaming
        pass

    def _escape(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    def show_welcome(self):
        html = """
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:28px;font-weight:700;color:#58a6ff;margin-bottom:12px;">Llama.cpp AI Assistant</div>
            <div style="font-size:14px;color:#8b949e;margin-bottom:30px;">Tool Calls & Visual Scripting</div>
            <div style="font-size:13px;color:#484f58;">Load a model from File → Load Model to begin</div>
        </div>
        """
        self.messages_view.setHtml(html)

    def show_no_model(self):
        self.append_system_message("No model loaded. Go to File → Load Model to get started.")

# ═══════════════════════════════════════════════════════════════════
#  STREAMING CHAT DISPLAY (simplified approach)
# ═══════════════════════════════════════════════════════════════════

class StreamingChatWidget(QWidget):
    send_requested = Signal(str)
    stop_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.display = QTextEdit()
        self.display.setReadOnly(True)
        layout.addWidget(self.display, 1)

        input_bar = QWidget()
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message... (Enter to send)")
        self.input_field.setMinimumHeight(44)
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("accentBtn")
        self.send_btn.setFixedWidth(90)
        self.send_btn.setMinimumHeight(44)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.setFixedWidth(80)
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setVisible(False)
        self.stop_btn.clicked.connect(self.stop_requested.emit)
        input_layout.addWidget(self.stop_btn)

        layout.addWidget(input_bar)
        self._streaming = False
        self._stream_text = ""
        self.show_welcome()

    def _on_send(self):
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self.send_requested.emit(text)

    def set_generating(self, v):
        self._streaming = v
        self.send_btn.setVisible(not v)
        self.stop_btn.setVisible(v)
        self.input_field.setEnabled(not v)

    def _esc(self, t):
        return t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _append_block(self, role, content, color, bg_color, is_html=False):
        c = self._esc(content) if not is_html else content
        self.display.append(
            f'<div style="margin:6px 0;padding:8px 12px;border-radius:8px;'
            f'background:{bg_color};border-left:3px solid {color};">'
            f'<span style="color:{color};font-weight:700;font-size:12px;">{role}</span><br>'
            f'<span style="color:#c9d1d9;font-size:14px;">{c}</span></div>'
        )
        sb = self.display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def show_welcome(self):
        self.display.setHtml("""
            <div style="text-align:center;padding:80px 20px;">
                <div style="font-size:32px;font-weight:800;color:#58a6ff;margin-bottom:8px;
                    letter-spacing:-0.5px;">Llama.cpp Assistant</div>
                <div style="font-size:15px;color:#8b949e;margin-bottom:32px;">
                    Tool Calls &bull; Visual Scripting &bull; Local AI</div>
                <div style="font-size:13px;color:#484f58;max-width:400px;margin:0 auto;line-height:1.6;">
                    Load a GGUF model via <b>File → Load Model</b> to begin.
                    Right-click the Visual Script canvas to add nodes.
                    Build workflows and register them as callable tools.</div>
            </div>""")

    def show_no_model(self):
        self._append_block("System", "No model loaded. Use File → Load Model to start.", "#8b949e", "#161b22")

    def append_user(self, text):
        self._append_block("You", text, "#c9d1d9", "#161b22")

    def start_assistant_stream(self):
        self._stream_text = ""
        self._streaming = True
        self.display.append(
            '<div id="stream_block" style="margin:6px 0;padding:8px 12px;border-radius:8px;'
            'background:#0d1117;border-left:3px solid #58a6ff;">'
            '<span style="color:#58a6ff;font-weight:700;font-size:12px;">Assistant</span><br>'
            '<span id="stream_content" style="color:#c9d1d9;font-size:14px;"></span></div>')

    def append_token(self, token):
        self._stream_text += self._esc(token)
        cursor = self.display.textCursor()
        doc = self.display.document()
        # Find the stream content span and replace
        html = self.display.toHtml()
        html = html.replace(
            '<span id="stream_content" style="color:#c9d1d9;font-size:14px;"></span>',
            f'<span id="stream_content" style="color:#c9d1d9;font-size:14px;">{self._stream_text}</span>'
        )
        self.display.setHtml(html)
        sb = self.display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def end_assistant_stream(self):
        if not self._streaming:
            if self._stream_text:
                self._append_block("Assistant", self._stream_text.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">"), "#58a6ff", "#0d1117")
        self._streaming = False
        self._stream_text = ""

    def append_tool_calls(self, tool_calls):
        for tc in tool_calls:
            fname = tc["function"]["name"]
            args = tc["function"].get("arguments", "{}")
            try:
                args_fmt = json.dumps(json.loads(args), indent=2)
            except:
                args_fmt = args
            html = f'<span style="color:#d29922;font-weight:600;">⚙ {self._esc(fname)}</span><br>'
            html += f'<pre style="color:#8b949e;margin:4px 0;font-size:12px;">{self._esc(args_fmt)}</pre>'
            self._append_block("Tool Call", "", "#d29922", "#1a1500", is_html=True)
            # Append the html directly
            self.display.append(
                f'<div style="margin:6px 0;padding:8px 12px;border-radius:8px;'
                f'background:#1a1500;border-left:3px solid #d29922;">'
                f'<span style="color:#d29922;font-weight:700;font-size:12px;">Tool Call</span><br>'
                f'{html}</div>')
            sb = self.display.verticalScrollBar()
            sb.setValue(sb.maximum())

    def append_tool_result(self, name, result, success):
        color = "#3fb950" if success else "#f85149"
        icon = "✓" if success else "✗"
        self.display.append(
            f'<div style="margin:6px 0;padding:8px 12px;border-radius:8px;'
            f'background:#0d1117;border-left:3px solid {color};">'
            f'<span style="color:{color};font-weight:700;font-size:12px;">{icon} Tool Result: {self._esc(name)}</span><br>'
            f'<pre style="color:#8b949e;margin:4px 0;font-size:12px;max-height:200px;overflow:auto;">{self._esc(result[:2000])}</pre>'
            f'</div>')
        sb = self.display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def append_error(self, text):
        self._append_block("Error", text, "#f85149", "#1a0000")

# ═══════════════════════════════════════════════════════════════════
#  TOOL PANEL
# ═══════════════════════════════════════════════════════════════════

class ToolPanel(QWidget):
    def __init__(self, tool_mgr: ToolManager):
        super().__init__()
        self.tool_mgr = tool_mgr
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel("Registered Tools")
        label.setStyleSheet("font-weight:700;font-size:13px;color:#58a6ff;padding:4px;")
        layout.addWidget(label)

        self.tool_list = QListWidget()
        self.tool_list.setSpacing(2)
        layout.addWidget(self.tool_list, 1)

        self.refresh()

    def refresh(self):
        self.tool_list.clear()
        for t in self.tool_mgr.list_tools():
            item = QListWidgetItem(f"⚙ {t.name}")
            item.setToolTip(t.description)
            item.setData(Qt.ItemDataRole.UserRole, t.name)
            self.tool_list.addItem(item)

# ═══════════════════════════════════════════════════════════════════
#  NODE PROPERTIES PANEL
# ═══════════════════════════════════════════════════════════════════

class NodePropertiesPanel(QWidget):
    node_data_changed = Signal()

    def __init__(self, tool_mgr: ToolManager):
        super().__init__()
        self.tool_mgr = tool_mgr
        self.current_node: Optional[NodeItem] = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.title_label = QLabel("Select a node")
        self.title_label.setStyleSheet("font-weight:700;font-size:14px;color:#58a6ff;padding:4px;")
        layout.addWidget(self.title_label)

        self.form_widget = QWidget()
        self.form_layout = QFormLayout(self.form_widget)
        self.form_layout.setContentsMargins(0, 8, 0, 0)
        self.form_layout.setSpacing(8)
        layout.addWidget(self.form_widget, 1)

        layout.addStretch()

    def set_node(self, node: Optional[NodeItem]):
        self.current_node = node
        # Clear form
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        if not node:
            self.title_label.setText("Select a node")
            return

        color = NODE_COLORS.get(node.node_type, "#8b949e")
        self.title_label.setText(f'<span style="color:{color};">● </span>{node.node_type.value}')
        self.title_label.setTextFormat(Qt.TextFormat.RichText)

        if node.node_type == NodeType.SCRIPT_INPUT:
            self._add_field("param_name", "Name", node.get_data("param_name", "input"))
            combo = QComboBox()
            combo.addItems(["string", "number", "boolean", "json"])
            combo.setCurrentText(node.get_data("data_type", "string"))
            combo.currentTextChanged.connect(lambda v: self._set("data_type", v))
            self.form_layout.addRow("Data Type:", combo)
            self._add_field("description", "Description", node.get_data("description", ""))
            self._add_field("default_value", "Default", node.get_data("default_value", ""))

        elif node.node_type == NodeType.TOOL_CALL:
            combo = QComboBox()
            combo.addItem("-- Select Tool --", "")
            for t in self.tool_mgr.list_tools():
                combo.addItem(t.name, t.name)
            idx = combo.findData(node.get_data("tool_name", ""))
            if idx >= 0: combo.setCurrentIndex(idx)
            combo.currentTextChanged.connect(lambda v: self._set("tool_name", v))
            self.form_layout.addRow("Tool:", combo)
            self._add_field("tool_args_desc", "Args Hint", node.get_data("tool_args_desc", "pass via connection"))

        elif node.node_type == NodeType.TRANSFORM:
            edit = QPlainTextEdit()
            edit.setPlainText(node.get_data("expression", ""))
            edit.setPlaceholderText("e.g. input.upper()\nlen(input)\njson.dumps(input)")
            edit.setMaximumHeight(80)
            edit.textChanged.connect(lambda: self._set("expression", edit.toPlainText()))
            self.form_layout.addRow("Expression:", edit)
            hint = QLabel("Vars: input (from port)\nBuiltins: int, float, str, len, json, math, upper, lower, strip, split, join, replace")
            hint.setStyleSheet("color:#484f58;font-size:11px;")
            hint.setWordWrap(True)
            self.form_layout.addRow(hint)

        elif node.node_type == NodeType.SCRIPT_OUTPUT:
            self._add_field("output_name", "Name", node.get_data("output_name", "output"))

    def _add_field(self, key, label, value):
        edit = QLineEdit(str(value) if value else "")
        edit.textChanged.connect(lambda v, k=key: self._set(k, v))
        self.form_layout.addRow(f"{label}:", edit)

    def _set(self, key, value):
        if self.current_node:
            self.current_node.set_data(key, value)
            self.current_node.update()
            self.node_data_changed.emit()

# ═══════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    def __init__(self, settings: Dict, parent=None):
        super().__init__(parent)
        self.settings = settings.copy()
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)

        self.ctx_spin = QSpinBox()
        self.ctx_spin.setRange(512, 131072)
        self.ctx_spin.setSingleStep(512)
        self.ctx_spin.setValue(settings["n_ctx"])
        form.addRow("Context Size:", self.ctx_spin)

        self.gpu_spin = QSpinBox()
        self.gpu_spin.setRange(-1, 128)
        self.gpu_spin.setValue(settings["n_gpu_layers"])
        self.gpu_spin.setToolTip("-1 = all layers to GPU")
        form.addRow("GPU Layers:", self.gpu_spin)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setDecimals(2)
        self.temp_spin.setValue(settings["temperature"])
        form.addRow("Temperature:", self.temp_spin)

        self.topp_spin = QDoubleSpinBox()
        self.topp_spin.setRange(0.0, 1.0)
        self.topp_spin.setSingleStep(0.05)
        self.topp_spin.setDecimals(2)
        self.topp_spin.setValue(settings["top_p"])
        form.addRow("Top P:", self.topp_spin)

        self.max_spin = QSpinBox()
        self.max_spin.setRange(64, 16384)
        self.max_spin.setSingleStep(256)
        self.max_spin.setValue(settings["max_tokens"])
        form.addRow("Max Tokens:", self.max_spin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Apply")
        ok.setObjectName("accentBtn")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

    def get_settings(self):
        return {
            "n_ctx": self.ctx_spin.value(),
            "n_gpu_layers": self.gpu_spin.value(),
            "temperature": self.temp_spin.value(),
            "top_p": self.topp_spin.value(),
            "max_tokens": self.max_spin.value(),
        }

# ═══════════════════════════════════════════════════════════════════
#  REGISTER SCRIPT DIALOG
# ═══════════════════════════════════════════════════════════════════

class RegisterScriptDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register Script as Tool")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(12)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("my_custom_tool")
        form.addRow("Tool Name:", self.name_edit)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Description the LLM will see")
        form.addRow("Description:", self.desc_edit)
        layout.addLayout(form)

        btns = QHBoxLayout()
        ok = QPushButton("Register")
        ok.setObjectName("accentBtn")
        ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(ok)
        layout.addLayout(btns)

# ═══════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Llama.cpp AI Assistant — Tool Calls & Visual Scripting")
        self.resize(1280, 820)

        self.tool_mgr = ToolManager()
        self.script_engine = ScriptEngine(self.tool_mgr)
        self.backend = LlamaBackend(self.tool_mgr)
        self.chat_history: List[Dict] = []

        self._build_ui()
        self._build_menus()
        self._connect_signals()
        self.statusBar().showMessage("Ready — Load a model to begin")

    def _build_ui(self):
        # Central: tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Chat tab
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat = StreamingChatWidget()
        chat_layout.addWidget(self.chat)
        self.tabs.addTab(chat_container, "💬 Chat")

        # Visual Script tab
        script_container = QWidget()
        script_layout = QHBoxLayout(script_container)
        script_layout.setContentsMargins(0, 0, 0, 0)
        script_layout.setSpacing(0)

        # Script toolbar
        script_toolbar = QWidget()
        stb_layout = QHBoxLayout(script_toolbar)
        stb_layout.setContentsMargins(8, 4, 8, 4)
        stb_layout.setSpacing(6)
        for nt in NodeType:
            btn = QPushButton(f"+ {nt.value}")
            btn.clicked.connect(lambda checked, t=nt: self._add_node_center(t))
            stb_layout.addWidget(btn)
        stb_layout.addStretch()
        self.run_btn = QPushButton("▶ Run Script")
        self.run_btn.setObjectName("accentBtn")
        self.run_btn.clicked.connect(self._run_script)
        stb_layout.addWidget(self.run_btn)
        self.register_btn = QPushButton("📋 Register as Tool")
        self.register_btn.clicked.connect(self._register_script)
        stb_layout.addWidget(self.register_btn)
        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.clicked.connect(self._clear_script)
        stb_layout.addWidget(self.clear_btn)

        script_vlayout = QVBoxLayout()
        script_vlayout.setContentsMargins(0, 0, 0, 0)
        script_vlayout.setSpacing(0)
        script_vlayout.addWidget(script_toolbar)

        # Node editor
        self.node_scene = NodeEditorScene()
        self.node_view = NodeEditorView(self.node_scene)
        self.node_view.setSceneRect(-2000, -2000, 4000, 4000)
        script_vlayout.addWidget(self.node_view, 1)

        # Result area
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setMaximumHeight(120)
        self.result_area.setPlaceholderText("Script execution results will appear here...")
        script_vlayout.addWidget(self.result_area)

        script_layout.addLayout(script_vlayout, 1)

        # Properties panel
        self.props_panel = NodePropertiesPanel(self.tool_mgr)
        self.props_panel.setFixedWidth(260)
        script_layout.addWidget(self.props_panel)

        self.tabs.addTab(script_container, "🔧 Visual Script")

        # Tool dock
        self.tool_dock = QDockWidget("Tools", self)
        self.tool_panel = ToolPanel(self.tool_mgr)
        self.tool_dock.setWidget(self.tool_panel)
        self.tool_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tool_dock)

    def _build_menus(self):
        mb = self.menuBar()
        file_menu = mb.addMenu("File")
        file_menu.addAction("Load Model...", self._load_model_dialog, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("Settings...", self._show_settings, QKeySequence("Ctrl+,"))
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close, QKeySequence("Ctrl+Q"))

        edit_menu = mb.addMenu("Edit")
        edit_menu.addAction("Clear Chat", self._clear_chat)

        help_menu = mb.addMenu("Help")
        help_menu.addAction("About", self._show_about)

    def _connect_signals(self):
        self.chat.send_requested.connect(self._on_chat_send)
        self.chat.stop_requested.connect(self._on_stop)
        self.node_scene.node_selected.connect(self.props_panel.set_node)
        self.node_scene.items_removed.connect(self._on_script_changed)
        self.node_scene.connection_added.connect(self._on_script_changed)
        self.node_scene.connection_removed.connect(self._on_script_changed)
        self.props_panel.node_data_changed.connect(self._on_script_changed)

    # ── Model Loading ──

    def _load_model_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load GGUF Model", "",
            "GGUF Models (*.gguf *.bin);;All Files (*)")
        if path:
            self.statusBar().showMessage(f"Loading {os.path.basename(path)}...")
            self.backend.load_model(path,
                lambda msg: self.statusBar().showMessage(msg),
                lambda m: self._on_model_loaded(m, path),
                lambda e: self._on_model_error(e))

    def _on_model_loaded(self, model, path):
        name = os.path.basename(path)
        self.statusBar().showMessage(f"Model loaded: {name}", 5000)
        self.chat.append_system_message(f"Model loaded: {name}")

    def _on_model_error(self, error):
        self.statusBar().showMessage(f"Error: {error}")
        QMessageBox.critical(self, "Model Load Error", error)
        if not LLAMA_AVAILABLE:
            QMessageBox.information(self, "Missing Package",
                "llama-cpp-python is not installed.\n\nInstall with:\n"
                "  pip install llama-cpp-python\n\n"
                "For GPU support:\n"
                "  CMAKE_ARGS='-DGGML_CUDA=on' pip install llama-cpp-python --force-reinstall --no-cache-dir")

    def _show_settings(self):
        dlg = SettingsDialog(self.backend.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.backend.settings = dlg.get_settings()
            self.statusBar().showMessage("Settings updated", 2000)

    # ── Chat ──

    def _on_chat_send(self, text: str):
        if not self.backend.is_loaded():
            self.chat.show_no_model()
            return

        self.chat.append_user(text)
        self.chat_history.append({"role": "user", "content": text})
        self.chat.set_generating(True)
        self.chat.start_assistant_stream()

        self.backend.chat(
            messages=self.chat_history,
            stream_cb=self.chat.append_token,
            tool_call_cb=self._on_tool_calls,
            tool_result_cb=self.chat.append_tool_result,
            complete_cb=self._on_response_complete,
            error_cb=self._on_response_error
        )

    def _on_tool_calls(self, tool_calls):
        self.chat.end_assistant_stream()
        self.chat.append_tool_calls(tool_calls)

    def _on_response_complete(self, content):
        self.chat.end_assistant_stream()
        self.chat_history.append({"role": "assistant", "content": content})
        self.chat.set_generating(False)

    def _on_response_error(self, error):
        self.chat.end_assistant_stream()
        self.chat.append_error(error)
        self.chat.set_generating(False)

    def _on_stop(self):
        self.backend.stop_generation()
        self.chat.end_assistant_stream()
        self.chat.set_generating(False)
        self.statusBar().showMessage("Generation stopped", 2000)

    def _clear_chat(self):
        self.chat_history.clear()
        self.chat.display.clear()
        self.chat.show_welcome()

    # ── Visual Script ──

    def _add_node_center(self, node_type: NodeType):
        center = self.node_view.mapToScene(self.node_view.viewport().rect().center())
        node = self.node_scene.add_node(node_type, center.x(), center.y())
        node.setSelected(True)
        self.node_scene.node_selected.emit(node)

    def _run_script(self):
        nodes, connections = self.node_scene.get_all_data()
        if not nodes:
            self.result_area.setPlainText("No nodes to execute.")
            return

        # Collect input values
        inputs = {}
        for n in nodes:
            if n["type"] == "SCRIPT_INPUT":
                pname = n.get("param_name", "input")
                default = n.get("default_value", "")
                val, ok = QInputDialog.getText(self, f"Input: {pname}",
                    f"Value for '{pname}' ({n.get('data_type','string')}):",
                    text=str(default) if default else "")
                if not ok:
                    return
                inputs[pname] = val

        try:
            results = self.script_engine.execute(nodes, connections, inputs)
            self.result_area.setPlainText(json.dumps(results, indent=2, ensure_ascii=False))
        except Exception as e:
            self.result_area.setPlainText(f"Execution Error:\n{traceback.format_exc()}")

    def _register_script(self):
        nodes, connections = self.node_scene.get_all_data()
        input_nodes = [n for n in nodes if n["type"] == "SCRIPT_INPUT"]
        output_nodes = [n for n in nodes if n["type"] == "SCRIPT_OUTPUT"]
        if not input_nodes or not output_nodes:
            QMessageBox.warning(self, "Invalid Script",
                "Script must have at least one Script Input and one Script Output node.")
            return

        dlg = RegisterScriptDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name = dlg.name_edit.text().strip()
        desc = dlg.desc_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid", "Tool name is required.")
            return

        td = self.script_engine.to_tool_definition(name, desc, nodes)
        if td:
            # Attach connection list for execution
            td.handler = lambda **kwargs, n=nodes, c=connections: ToolResult(
                True, json.dumps(self.script_engine.execute(n, c, kwargs), ensure_ascii=False))
            self.tool_mgr.register(td)
            self.tool_panel.refresh()
            self.statusBar().showMessage(f"Registered tool: {name}", 3000)
            QMessageBox.information(self, "Registered",
                f"Tool '{name}' registered successfully.\n"
                f"It will be available for the LLM to call.")
        else:
            QMessageBox.warning(self, "Error", "Failed to create tool definition.")

    def _clear_script(self):
        r = QMessageBox.question(self, "Clear Script", "Remove all nodes and connections?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self.node_scene.clear_all()
            self.result_area.clear()

    def _on_script_changed(self, *args):
        # Update connection refs for registered tools
        pass

    # ── Help ──

    def _show_about(self):
        QMessageBox.about(self, "About",
            "<h3>Llama.cpp AI Assistant</h3>"
            "<p>Tool Calls & Visual Scripting</p>"
            "<p>Built with PySide6 + llama-cpp-python</p>"
            "<hr>"
            "<p><b>Chat:</b> Load a GGUF model, then chat. The LLM can call registered tools.</p>"
            "<p><b>Visual Script:</b> Right-click to add nodes. Connect output→input ports. "
            "Register scripts as tools the LLM can invoke.</p>"
            "<p><b>Shortcuts:</b> Delete=remove, Scroll=zoom, Middle-drag=pan, Esc=cancel</p>")


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLE)

    # Dark palette fallback
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#c9d1d9"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#0d1117"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#161b22"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#c9d1d9"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#c9d1d9"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#21262d"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#c9d1d9"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#58a6ff"))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()