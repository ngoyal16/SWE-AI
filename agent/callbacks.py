from typing import Dict, Any, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from .common.storage import storage

class SessionCallbackHandler(BaseCallbackHandler):
    def __init__(self, session_id: str):
        self.session_id = session_id

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> Any:
        tool_name = serialized.get("name", "tool")
        storage.append_log(self.session_id, f"Executing tool '{tool_name}' with input: {input_str}")

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        # Truncate output if too long to avoid flooding logs with massive file contents
        output_str = str(output)
        if len(output_str) > 1000:
             storage.append_log(self.session_id, f"Tool output: {output_str[:1000]}... (truncated)")
        else:
             storage.append_log(self.session_id, f"Tool output: {output_str}")

    def on_tool_error(self, error: BaseException, **kwargs: Any) -> Any:
        storage.append_log(self.session_id, f"Tool error: {str(error)}")
