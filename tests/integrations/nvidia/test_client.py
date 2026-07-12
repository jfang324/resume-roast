"""NvidiaClient: SDK wiring, response handling, and error mapping."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx
import openai
import pytest

from resume_roast.integrations.nvidia.client import NvidiaClient
from resume_roast.integrations.nvidia.errors import (
    AuthenticationError,
    EmptyResponseError,
    NvidiaError,
    TransientError,
    TruncatedResponseError,
)
from resume_roast.integrations.nvidia.types import Message

# --- Stand-ins for the SDK's response objects (attribute-compatible) ---


@dataclass
class _FakeUsage:
    prompt_tokens: int = 10
    completion_tokens: int = 20
    total_tokens: int = 30


@dataclass
class _FakeMessage:
    content: str | None


@dataclass
class _FakeChoice:
    message: _FakeMessage
    finish_reason: str | None = "stop"


@dataclass
class _FakeResponse:
    choices: list[_FakeChoice]
    usage: _FakeUsage | None = None


@dataclass
class _FakeDelta:
    content: str | None


@dataclass
class _FakeStreamChoice:
    delta: _FakeDelta
    finish_reason: str | None = None


@dataclass
class _FakeChunk:
    choices: list[_FakeStreamChoice]
    usage: _FakeUsage | None = None


class _RecordingCompletions:
    """Stands in for `client.chat.completions`: returns or raises a canned result."""

    def __init__(self) -> None:
        self.result: object = None
        self.kwargs: dict[str, Any] = {}

    def create(self, **kwargs: Any) -> object:
        self.kwargs = kwargs
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


@dataclass
class _StubChat:
    completions: _RecordingCompletions


class _StubOpenAI:
    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs
        self.chat = _StubChat(completions=_RecordingCompletions())


@pytest.fixture
def stub_sdk(monkeypatch: pytest.MonkeyPatch) -> _StubOpenAI:
    created: list[_StubOpenAI] = []

    def factory(**kwargs: Any) -> _StubOpenAI:
        stub = _StubOpenAI(**kwargs)
        created.append(stub)
        return stub

    monkeypatch.setattr("resume_roast.integrations.nvidia.client.OpenAI", factory)
    NvidiaClient(api_key="test-key", model="test/model")  # pragma: allowlist secret
    return created[0]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, stub_sdk: _StubOpenAI) -> NvidiaClient:
    def factory(**_: Any) -> _StubOpenAI:
        return stub_sdk

    monkeypatch.setattr("resume_roast.integrations.nvidia.client.OpenAI", factory)
    return NvidiaClient(api_key="test-key", model="test/model")  # pragma: allowlist secret


def _status_error(cls: type[openai.APIStatusError], status_code: int) -> openai.APIStatusError:
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    response = httpx.Response(status_code, request=request)
    return cls("boom", response=response, body=None)


_MESSAGES = [Message(role="system", content="be brief"), Message(role="user", content="hi")]


class TestConstruction:
    def test_sdk_client_configuration(self, stub_sdk: _StubOpenAI) -> None:
        assert stub_sdk.init_kwargs == {
            "base_url": "https://integrate.api.nvidia.com/v1",
            "api_key": "test-key",  # pragma: allowlist secret
            "timeout": 180.0,
            "max_retries": 2,
        }


class TestPrompt:
    def test_returns_completion_with_usage(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(
            choices=[_FakeChoice(message=_FakeMessage(content="roasted"))],
            usage=_FakeUsage(),
        )

        completion = client.prompt(_MESSAGES)

        assert completion.text == "roasted"
        assert completion.finish_reason == "stop"
        assert completion.usage is not None
        assert completion.usage.total_tokens == 30

    def test_request_shape(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(
            choices=[_FakeChoice(message=_FakeMessage(content="ok"))]
        )

        client.prompt(_MESSAGES)

        kwargs = stub_sdk.chat.completions.kwargs
        assert kwargs["model"] == "test/model"
        assert kwargs["messages"] == [
            {"role": "system", "content": "be brief"},
            {"role": "user", "content": "hi"},
        ]
        assert kwargs["temperature"] == 0.0
        assert kwargs["max_tokens"] == 8192
        assert kwargs["stream"] is False
        # No extra_body: chat_template_kwargs are model-specific (Mistral
        # rejects them with a 400), and this client stays model-agnostic.
        assert "extra_body" not in kwargs

    def test_missing_usage_maps_to_none(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(
            choices=[_FakeChoice(message=_FakeMessage(content="ok"))], usage=None
        )

        assert client.prompt(_MESSAGES).usage is None

    def test_no_choices_raises_empty(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(choices=[])

        with pytest.raises(EmptyResponseError):
            client.prompt(_MESSAGES)

    def test_null_content_raises_empty(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(
            choices=[_FakeChoice(message=_FakeMessage(content=None))]
        )

        with pytest.raises(EmptyResponseError, match="finish_reason: stop"):
            client.prompt(_MESSAGES)

    def test_length_finish_raises_truncated(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = _FakeResponse(
            choices=[_FakeChoice(message=_FakeMessage(content="partial"), finish_reason="length")]
        )

        with pytest.raises(TruncatedResponseError, match="8192"):
            client.prompt(_MESSAGES)

    @pytest.mark.parametrize(
        ("sdk_error", "expected"),
        [
            (_status_error(openai.AuthenticationError, 401), AuthenticationError),
            (_status_error(openai.PermissionDeniedError, 403), AuthenticationError),
            (_status_error(openai.RateLimitError, 429), TransientError),
            (_status_error(openai.InternalServerError, 500), TransientError),
            (
                openai.APIConnectionError(
                    request=httpx.Request("POST", "https://integrate.api.nvidia.com/v1")
                ),
                TransientError,
            ),
            (openai.OpenAIError("unrecognized"), NvidiaError),
        ],
    )
    def test_sdk_error_mapping(
        self,
        client: NvidiaClient,
        stub_sdk: _StubOpenAI,
        sdk_error: openai.OpenAIError,
        expected: type[NvidiaError],
    ) -> None:
        stub_sdk.chat.completions.result = sdk_error

        with pytest.raises(expected):
            client.prompt(_MESSAGES)

    def test_auth_error_names_the_remedy(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = _status_error(openai.AuthenticationError, 401)

        with pytest.raises(AuthenticationError, match="resume-roast config credentials"):
            client.prompt(_MESSAGES)


class TestPromptStream:
    def test_yields_chunks_then_exposes_usage_and_finish_reason(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = [
            _FakeChunk(choices=[_FakeStreamChoice(delta=_FakeDelta(content="Hello"))]),
            _FakeChunk(choices=[_FakeStreamChoice(delta=_FakeDelta(content=" world"))]),
            _FakeChunk(
                choices=[_FakeStreamChoice(delta=_FakeDelta(content=None), finish_reason="stop")]
            ),
            _FakeChunk(choices=[], usage=_FakeUsage()),
        ]

        stream = client.prompt_stream(_MESSAGES)
        chunks = list(stream)

        assert chunks == ["Hello", " world"]
        assert stream.finish_reason == "stop"
        assert stream.usage is not None
        assert stream.usage.total_tokens == 30

    def test_request_shape(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        stub_sdk.chat.completions.result = []

        list(client.prompt_stream(_MESSAGES))

        kwargs = stub_sdk.chat.completions.kwargs
        assert kwargs["stream"] is True
        assert kwargs["stream_options"] == {"include_usage": True}
        assert kwargs["max_tokens"] == 8192
        assert "extra_body" not in kwargs

    def test_truncation_is_reported_not_raised(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = [
            _FakeChunk(
                choices=[
                    _FakeStreamChoice(delta=_FakeDelta(content="partial"), finish_reason="length")
                ]
            ),
        ]

        stream = client.prompt_stream(_MESSAGES)

        assert list(stream) == ["partial"]
        assert stream.finish_reason == "length"

    def test_usage_absent_when_server_omits_it(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = [
            _FakeChunk(choices=[_FakeStreamChoice(delta=_FakeDelta(content="hi"))]),
        ]

        stream = client.prompt_stream(_MESSAGES)
        list(stream)

        assert stream.usage is None

    def test_error_before_streaming_is_mapped(
        self, client: NvidiaClient, stub_sdk: _StubOpenAI
    ) -> None:
        stub_sdk.chat.completions.result = _status_error(openai.AuthenticationError, 401)

        with pytest.raises(AuthenticationError):
            client.prompt_stream(_MESSAGES)

    def test_error_mid_stream_is_mapped(self, client: NvidiaClient, stub_sdk: _StubOpenAI) -> None:
        def chunks() -> Iterator[_FakeChunk]:
            yield _FakeChunk(choices=[_FakeStreamChoice(delta=_FakeDelta(content="Hel"))])
            raise openai.OpenAIError("connection dropped")

        stub_sdk.chat.completions.result = chunks()

        stream = client.prompt_stream(_MESSAGES)
        iterator = iter(stream)
        assert next(iterator) == "Hel"
        with pytest.raises(NvidiaError):
            next(iterator)
