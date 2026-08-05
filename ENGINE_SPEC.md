# Vahiy Engine Specification

Version: 1.0

---

# Overview

Vahiy Engine is the backend service that powers the Vahiy AI application.

It is responsible for:

- Reading Ahit Corpus.
- Searching religious texts.
- Preparing AI context.
- Communicating with Large Language Models.
- Returning structured, source-based responses.

The engine itself contains no religious opinions.

It only retrieves information from the corpus and prepares it for AI.

---

# Design Principles

The engine must always follow these principles.

## 1. Source First

Never answer from memory if the corpus contains the answer.

The corpus is always the primary source.

---

## 2. Transparency

Every AI answer should include the sources used whenever possible.

---

## 3. Neutrality

The engine must never favor any religion, denomination, sect, ideology or theological position.

---

## 4. Deterministic Retrieval

Searching the corpus should always produce reproducible results.

---

## 5. Separation of Responsibilities

Ahit Corpus stores data.

Vahiy Engine searches and prepares data.

The AI interprets the retrieved context.

The application only displays the result.
---

# Project Architecture

Vahiy Engine is designed as an independent backend service.

It communicates with:

- Ahit Corpus
- OpenAI API (or another supported LLM provider)
- The Vahiy AI application
- Authentication service (future)
- Database (future)

Architecture:

Vahiy AI App
        │
        ▼
   Vahiy Engine
        │
   ┌────┴────┐
   ▼         ▼
Ahit Corpus  OpenAI API
---

# Responsibilities

The Vahiy Engine has one responsibility:

Transform a user's question into a reliable, source-based answer.

To accomplish this, every request follows the same pipeline.

Pipeline:

1. Receive the user's request.

2. Analyze the request.

3. Search Ahit Corpus.

4. Retrieve every relevant source.

5. Build an AI context.

6. Send the context to the configured Large Language Model.

7. Receive the generated answer.

8. Attach the supporting sources.

9. Return the final response to the application.

The engine must never generate theological opinions by itself.

Its responsibility is retrieval, context building, and orchestration.

Reasoning is delegated to the AI model using the retrieved corpus.
---

# Public API

Version: v1

The first version of Vahiy Engine exposes only a minimal public API.

The API must remain simple, stable, and well documented.

---

## GET /verse

Returns a single verse.

Parameters:

- osis

Example:

GET /verse?osis=John.3.16

---

## GET /search

Searches Ahit Corpus.

Parameters:

- query

Example:

GET /search?query=logos

---

## POST /chat

Accepts a natural language question.

Request:

{
    "message": "What does Logos mean in John 1:1?"
}

Response:

{
    "answer": "...",
    "sources": [
        "John.1.1",
        "Strong:G3056"
    ]
}

---

Every endpoint must return JSON.

Every endpoint must support UTF-8.

Every error response must also return JSON.
