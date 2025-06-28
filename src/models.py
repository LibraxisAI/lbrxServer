"""
Pydantic models for API requests/responses
"""
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "function"]
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = Field(default=None, ge=1)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    seed: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    response_format: Optional[Dict[str, Any]] = None
    
    # Custom fields for session management
    session_id: Optional[str] = None
    sandbox_id: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[Literal["stop", "length", "content_filter", "tool_calls"]] = None
    logprobs: Optional[Dict[str, Any]] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"]
    created: int
    model: str
    system_fingerprint: str
    choices: List[Choice]
    usage: Usage


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"]
    created: int
    model: str
    system_fingerprint: str
    choices: List[Dict[str, Any]]


class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    suffix: Optional[str] = None
    max_tokens: Optional[int] = Field(default=16, ge=1)
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stream: bool = False
    logprobs: Optional[int] = None
    echo: bool = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    best_of: int = Field(default=1, ge=1)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    seed: Optional[int] = None


class EmbeddingRequest(BaseModel):
    model: str
    input: Union[str, List[str]]
    encoding_format: Literal["float", "base64"] = "float"
    user: Optional[str] = None


class EmbeddingData(BaseModel):
    object: Literal["embedding"] = "embedding"
    index: int
    embedding: List[float]


class EmbeddingResponse(BaseModel):
    object: Literal["list"] = "list"
    data: List[EmbeddingData]
    model: str
    usage: Dict[str, int]


class Model(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str = "libraxis"
    permission: List[Dict[str, Any]] = []
    root: str
    parent: Optional[str] = None


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: List[Model]


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: Optional[str] = None
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail