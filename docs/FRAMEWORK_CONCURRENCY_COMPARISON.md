# Framework Concurrency Models Comparison

## Overview

This document compares how different web frameworks handle blocking operations, synchronous queries, and concurrency. Understanding these patterns helps when choosing frameworks and designing systems.

---

## Synchronous Frameworks (Blocking by Default)

### Django
- **Model**: Synchronous by default
- **Concurrency**: Uses threads/processes (via WSGI servers like Gunicorn with workers)
- **Database**: Synchronous queries (unless using async views/ORM in Django 3.1+)
- **Blocking Behavior**: Each request blocks until complete
- **Pattern**: Run with multiple workers (`gunicorn app:app --workers 4`)
- **Notes**: Has async support (Django 3.1+), but most codebase is still synchronous

### Flask
- **Model**: Synchronous by default
- **Concurrency**: Uses threads/processes (via Gunicorn/uWSGI with workers)
- **Database**: All database queries are synchronous
- **Blocking Behavior**: Each request blocks until complete
- **Pattern**: Run with multiple workers (`gunicorn app:app --workers 4`)
- **Notes**: No built-in async support (though Quart is an async Flask alternative)

### Ruby on Rails
- **Model**: Synchronous by default
- **Concurrency**: Uses threads/processes (via Puma/Unicorn with workers)
- **Database**: Synchronous queries
- **Blocking Behavior**: Each request blocks until complete
- **Pattern**: Run with multiple workers

---

## Async-Capable Frameworks

### FastAPI
- **Model**: Async-capable, but can mix sync and async
- **Concurrency**: Single event loop (unless using workers)
- **Database**: Can use sync SQLAlchemy (blocks) OR async SQLAlchemy (non-blocking)
- **Blocking Behavior**: 
  - If you use sync SQLAlchemy + sync OpenAI client → blocks event loop
  - If you use async SQLAlchemy + async OpenAI → truly concurrent
- **Common Issue**: Declare `async def` but use blocking operations inside → blocks everything
- **Pattern**: 
  - Use async libraries throughout, OR
  - Run with workers (`uvicorn app:app --workers 4`)

### Node.js/Express
- **Model**: Async by default (event loop)
- **Concurrency**: Single event loop handles all requests
- **Database**: Libraries are async (`pg`, `mysql2`, etc.)
- **HTTP Clients**: Async (`axios`, `fetch`)
- **Blocking Behavior**: Blocking operations (like `fs.readFileSync`) block the entire event loop
- **Pattern**: Use async libraries throughout, avoid blocking operations

### Go (Gin, Echo, etc.)
- **Model**: Goroutines handle concurrency
- **Concurrency**: Each request can spawn a goroutine
- **Database**: Drivers are typically synchronous per goroutine, but goroutines don't block each other
- **Blocking Behavior**: Very concurrent by design - goroutines don't block each other
- **Pattern**: Natural concurrency - no special configuration needed

---

## The Core Issue

The problem isn't unique to FastAPI. It's about **mixing sync and async**:

### 1. If Your Framework is Async-Capable (FastAPI, Node.js)
- Using sync operations inside async functions **blocks the event loop**
- Other requests **wait**
- **Solution**: Use async libraries throughout

### 2. If Your Framework is Synchronous (Django, Flask)
- Each request blocks by design
- Concurrency comes from **multiple worker processes/threads**
- **Solution**: Use workers (Gunicorn with 4+ workers)

---

## Real-World Patterns

### Django/Flask Approach
```bash
# Run with multiple workers
gunicorn app:app --workers 4  # 4 separate processes
# Each process handles requests independently
# Blocking is fine because each worker is separate
```

**Characteristics:**
- Each worker is a separate process
- Blocking operations only affect that worker
- More memory usage (each worker loads full app)
- Simple mental model

### FastAPI/Node.js Approach
```python
# Single process with async event loop
# Blocking operations block ALL requests
# Must use async libraries throughout
```

**Characteristics:**
- Single process with event loop
- Blocking operations affect all requests
- Less memory usage (single process)
- Requires discipline to use async libraries

### Go Approach
```go
// Each request gets a goroutine
// Goroutines don't block each other
// Can use sync operations per goroutine
```

**Characteristics:**
- Goroutines are lightweight
- Natural concurrency
- Can use synchronous operations per goroutine
- Very efficient

---

## Why FastAPI Can Be Tricky

FastAPI supports **both sync and async**, which makes it easy to:
- Write `async def` endpoints ✅
- Use sync SQLAlchemy inside → **blocks everything** ❌
- Use sync OpenAI client → **blocks everything** ❌

**The Problem:**
```python
@router.post("/generate")
async def generate():  # Looks async...
    user = db.query(User).first()  # But this is blocking!
    response = openai_client.chat.completions.create(...)  # This too!
    # Blocks entire event loop - other requests wait
```

**The Solution:**
```python
@router.post("/generate")
async def generate():
    user = await db.execute(select(User))  # Truly async
    response = await async_openai_client.chat.completions.create(...)  # Truly async
    # Doesn't block - other requests process concurrently
```

Django/Flask are simpler in this sense: they're synchronous, so you just use workers for concurrency.

---

## Comparison Table

| Framework | Default Model | Concurrency Method | Blocking Behavior | Solution |
|-----------|--------------|-------------------|-------------------|----------|
| **Django** | Sync | Workers (processes) | Each request blocks | Use workers |
| **Flask** | Sync | Workers (processes) | Each request blocks | Use workers |
| **FastAPI** | Async-capable | Event loop OR workers | Sync ops block all | Use async libs OR workers |
| **Node.js** | Async | Event loop | Blocking ops block all | Use async libs |
| **Go** | Goroutines | Goroutines | Natural concurrency | No special config |

---

## Bottom Line

- **Django/Flask**: Synchronous by default → use workers for concurrency
- **FastAPI**: Async-capable → use async libraries OR workers
- **Node.js**: Async by default → use async libraries
- **Go**: Goroutines → natural concurrency, no special config needed

The blocking issue you're seeing is **common in async frameworks** when mixing sync operations. In Django/Flask, you'd typically use workers instead of async, which avoids this problem but uses more memory.

---

## Recommendations for SpendSense

**Current Situation:**
- FastAPI with sync SQLAlchemy + sync OpenAI client
- Blocking operations block the event loop
- Other requests wait during recommendation generation

**Options:**
1. **Quick Fix**: Use FastAPI BackgroundTasks + Redis status tracking
2. **Better Fix**: Migrate to async SQLAlchemy + async OpenAI client
3. **Production Fix**: Use task queue (Celery) with Redis
4. **Alternative**: Run with workers (`uvicorn --workers 4`) - simpler but uses more memory

**Current Implementation**: Option 4 (uvicorn workers) - ✅ Implemented
- Running with `--workers 4` for concurrent request handling
- No code changes required
- Compatible with future improvements (async, BackgroundTasks, task queue)