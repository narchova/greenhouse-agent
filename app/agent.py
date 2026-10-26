# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

import json
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

try:
    from app.a2ui.schema.manager import A2uiSchemaManager
    from app.a2ui.basic_catalog.provider import BasicCatalog
except ImportError:
    from a2ui.schema.manager import A2uiSchemaManager
    from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback

from app.firestore_tools import (
    list_plants,
    search_plants_by_light,
    get_plant_details,
    add_plant,
    log_plant_watering,
)
from app.gbif_tools import lookup_species_taxonomy
from app.maps_tools import geocode_address, find_nearby_places
from app.image_tools import generate_plant_image
from app.video_tools import generate_plant_video

MODEL = "gemini-3.8-flash"

# Configure AgentEngineSandboxCodeExecutor from deployment_metadata.json
_metadata_file = Path(__file__).resolve().parent.parent / "deployment_metadata.json"
_code_executor = None
if _metadata_file.exists():
    try:
        _meta = json.loads(_metadata_file.read_text())
        _agent_engine_id = _meta.get("remote_agent_runtime_id")
        if _agent_engine_id:
            _code_executor = AgentEngineSandboxCodeExecutor(
                agent_engine_resource_name=_agent_engine_id
            )
    except Exception:
        pass
if _code_executor is None:
    _code_executor = AgentEngineSandboxCodeExecutor()


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


# Build system prompt with A2uiSchemaManager (version 0.8) and the Basic Catalog
_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

_instruction = _schema_manager.generate_system_prompt(
    role_description=(
        "You are a friendly and knowledgeable greenhouse and indoor plant assistant. "
        "You help users manage and discover plants in the greenhouse catalog, check care "
        "requirements, search for plants matching their home lighting conditions, and add new plants to inventory. "
        "You remember the user's stated preferences, plant care history, and home environment from previous conversations "
        "and use them to personalize your advice."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=_instruction,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        list_plants,
        search_plants_by_light,
        get_plant_details,
        add_plant,
        log_plant_watering,
        lookup_species_taxonomy,
        geocode_address,
        find_nearby_places,
        generate_plant_image,
        generate_plant_video,
    ],
    code_executor=_code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
