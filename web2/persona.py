"""
数据模型定义 - 人格（Persona）配置
"""

from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
import uuid
import json
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class Persona:
    """人格配置（Agent）"""
    id: str
    full_name: str
    nickname: str
    role: str
    personality: str
    scenario: str
    system_prompt: str
    llm_profile_id: Optional[str] = None  # 绑定的 LLM 配置 ID
    description: str = ""
    enabled: bool = True  # 是否启用（替代原来Agent开关）
    mcp_enabled: bool = False  # 是否启用 MCP 服务
    mcp_servers: Optional[List[str]] = None  # 启用的 MCP 服务器列表
    skills: Optional[List[str]] = None  # 启用的技能工具列表
    is_active: bool = False
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """初始化默认值"""
        if self.mcp_servers is None:
            self.mcp_servers = []
        if self.skills is None:
            self.skills = []
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        """从字典创建"""
        return cls(**data)
    
    def build_system_prompt(self) -> str:
        """构建完整系统提示词"""
        prompt_parts = []
        
        if self.full_name:
            prompt_parts.append(f"姓名：{self.full_name}")
        if self.nickname:
            prompt_parts.append(f"昵称：{self.nickname}")
        if self.role:
            prompt_parts.append(f"身份：{self.role}")
        if self.personality:
            prompt_parts.append(f"性格：{self.personality}")
        if self.scenario:
            prompt_parts.append(f"场景：{self.scenario}")
        if self.system_prompt:
            if prompt_parts:
                prompt_parts.append("")
            prompt_parts.append(self.system_prompt)
        
        return "\n".join(prompt_parts)


class PersonaStore:
    """人格配置存储"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _read_file(self) -> dict:
        """读取存储文件"""
        if not self.storage_path.exists():
            return {"personas": [], "active_id": None}
        
        with open(self.storage_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _write_file(self, data: dict) -> None:
        """写入存储文件"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def list_personas(self) -> List[Persona]:
        """列出所有人格"""
        data = self._read_file()
        personas = []
        for p_data in data.get("personas", []):
            personas.append(Persona.from_dict(p_data))
        return personas
    
    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """获取单个人格"""
        personas = self.list_personas()
        for p in personas:
            if p.id == persona_id:
                return p
        return None
    
    def create_persona(
        self,
        full_name: str,
        nickname: str,
        role: str,
        personality: str,
        scenario: str,
        system_prompt: str,
        llm_profile_id: Optional[str] = None,
        description: str = "",
        enabled: bool = True,
        mcp_enabled: bool = False,
        mcp_servers: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
    ) -> Persona:
        """创建新人格"""
        now = datetime.now().isoformat()
        persona = Persona(
            id=str(uuid.uuid4()),
            full_name=full_name,
            nickname=nickname,
            role=role,
            personality=personality,
            scenario=scenario,
            system_prompt=system_prompt,
            llm_profile_id=llm_profile_id,
            description=description,
            enabled=enabled,
            mcp_enabled=mcp_enabled,
            mcp_servers=mcp_servers,
            skills=skills,
            is_active=False,
            created_at=now,
            updated_at=now,
        )
        
        data = self._read_file()
        personas = data.get("personas", [])
        personas.append(persona.to_dict())
        data["personas"] = personas
        self._write_file(data)
        
        return persona
    
    def update_persona(
        self,
        persona_id: str,
        **kwargs,
    ) -> Optional[Persona]:
        """更新人格"""
        data = self._read_file()
        personas = data.get("personas", [])
        
        for i, p_data in enumerate(personas):
            if p_data["id"] == persona_id:
                # 更新字段
                for key, value in kwargs.items():
                    if value is not None:
                        p_data[key] = value
                p_data["updated_at"] = datetime.now().isoformat()
                
                personas[i] = p_data
                data["personas"] = personas
                self._write_file(data)
                
                return Persona.from_dict(p_data)
        
        return None
    
    def delete_persona(self, persona_id: str) -> bool:
        """删除人格"""
        data = self._read_file()
        personas = data.get("personas", [])
        
        original_len = len(personas)
        personas = [p for p in personas if p["id"] != persona_id]
        
        if len(personas) == original_len:
            return False
        
        # 如果删除的是激活的，清除激活状态
        if data.get("active_id") == persona_id:
            data["active_id"] = None
        
        data["personas"] = personas
        self._write_file(data)
        
        return True
    
    def activate_persona(self, persona_id: str) -> bool:
        """激活人格"""
        data = self._read_file()
        personas = data.get("personas", [])
        
        # 先取消所有激活
        found = False
        for p_data in personas:
            if p_data["id"] == persona_id:
                p_data["is_active"] = True
                found = True
            else:
                p_data["is_active"] = False
        
        if not found:
            return False
        
        data["active_id"] = persona_id
        data["personas"] = personas
        self._write_file(data)
        
        return True
    
    def get_active_persona(self) -> Optional[Persona]:
        """获取当前激活的人格"""
        data = self._read_file()
        active_id = data.get("active_id")
        
        if not active_id:
            return None
        
        return self.get_persona(active_id)
    
    def get_active_id(self) -> Optional[str]:
        """获取当前激活的 ID"""
        data = self._read_file()
        return data.get("active_id")