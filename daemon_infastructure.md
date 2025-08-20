# Daemon Architecture — High‑Level Blueprint

A concise blueprint to build a long‑running daemon architecture from scratch with no framework assumptions.

## Checklist
- Define purpose and constraints
- Specify core components and data contracts
- Outline execution lifecycle and control flow
- Plan memory, tools, and safety boundaries
- Cover observability, testing, and deployment
- Note failure modes and extensibility

## Purpose & Constraints
- Goal: long‑running, autonomous background agent that accepts tasks, uses tools, maintains memory, and produces artifacts.
- Constraints: minimal external dependencies, deterministic contracts, safe by default, observable, easy to extend.

## Core Principles
- Single source of truth for state; everything else is a projection (views, logs, caches).
- Small, composable services; explicit data contracts; predictable side effects.
- Log everything that matters; make flows testable and replayable.
- Start simple; evolve via migrations and versioned interfaces.

## Minimal v1 Architecture
- Orchestrator: event loop that accepts tasks, plans tool calls, executes steps, and emits results.
- Tooling layer: bounded, permissioned functions (filesystem, web fetch, search, code run, parsers, notifications).
- Model interface: pluggable LLM/embedding providers behind stable APIs.
- Memory:
    - KV store for facts/settings
    - Vector store for semantic recall
    - Journal/store for artifacts (files)
    - Periodic consolidation jobs
- Scheduler/Queue: FIFO for tasks; delayed jobs for retries and consolidation.
- Configuration/Secrets: typed config, env‑based secrets, runtime override.
- Observability: structured logs, metrics, traces, HTML/JSON session logs.
- API/UI: minimal REST/WebSocket for sending tasks and streaming progress; simple web UI optional.

## Data Contracts (stable)
- Task envelope:
    - `id`, `created_at`, `type`, `goal`, `inputs`, `attachments`, `context_hints`, `priority`
- Tool call:
    - `name`, `args` (JSON), `timeout_ms`, `allow_network`, `allow_fs`, `expected_output_schema`
- Tool result:
    - `ok`, `data`, `error`, `started_at`, `finished_at`, `logs`
- Memory record:
    - `id`, `area` (main|fragments|solutions|instruments), `text`, `metadata`, `created_at`, `embeddings[]`
- Run report:
    - `task_id`, `summary`, `artifacts[]`, `decisions[]`, `next_steps[]`, `telemetry`

## Execution Lifecycle
1. Intake: validate task, resolve attachments, seed context.
2. Retrieve: pull relevant memory (tags + semantic search).
3. Plan: produce a light plan (steps, tools, stop conditions).
4. Act: execute tools with guardrails; stream partials; store artifacts.
5. Reflect: summarize changes; write short memories; tag artifacts.
6. Consolidate (async): merge short notes → durable summaries; update embeddings; prune noise.
7. Notify: emit final response and optional follow‑ups.

## Tools (v1 set)
- Files: `read_text`, `write_text`, `list_dir`, `read_bin` (with allow‑list root)
- Web: `http_get` (safe headers, size limits)
- Search: local full‑text; vector similarity over memory
- Code: `run_sandboxed` (timeouts, resource limits, no network by default)
- Parse: `markdown_to_text`, `pdf_to_text` (via temp files), `html_to_text`
- Notify: `user_notification(text, severity)`
- All tools: JSON args, strict input validation, clear output schema, timeouts, logging.

## Memory Design
- Areas:
    - `main`: short canonical profile/context facts
    - `fragments`: scratch notes and snippets
    - `solutions`: plans, decisions, summaries
    - `instruments`: tool run summaries and benchmarks
- Stores:
    - KV: small YAML/JSON files for identity and settings
    - Vector: FAISS/SQLite‑ANN + `embeddings.json` index
    - Artifacts: files in structured folders with `metadata.json`
- Consolidation job:
    - Trigger by thresholds (count or size) or time window
    - Merge related fragments → solutions; update tags; re‑embed
    - Enforce budgets (max files, max bytes) and prune strategy

## Safety Boundaries
- Sandboxes: tool execution uses allow‑listed roots; code runner uses temp working dir.
- Permissions: tool flags (`allow_fs`, `allow_net`); deny by default.
- Rate limits: per tool and per provider.
- Redaction: strip secrets from logs; use secret placeholders in outputs.
- Policy checks: pre‑flight validators for dangerous args (e.g., `rm -rf`, unbounded fetch).

## Observability
- Structured logs (JSON) with `trace_id`/`run_id`/`tool_step_id`.
- Session transcript HTML for human review (tool call previews + diffs).
- Metrics: task latency, tool success rate, token usage, memory growth, consolidation duration.
- Debug mode: record inputs/outputs for deterministic replay.

## Testing
- Unit: tool arg validation, path resolution, parser edge cases.
- Contract: JSON schemas for task, tool I/O, memory records; validate in CI.
- Integration: golden tests for end‑to‑end small tasks with fixed seeds.
- Fuzz: randomized tool args within bounds; ensure safe failures.
- Replay: load a session log and re‑execute without side effects.

## Deployment
- Local: single process with asyncio; config via `.env`.
- Container: Dockerfile, non‑root user, volume mount for workspace/memory.
- Production: process manager or Kubernetes; persistent volume for memory; metrics exporter.
- Secrets: mounted files or secret manager; never bake secrets into images.

## Failure Modes & Resilience
- Timeouts: per tool and overall task; cancel and summarize partial results.
- Retries: idempotent tools only; exponential backoff; max attempts.
- Backpressure: queue length threshold → shed/slow low‑priority tasks.
- Corruption: validate memory indexes; rebuild on checksum mismatch.
- Partial outputs: always produce a summary even on failure.

## Extensibility
- Plugin system: register tool with `name`, `schema`, `handler`; auto‑docs.
- Providers: LLM/embedding adapters with same interface and test harness.
- Policies: hookable validators; allow project‑specific rules.
- Migrations: versioned memory schema; safe upgrades.

## Minimal Implementation Plan (from zero)
Day 1
- Scaffolding: repository, config loader, JSON schemas, logging.
- Basic tools: `read_text`, `write_text`, `http_get`, `list_dir`.
- Orchestrator: CLI task runner with plan/act/report loop.
- Memory: folders + `embeddings.json` + FAISS index.

Day 2
- Add vector search, consolidation job, and tags.
- Add code runner sandbox with strict timeouts; artifact writer.
- Add provider adapters (chat, embed) behind interfaces.

Day 3
- API: `POST /tasks`, `GET /runs/{id}`, SSE for logs.
- Observability: metrics, HTML log renderer.
- Tests: unit for tools, contract validation, 2 E2E tasks.

Day 4+
- Policies/permissions, retries/backpressure, plugin loader.
- UI: lightweight web panel for runs and files.
- Hardening: resource limits, rate limiting, memory pruning.

## Practical Conventions
- Paths: one workspace root; all paths relative to it.
- Contracts first: write JSON schemas before code.
- Determinism: seed model sampling for tests where possible.
- Docs: README for ops, CONTRIBUTING for plugins, ADRs for key decisions.

This blueprint provides a clear, minimal map to build a safe, observable, and extensible daemon with predictable behavior and room to grow.