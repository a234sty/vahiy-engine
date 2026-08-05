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
