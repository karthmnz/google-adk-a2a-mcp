import json
import random
from typing import Any, AsyncIterable, Dict, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
import asyncio

class CountryInput(BaseModel):
    country: str = Field(description="The country to get information about.")

class CaptialAgent:
    """An agent that tells Capitals of a country"""

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
    APP_NAME = "agent_comparison_app"
    USER_ID = "test_user_456"
    SESSION_ID_TOOL_AGENT = "session_tool_agent_xyz"
    SESSION_ID_SCHEMA_AGENT = "session_schema_agent_xyz"
    MODEL_NAME = "gemini-1.5-flash"

    def __init__(self):
        self._agent = asyncio.run(self._build_agent()) 
        self._user_id = "remote_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )

    def invoke(self, query, session_id) -> str:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = list(
            self._runner.run(
                user_id=self._user_id, session_id=session.id, new_message=content
            )
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return ""
        return "\n".join([p.text for p in events[-1].content.parts if p.text])
    
    async def get_tools_async(self):
        tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='python',
                args=["mcps/capital/main.py"
                ]
            )
            # connection_params=SseServerParams(url="http://remote-server:port/path", headers={...})
        )
        return tools, exit_stack

    async def stream(self, query, session_id) -> AsyncIterable[Dict[str, Any]]:
        session = self._runner.session_service.get_session(
            app_name=self._agent.name, user_id=self._user_id, session_id=session_id
        )
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                elif (
                    event.content
                    and event.content.parts
                    and any([True for p in event.content.parts if p.function_response])
                ):
                    response = next(
                        (p.function_response.model_dump() for p in event.content.parts)
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "Processing the reimbursement request...",
                }

    async def _build_agent(self) -> LlmAgent:
        """Builds the Cpaital agent that tells Capitals of a country"""
        tool_mcp, _ = await self.get_tools_async()
        return LlmAgent(
            model="gemini-1.5-flash",
            name="capital_agent_tool",
            description="Retrieves the capital city using a specific tool.",
            instruction="""You are a helpful agent that provides the capital city of a country using a tool.
        The user will provide the country name in a JSON format like {"country": "country_name"}.
        1. Extract the country name.
        2. Use the `get_capital_city` tool to find the capital.
        3. Respond clearly to the user, stating the capital city found by the tool.
        """,
            tools=tool_mcp,
        )