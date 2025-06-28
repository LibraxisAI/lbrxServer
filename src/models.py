"""
Pydantic models for API requests/responses
"""
from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: str | None = None
    function_call: dict[str, Any] | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    stop: str | list[str] | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    seed: int | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None

    # Custom fields for session management
    session_id: str | None = None
    sandbox_id: str | None = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"] | None = None
    logprobs: dict[str, Any] | None = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    system_fingerprint: str
    choices: list[Choice]
    usage: Usage


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    system_fingerprint: str
    choices: list[dict[str, Any]]


class CompletionRequest(BaseModel):
    model: str
    prompt: str | list[str]
    suffix: str | None = None
    max_tokens: int | None = Field(default=16, ge=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    logprobs: int | None = None
    echo: bool = False
    stop: str | list[str] | None = None
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    best_of: int = Field(default=1, ge=1)
    logit_bias: dict[str, float] | None = None
    user: str | None = None
    seed: int | None = None


class EmbeddingRequest(BaseModel):
    model: str
    input: str | list[str]
    encoding_format: Literal["float", "base64"] = "float"
    user: str | None = None


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    index: int
    embedding: list[float]


class EmbeddingResponse(BaseModel):
    object: Literal["list"] = "list"
    data: list[EmbeddingData]
    model: str
    usage: dict[str, int]


class Model(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "libraxis"
    permission: list[dict[str, Any]] = []
    root: str
    parent: str | None = None


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: list[Model]


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
