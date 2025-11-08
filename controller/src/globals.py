from typing import List, Dict, Union, Optional, Any
from component_manager import ComponentManager

class Globals:
    process_metadata: List[Dict[str, Any]] = []
    controller_init_time : str = ""
    thread_manager : ComponentManager = None
