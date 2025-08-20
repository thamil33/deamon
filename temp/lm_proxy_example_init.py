class LMProxyChatAdapter:
    """Adapter for VS Code LM Proxy (or any OpenAI-compatible proxy endpoint).

    Implements the unified_call interface used by Agent. Streams chunks and
    invokes callbacks similar to LiteLLMChatWrapper.unified_call.
    """

    def __init__(self, provider: str, model: str, model_config: Optional[ModelConfig] = None, **kwargs: Any):
        # Default base from model_config.api_base or localhost
        self.provider = provider
        self.model = model
        self.a0_model_conf = model_config
        self.kwargs = kwargs or {}
        # api_base may be provided via kwargs['api_base'] or model_config.api_base
        api_base = self.kwargs.get("api_base") or (model_config.api_base if model_config else "")
        self.base_url = (api_base or "http://localhost:4000").rstrip("/")
        self.headers = {"Content-Type": "application/json"}

    def _convert_messages(self, messages: List[BaseMessage] | List[dict]) -> List[dict]:
        if not messages:
            return []
        if isinstance(messages[0], dict):
            # assume already openai-like
            return messages  # type: ignore
        # convert LangChain BaseMessage list
        result: List[dict] = []
        role_mapping = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}
        for m in messages:  # type: ignore
            role = role_mapping.get(getattr(m, "type", ""), getattr(m, "type", ""))
            msg = {"role": role, "content": getattr(m, "content", "")}
            # Handle tool call id if present
            tool_call_id = getattr(m, "tool_call_id", None)
            if tool_call_id:
                msg["tool_call_id"] = tool_call_id
            result.append(msg)
        return result

    async def unified_call(
        self,
        system_message: str = "",
        user_message: str = "",
        messages: List[BaseMessage] | None = None,
        response_callback: Callable[[str, str], Awaitable[None]] | None = None,
        reasoning_callback: Callable[[str, str], Awaitable[None]] | None = None,
        tokens_callback: Callable[[str, int], Awaitable[None]] | None = None,
        rate_limiter_callback: Callable[[str, str, int, int], Awaitable[bool]] | None = None,
        **kwargs: Any,
    ) -> Tuple[str, str]:

        turn_off_logging()

        # Build messages array
        msgs: List[dict] = []
        if messages:
            msgs = self._convert_messages(messages)
        if system_message:
            msgs.insert(0, {"role": "system", "content": system_message})
        if user_message:
            msgs.append({"role": "user", "content": user_message})

        # Apply rate limiting if configured
        limiter = await apply_rate_limiter(self.a0_model_conf, _json.dumps(msgs), rate_limiter_callback)

        # Prepare request
        url = f"{self.base_url}/openai/v1/chat/completions"
        payload = {"model": self.model, "messages": msgs, "stream": True}
        # merge known kwargs into payload (temperature, top_p, etc.)
        merged_kwargs = {**(self.kwargs or {}), **kwargs}
        for k, v in (merged_kwargs or {}).items():
            if k in ("api_base",):
                continue
            payload.setdefault(k, v)

        response_text = ""
        reasoning_text = ""

        # Perform streaming HTTP request
        try:
            resp = requests.post(url, headers=self.headers, json=payload, stream=True)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            # Return error as response text
            return f"[LMProxy error] {e}", reasoning_text

        # Iterate over streamed lines
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            data_str = line
            if data_str.startswith("data: "):
                data_str = data_str[len("data: ") :]
            if data_str.strip() == "[DONE]":
                break
            try:
                chunk = _json.loads(data_str)
            except _json.JSONDecodeError:
                # skip undecodable chunk
                continue

            parsed = _parse_chunk(chunk)

            if parsed["reasoning_delta"]:
                reasoning_text += parsed["reasoning_delta"]
                if reasoning_callback:
                    await reasoning_callback(parsed["reasoning_delta"], reasoning_text)
                if tokens_callback:
                    await tokens_callback(parsed["reasoning_delta"], approximate_tokens(parsed["reasoning_delta"]))
                if limiter:
                    limiter.add(output=approximate_tokens(parsed["reasoning_delta"]))

            if parsed["response_delta"]:
                response_text += parsed["response_delta"]
                if response_callback:
                    await response_callback(parsed["response_delta"], response_text)
                if tokens_callback:
                    await tokens_callback(parsed["response_delta"], approximate_tokens(parsed["response_delta"]))
                if limiter:
                    limiter.add(output=approximate_tokens(parsed["response_delta"]))

        return response_text, reasoning_text

