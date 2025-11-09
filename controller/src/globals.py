from typing import List, Dict, Union, Optional, Any

class Globals:
    process_metadata: List[Dict[str, Any]] = []
    controller_init_time : str = ""
    thread_manager = None
    api_auth = None
    target_managers = {}
