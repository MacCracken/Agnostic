import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TeamConfig:
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "team_config.json"
            )
        
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded team configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Team config not found at {self.config_path}, using defaults")
            return self._get_defaults()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in team config: {e}")
            return self._get_defaults()
    
    def _get_defaults(self) -> Dict[str, Any]:
        return {
            "team_presets": {
                "standard": {
                    "agent_count": 6,
                    "agents": ["qa-manager", "senior-qa", "junior-qa", "qa-analyst", "security-compliance", "performance"],
                    "workflow_mode": "specialized"
                }
            },
            "default_team_size": "standard"
        }
    
    def get_team_size(self) -> str:
        return os.getenv("QA_TEAM_SIZE", self._config.get("default_team_size", "standard"))
    
    def get_team_preset(self, size: Optional[str] = None) -> Dict[str, Any]:
        size = size or self.get_team_size()
        presets = self._config.get("team_presets", {})
        return presets.get(size, presets.get("standard", {}))
    
    def get_agent_config(self, agent_key: str) -> Optional[Dict[str, Any]]:
        roles = self._config.get("agent_roles", {})
        return roles.get(agent_key)
    
    def get_workflow_mode(self) -> str:
        preset = self.get_team_preset()
        return preset.get("workflow_mode", "specialized")
    
    def get_workflow_config(self) -> Dict[str, Any]:
        mode = self.get_workflow_mode()
        workflows = self._config.get("workflows", {})
        return workflows.get(mode, workflows.get("specialized", {}))
    
    def get_routing_for_complexity(self, complexity: str) -> str:
        routing = self._config.get("complexity_routing", {})
        return routing.get(complexity, {}).get("route_to", "junior-qa")
    
    def get_delegation_rules(self) -> Dict[str, Any]:
        workflow = self.get_workflow_config()
        return workflow.get("delegation_rules", {})
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        workflow = self.get_workflow_config()
        return workflow.get("agent_capabilities", {})
    
    def get_all_agents_for_current_team(self) -> List[str]:
        preset = self.get_team_preset()
        return preset.get("agents", [])
    
    def is_agent_in_current_team(self, agent_key: str) -> bool:
        return agent_key in self.get_all_agents_for_current_team()
    
    def get_tools_for_agent(self, agent_key: str) -> List[str]:
        agent_config = self.get_agent_config(agent_key)
        if agent_config:
            return agent_config.get("tools", [])
        return []
    
    def get_agent_focus(self, agent_key: str) -> str:
        agent_config = self.get_agent_config(agent_key)
        if agent_config:
            return agent_config.get("focus", "")
        return ""
    
    def get_team_summary(self) -> Dict[str, Any]:
        preset = self.get_team_preset()
        return {
            "team_size": self.get_team_size(),
            "agent_count": preset.get("agent_count", 0),
            "agents": preset.get("agents", []),
            "workflow_mode": preset.get("workflow_mode", "specialized"),
            "description": preset.get("description", "")
        }
    
    def supports_dynamic_scaling(self) -> bool:
        return self._config.get("supports_dynamic_scaling", True)


team_config = TeamConfig()
