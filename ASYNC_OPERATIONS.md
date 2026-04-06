# Asynchronous Operations - Complete Guide

**Version:** 1.0
**Date:** 2026-04-06
**Priority:** HIGH (Phase 1.5)
**Timeline:** 2 weeks
**Status:** Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [What Async Provides (and Doesn't)](#what-async-provides-and-doesnt)
3. [Architecture Design](#architecture-design)
4. [DazScriptServer Implementation](#dazscriptserver-implementation)
5. [MCP Server Implementation](#mcp-server-implementation)
6. [Usage Patterns](#usage-patterns)
7. [Testing Strategy](#testing-strategy)
8. [Implementation Timeline](#implementation-timeline)

---

## Executive Summary

### Problem Statement

Current synchronous architecture blocks HTTP connections during long operations:
- Renders can take 30 seconds to 30+ minutes
- HTTP timeouts require very high timeout settings
- No cancellation possible once started
- No progress feedback
- LLM/user sees nothing for minutes (appears frozen)

### Solution

Implement asynchronous request pattern:
```
Client → Submit request → Immediate response with request_id
         ↓ (HTTP connection closed)
     Poll status periodically
         ↓
     Retrieve result when complete
```

### Key Findings from SDK Investigation

✅ **Render cancellation IS supported:**
- `DzRenderer::killRender()` exists (dzrenderer.h line 701)
- `bool isRendering() const` for status checks
- Signals available: `renderStarting()`, `renderFinished(bool)`

✅ **DAZ Studio is single-threaded:**
- Only serial execution possible
- Scene locks during render
- Cannot modify scene while rendering in MVP

✅ **Time estimation feasible:**
- Track render history
- Estimate based on scene complexity

### Implementation Approach

- **Request registry** in DazScriptServer (C++)
- **Queue management** with serial processing (1 operation at a time)
- **Cancellation** via `killRender()` + script flag checking
- **Progress tracking** via frame counting (animation) + time estimates
- **TTL cleanup** removes old requests after 1 hour
- **In-memory only** for MVP (no persistence)

---

## What Async Provides (and Doesn't)

### ✅ What Async DOES Provide

#### 1. HTTP Non-Blocking
**Before:**
```
Client → POST /execute (render script)
         ↓ Connection held open 10 minutes
         ← Response after render completes
```

**After:**
```
Client → POST /execute/async
         ← {"request_id": "abc123", "status": "queued"} (immediate)

Client → GET /requests/abc123/status (poll every 5 seconds)
         ← {"status": "running", "progress": 0.45}

Client → GET /requests/abc123/result
         ← {"status": "completed", "result": {...}}
```

**Benefit:** No HTTP timeout issues, connection not held open

#### 2. Cancellation
```python
request = daz_render_async("/test.png")
# Realize settings wrong after 2 minutes
daz_cancel_request(request["request_id"])
# Render stops, can try again
```

**Benefit:** Stop wasted render time

#### 3. Progress Monitoring
```python
status = daz_get_request_status("abc123")
# {"status": "running", "progress": 0.45, "elapsed_ms": 120000,
#  "message": "Rendering frame 54 of 120"}
```

**Benefit:** User knows render is progressing, not frozen

#### 4. Serial Queueing
```python
# Submit all at once
req1 = daz_render_with_camera_async("Cam1", "/r1.png")
req2 = daz_render_with_camera_async("Cam2", "/r2.png")
req3 = daz_render_with_camera_async("Cam3", "/r3.png")

# Execute serially: Cam1 → Cam2 → Cam3
# But can poll all statuses without blocking
```

**Benefit:** Batch operations more efficient

#### 5. LLM Multi-Project Work
```python
# Start render for Project A
render_a = daz_render_async("/projectA/render.png")

# LLM can now:
# - Respond to user about Project B
# - Work on code in Project C
# - Come back later to check Project A status
```

**Benefit:** LLM not blocked waiting

### ❌ What Async Does NOT Provide (MVP)

#### 1. Scene Modification During Render

**DAZ Studio is single-threaded.** While rendering:
- ❌ Cannot change lighting
- ❌ Cannot move camera
- ❌ Cannot adjust poses
- ❌ Cannot load content
- ❌ Cannot execute ANY scene operation

**Why?** Render locks the scene. DAZ Studio is busy and cannot accept modifications.

#### 2. Parallel/Concurrent Execution

**Serial execution only:**
```
Render 1 starts    → RUNNING → scene locked
Render 2 submitted → QUEUED  → waits for Render 1
Light change       → QUEUED  → waits for Render 2
Render 3 submitted → QUEUED  → waits for Light change
```

**Execution is strictly sequential.**

#### 3. Real-Time Adjustments

Cannot tweak render settings mid-execution. Must:
1. Cancel current render
2. Adjust settings
3. Start new render

### Correct Usage Examples

#### ✅ CORRECT: Sequential Scene Exploration
```python
# Render base version
render1 = daz_render_async("/base.png")
await daz_wait_for_request(render1["request_id"])  # Wait

# Modify scene (now safe)
daz_apply_lighting_preset("dramatic", "Genesis 9")

# Render variation
render2 = daz_render_async("/dramatic.png")
await daz_wait_for_request(render2["request_id"])
```

#### ❌ WRONG: Trying to Modify During Render
```python
# ❌ This will BLOCK, not work in parallel
render1 = daz_render_async("/base.png")
# This BLOCKS until render1 completes:
daz_apply_lighting_preset("dramatic", "Genesis 9")
render2 = daz_render_async("/dramatic.png")
```

### Future: iRay Server Offload (Phase 4)

**With iRay Server, render offloaded to separate server:**
```
DAZ Studio → Send job → iRay Server (different machine/process)
           ↓
      Scene unlocked!
           ↓
    Can modify immediately
```

**Enables:**
- ✅ Modify scene while render running
- ✅ True parallel rendering
- ✅ Render farm integration

**But requires:** Separate iRay Server setup, network rendering, additional API integration

---

## Architecture Design

### Request State Machine

```
User Request
     ↓
  QUEUED (in queue, waiting)
     ↓
  RUNNING (executing, scene locked)
     ↓
  {COMPLETED, FAILED, CANCELLED}
     ↓
  TTL cleanup (deleted after 1 hour)
```

### Memory Structure

```cpp
// In DzScriptServerPane
struct AsyncRequest {
    QString id;                      // "render-abc123"
    QString type;                    // "render", "execute", "animation"
    RequestStatus status;            // QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED

    // Script data
    QString script;
    QVariantMap args;

    // Results
    QVariantMap result;
    QString error;

    // Progress tracking
    double progress;                 // 0.0-1.0 or -1.0 (unknown)
    int current_frame;               // For animation
    int total_frames;                // For animation
    QString message;                 // "Rendering frame 54 of 120"

    // Timing
    qint64 submitted_at;
    qint64 started_at;
    qint64 completed_at;
    int estimated_duration_ms;       // From history

    // Cancellation
    QAtomicInt cancel_requested;     // 0=no, 1=yes

    // Thread
    QThread* execution_thread;
};

// Global registry (protected by mutex)
QMap<QString, AsyncRequest> m_asyncRequests;
QMutex m_asyncMutex;
QQueue<QString> m_asyncQueue;        // FIFO
QString m_currentRequestId;          // Currently executing
QTimer* m_cleanupTimer;              // TTL cleanup every 5 minutes
```

### API Endpoints

```
POST   /execute/async               # Execute script async, return request_id
POST   /scripts/{id}/async          # Execute registered script async
GET    /requests/{id}/status        # Get status (lightweight, non-blocking)
GET    /requests/{id}/result        # Get result (optional blocking with timeout)
DELETE /requests/{id}               # Cancel request
GET    /requests                    # List all requests (optional status filter)
```

---

## DazScriptServer Implementation

### 1. Header Changes (DzScriptServerPane.h)

Add to class definition:

```cpp
private:
    enum RequestStatus {
        REQUEST_QUEUED,
        REQUEST_RUNNING,
        REQUEST_COMPLETED,
        REQUEST_FAILED,
        REQUEST_CANCELLED
    };

    struct AsyncRequest {
        QString id;
        QString type;
        RequestStatus status;
        QString script;
        QVariantMap args;
        QVariantMap result;
        QString error;
        double progress;
        int current_frame;
        int total_frames;
        QString message;
        qint64 submitted_at;
        qint64 started_at;
        qint64 completed_at;
        int estimated_duration_ms;
        QAtomicInt cancel_requested;
        QThread* execution_thread;
    };

    // Request management
    QMap<QString, AsyncRequest> m_asyncRequests;
    QMutex m_asyncMutex;
    QQueue<QString> m_asyncQueue;
    QString m_currentRequestId;
    QTimer* m_cleanupTimer;

    // Render history for time estimation
    struct RenderHistoryEntry {
        qint64 duration_ms;
        int node_count;
        int light_count;
        QString renderer_type;
        int frame_count;
    };
    QList<RenderHistoryEntry> m_renderHistory;
    static const int MAX_HISTORY_SIZE = 100;

    // Methods
    void processNextAsyncRequest();
    void executeAsyncRequest(const QString& requestId);
    void cleanupOldRequests();
    QString generateRequestId(const QString& type);
    std::string statusToString(RequestStatus status);

    bool executeScriptWithCancellation(
        const QString& script,
        const QVariantMap& args,
        QAtomicInt* cancelFlag,
        QVariantMap& result
    );

    void recordRenderTime(
        qint64 duration_ms,
        int node_count,
        int light_count,
        const QString& renderer_type,
        int frame_count
    );

    int estimateRenderDuration(
        int node_count,
        int light_count,
        const QString& renderer_type,
        int frame_count
    );
```

### 2. Queue Management (DzScriptServerPane.cpp)

```cpp
void DzScriptServerPane::processNextAsyncRequest() {
    QMutexLocker locker(&m_asyncMutex);

    // Already running?
    if (!m_currentRequestId.isEmpty()) {
        return;
    }

    // Queue empty?
    if (m_asyncQueue.isEmpty()) {
        return;
    }

    // Dequeue next request
    QString requestId = m_asyncQueue.dequeue();
    m_currentRequestId = requestId;

    auto& request = m_asyncRequests[requestId];
    request.status = REQUEST_RUNNING;
    request.started_at = QDateTime::currentMSecsSinceEpoch();

    locker.unlock();

    // Execute in background thread
    QThread* thread = QThread::create([this, requestId]() {
        executeAsyncRequest(requestId);
    });

    {
        QMutexLocker locker2(&m_asyncMutex);
        m_asyncRequests[requestId].execution_thread = thread;
    }

    thread->start();
}

void DzScriptServerPane::executeAsyncRequest(const QString& requestId) {
    QMutexLocker locker(&m_asyncMutex);
    auto& request = m_asyncRequests[requestId];
    QString script = request.script;
    QVariantMap args = request.args;
    locker.unlock();

    try {
        QVariantMap result;
        bool success = false;

        // Execute on main thread (DAZ requirement)
        QMetaObject::invokeMethod(this, [&]() {
            success = executeScriptWithCancellation(
                script, args, &request.cancel_requested, result
            );
        }, Qt::BlockingQueuedConnection);

        // Update request with result
        locker.relock();
        if (success) {
            request.status = REQUEST_COMPLETED;
            request.result = result;
        } else {
            request.status = REQUEST_FAILED;
            request.error = result["error"].toString();
        }
        request.completed_at = QDateTime::currentMSecsSinceEpoch();
        request.progress = 1.0;

    } catch (const std::exception& e) {
        locker.relock();
        request.status = REQUEST_FAILED;
        request.error = QString("Exception: %1").arg(e.what());
        request.completed_at = QDateTime::currentMSecsSinceEpoch();
    }

    locker.unlock();

    // Clear current and process next
    {
        QMutexLocker locker2(&m_asyncMutex);
        m_currentRequestId.clear();
    }

    processNextAsyncRequest();
}
```

### 3. Cancellation Support

```cpp
bool DzScriptServerPane::executeScriptWithCancellation(
    const QString& script,
    const QVariantMap& args,
    QAtomicInt* cancelFlag,
    QVariantMap& result
) {
    // Start script execution
    bool success = executeScript(script, args, result);

    // Monitor for cancellation if render-related
    if (cancelFlag && cancelFlag->load() == 1) {
        // Attempt to cancel via DAZ API
        DzRenderMgr* renderMgr = dzApp->getRenderMgr();
        if (renderMgr && renderMgr->isRendering()) {
            DzRenderer* renderer = renderMgr->getActiveRenderer();
            if (renderer) {
                renderer->killRender();
            }
        }
        result["error"] = "Cancelled by user";
        return false;
    }

    return success;
}
```

### 4. HTTP Endpoints

```cpp
void DzScriptServerPane::setupRoutes() {
    // ... existing routes ...

    // POST /execute/async
    m_pServer->Post("/execute/async", [this](const httplib::Request& req, httplib::Response& res) {
        nlohmann::json body = nlohmann::json::parse(req.body, nullptr, false);
        if (body.is_discarded()) {
            return sendError(res, 400, "Invalid JSON");
        }

        QString script = QString::fromStdString(body["script"].get<std::string>());
        QVariantMap args = jsonToQVariantMap(body["args"]);
        QString requestId = generateRequestId("execute");

        AsyncRequest request;
        request.id = requestId;
        request.type = "execute";
        request.status = REQUEST_QUEUED;
        request.script = script;
        request.args = args;
        request.progress = 0.0;
        request.submitted_at = QDateTime::currentMSecsSinceEpoch();
        request.cancel_requested.store(0);
        request.execution_thread = nullptr;

        {
            QMutexLocker locker(&m_asyncMutex);
            m_asyncRequests[requestId] = request;
            m_asyncQueue.enqueue(requestId);
        }

        processNextAsyncRequest();

        nlohmann::json response;
        response["request_id"] = requestId.toStdString();
        response["status"] = "queued";
        response["submitted_at"] = QDateTime::currentDateTime()
            .toString(Qt::ISODate).toStdString();

        res.set_content(response.dump(), "application/json");
    });

    // GET /requests/{id}/status
    m_pServer->Get(R"(/requests/([^/]+)/status)",
        [this](const httplib::Request& req, httplib::Response& res) {
        QString requestId = QString::fromStdString(req.matches[1]);

        QMutexLocker locker(&m_asyncMutex);

        if (!m_asyncRequests.contains(requestId)) {
            return sendError(res, 404, "Request not found");
        }

        const auto& request = m_asyncRequests[requestId];

        nlohmann::json response;
        response["request_id"] = requestId.toStdString();
        response["status"] = statusToString(request.status);
        response["progress"] = request.progress;

        if (request.type == "animation") {
            response["current_frame"] = request.current_frame;
            response["total_frames"] = request.total_frames;
            response["message"] = request.message.toStdString();
        }

        if (request.status == REQUEST_RUNNING) {
            qint64 elapsed = QDateTime::currentMSecsSinceEpoch() - request.started_at;
            response["elapsed_ms"] = elapsed;

            if (request.estimated_duration_ms > 0) {
                qint64 remaining = request.estimated_duration_ms - elapsed;
                response["estimated_remaining_ms"] = std::max(0LL, remaining);
            }
        }

        res.set_content(response.dump(), "application/json");
    });

    // GET /requests/{id}/result
    m_pServer->Get(R"(/requests/([^/]+)/result)",
        [this](const httplib::Request& req, httplib::Response& res) {
        QString requestId = QString::fromStdString(req.matches[1]);
        bool wait = req.has_param("wait") && req.get_param_value("wait") == "true";
        int timeout = req.has_param("timeout") ?
            std::stoi(req.get_param_value("timeout")) : 300;

        auto startTime = QDateTime::currentMSecsSinceEpoch();

        while (wait) {
            QMutexLocker locker(&m_asyncMutex);

            if (!m_asyncRequests.contains(requestId)) {
                return sendError(res, 404, "Request not found");
            }

            const auto& request = m_asyncRequests[requestId];

            if (request.status == REQUEST_COMPLETED ||
                request.status == REQUEST_FAILED ||
                request.status == REQUEST_CANCELLED) {

                nlohmann::json response;
                response["request_id"] = requestId.toStdString();
                response["status"] = statusToString(request.status);

                if (request.status == REQUEST_COMPLETED) {
                    response["result"] = qvariantMapToJson(request.result);
                } else if (request.status == REQUEST_FAILED) {
                    response["error"] = request.error.toStdString();
                }

                response["duration_ms"] = request.completed_at - request.started_at;
                response["completed_at"] = QDateTime::fromMSecsSinceEpoch(request.completed_at)
                    .toString(Qt::ISODate).toStdString();

                res.set_content(response.dump(), "application/json");
                return;
            }

            locker.unlock();

            if (QDateTime::currentMSecsSinceEpoch() - startTime > timeout * 1000) {
                return sendError(res, 408, "Timeout waiting for result");
            }

            QThread::msleep(500);
        }

        // Non-blocking mode
        QMutexLocker locker(&m_asyncMutex);
        const auto& request = m_asyncRequests[requestId];

        nlohmann::json response;
        response["request_id"] = requestId.toStdString();
        response["status"] = statusToString(request.status);
        if (request.progress >= 0) {
            response["progress"] = request.progress;
        }

        res.set_content(response.dump(), "application/json");
    });

    // DELETE /requests/{id} - Cancel
    m_pServer->Delete(R"(/requests/([^/]+))",
        [this](const httplib::Request& req, httplib::Response& res) {
        QString requestId = QString::fromStdString(req.matches[1]);

        QMutexLocker locker(&m_asyncMutex);

        if (!m_asyncRequests.contains(requestId)) {
            return sendError(res, 404, "Request not found");
        }

        auto& request = m_asyncRequests[requestId];

        if (request.status == REQUEST_COMPLETED ||
            request.status == REQUEST_FAILED ||
            request.status == REQUEST_CANCELLED) {
            return sendError(res, 400, "Request already finished");
        }

        request.cancel_requested.store(1);

        if (request.status == REQUEST_QUEUED) {
            m_asyncQueue.removeAll(requestId);
            request.status = REQUEST_CANCELLED;
            request.completed_at = QDateTime::currentMSecsSinceEpoch();
        } else if (request.status == REQUEST_RUNNING) {
            request.status = REQUEST_CANCELLED;
        }

        nlohmann::json response;
        response["request_id"] = requestId.toStdString();
        response["status"] = "cancelled";
        response["message"] = "Cancellation requested";
        response["cancelled_at"] = QDateTime::currentDateTime()
            .toString(Qt::ISODate).toStdString();

        res.set_content(response.dump(), "application/json");
    });

    // GET /requests - List
    m_pServer->Get("/requests", [this](const httplib::Request& req, httplib::Response& res) {
        QString statusFilter;
        if (req.has_param("status")) {
            statusFilter = QString::fromStdString(req.get_param_value("status"));
        }

        QMutexLocker locker(&m_asyncMutex);

        nlohmann::json requests = nlohmann::json::array();
        int queued = 0, running = 0, completed = 0;

        for (const auto& request : m_asyncRequests) {
            if (!statusFilter.isEmpty() &&
                statusToString(request.status) != statusFilter.toStdString()) {
                continue;
            }

            nlohmann::json item;
            item["request_id"] = request.id.toStdString();
            item["type"] = request.type.toStdString();
            item["status"] = statusToString(request.status);
            item["progress"] = request.progress;
            item["submitted_at"] = QDateTime::fromMSecsSinceEpoch(request.submitted_at)
                .toString(Qt::ISODate).toStdString();

            requests.push_back(item);

            if (request.status == REQUEST_QUEUED) queued++;
            else if (request.status == REQUEST_RUNNING) running++;
            else if (request.status == REQUEST_COMPLETED) completed++;
        }

        nlohmann::json response;
        response["requests"] = requests;
        response["total"] = requests.size();
        response["queued"] = queued;
        response["running"] = running;
        response["completed"] = completed;

        res.set_content(response.dump(), "application/json");
    });
}
```

### 5. Cleanup Timer

```cpp
// In constructor
m_cleanupTimer = new QTimer(this);
connect(m_cleanupTimer, &QTimer::timeout, this, &DzScriptServerPane::cleanupOldRequests);
m_cleanupTimer->start(5 * 60 * 1000);  // Every 5 minutes

void DzScriptServerPane::cleanupOldRequests() {
    QMutexLocker locker(&m_asyncMutex);

    qint64 now = QDateTime::currentMSecsSinceEpoch();
    qint64 ttl = 60 * 60 * 1000;  // 1 hour

    QStringList toRemove;

    for (auto it = m_asyncRequests.begin(); it != m_asyncRequests.end(); ++it) {
        const auto& request = it.value();

        if (request.status == REQUEST_COMPLETED ||
            request.status == REQUEST_FAILED ||
            request.status == REQUEST_CANCELLED) {

            qint64 age = now - request.completed_at;
            if (age > ttl) {
                toRemove.append(it.key());
            }
        }
    }

    for (const QString& id : toRemove) {
        m_asyncRequests.remove(id);
    }
}
```

### 6. Helper Functions

```cpp
QString DzScriptServerPane::generateRequestId(const QString& type) {
    QString uuid = QUuid::createUuid().toString(QUuid::WithoutBraces);
    return QString("%1-%2").arg(type).arg(uuid.left(8));
}

std::string DzScriptServerPane::statusToString(RequestStatus status) {
    switch (status) {
        case REQUEST_QUEUED: return "queued";
        case REQUEST_RUNNING: return "running";
        case REQUEST_COMPLETED: return "completed";
        case REQUEST_FAILED: return "failed";
        case REQUEST_CANCELLED: return "cancelled";
        default: return "unknown";
    }
}
```

---

## MCP Server Implementation

### New Tools

```python
@mcp.tool()
async def daz_render_async(
    output_path: str | None = None,
) -> dict[str, Any]:
    """Trigger render asynchronously. Returns immediately with request ID.

    Use daz_get_request_status() to poll progress and daz_get_request_result()
    to retrieve final result when done.

    IMPORTANT: Scene is locked while rendering. Cannot modify scene until
    render completes.

    Returns:
        {"request_id": "render-abc123", "status": "queued", "submitted_at": "..."}
    """
    client = _get_client()
    args = {"outputPath": output_path} if output_path else {}

    response = await client.post("/scripts/vangard-render/async", json={"args": args})
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_get_request_status(request_id: str) -> dict[str, Any]:
    """Get status of asynchronous request (non-blocking).

    Lightweight operation that returns current status without waiting.

    Returns:
        {
            "request_id": "render-abc123",
            "status": "running",  # queued, running, completed, failed, cancelled
            "progress": 0.45,     # 0.0-1.0 or null
            "elapsed_ms": 120000,
            "estimated_remaining_ms": 147000,
            "message": "Rendering frame 54 of 120"
        }
    """
    client = _get_client()
    response = await client.get(f"/requests/{request_id}/status")
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_get_request_result(
    request_id: str,
    wait: bool = True,
    timeout_seconds: int = 300,
) -> dict[str, Any]:
    """Get result of asynchronous request.

    Args:
        request_id: Request ID from async operation
        wait: If True, blocks until complete (up to timeout)
        timeout_seconds: Max wait time if wait=True (default 300s)

    Returns:
        {
            "request_id": "render-abc123",
            "status": "completed",
            "result": {...},
            "duration_ms": 267000,
            "completed_at": "..."
        }
    """
    client = _get_client()
    params = {"wait": str(wait).lower(), "timeout": timeout_seconds}
    response = await client.get(f"/requests/{request_id}/result", params=params)
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_cancel_request(request_id: str) -> dict[str, Any]:
    """Cancel a running or queued request.

    For render operations, cancellation may take a few seconds to take effect.
    For queued operations, cancellation is immediate.

    Returns:
        {"request_id": "...", "status": "cancelled", "cancelled_at": "..."}
    """
    client = _get_client()
    response = await client.delete(f"/requests/{request_id}")
    _check_response(response)
    return response.json()


@mcp.tool()
async def daz_list_requests(
    status_filter: str | None = None
) -> dict[str, Any]:
    """List all active and recent requests.

    Args:
        status_filter: Optional filter ("queued", "running", "completed", "failed", "cancelled")

    Returns:
        {
            "requests": [...],
            "total": 5,
            "queued": 2,
            "running": 1,
            "completed": 2
        }
    """
    client = _get_client()
    params = {"status": status_filter} if status_filter else {}
    response = await client.get("/requests", params=params)
    _check_response(response)
    return response.json()


# Helper function (not a tool)
async def daz_wait_for_request(
    request_id: str,
    poll_interval: int = 5,
    timeout_seconds: int = 3600,
    progress_callback = None
) -> dict[str, Any]:
    """Wait for request to complete with progress updates.

    Polls status every poll_interval seconds.
    """
    start_time = time.time()

    while True:
        status = await daz_get_request_status(request_id)

        if progress_callback:
            progress_callback(status)

        if status["status"] in ["completed", "failed", "cancelled"]:
            if status["status"] == "failed":
                raise ToolError(f"Request failed: {status.get('error', 'Unknown')}")
            if status["status"] == "cancelled":
                raise ToolError("Request was cancelled")

            return await daz_get_request_result(request_id, wait=False)

        if time.time() - start_time > timeout_seconds:
            raise TimeoutError(f"Request timed out after {timeout_seconds}s")

        await asyncio.sleep(poll_interval)


@mcp.tool()
async def daz_set_render_quality(preset: str) -> dict[str, Any]:
    """Set render quality preset for fast vs high-quality rendering.

    Presets:
        draft: Very fast (30s-2min), low quality, for quick checks
        preview: Fast (2-5min), moderate quality, for composition review
        good: Slow (10-20min), good quality, for client review
        final: Very slow (30min-2hr), highest quality, for final output

    Adjusts: max samples, render quality, convergence ratio
    """
    presets = {
        "draft": {"Max Samples": 100, "Render Quality": 0.5},
        "preview": {"Max Samples": 500, "Render Quality": 0.75},
        "good": {"Max Samples": 2000, "Render Quality": 0.9},
        "final": {"Max Samples": 5000, "Render Quality": 1.0}
    }

    if preset not in presets:
        raise ToolError(f"Unknown preset: {preset}")

    settings = presets[preset]
    for prop_name, value in settings.items():
        await daz_set_property("Render Settings", prop_name, value)

    return {"preset": preset, "settings": settings}
```

---

## Usage Patterns

### Pattern 1: Test Render Workflow

```python
# Set draft quality for fast test
daz_set_render_quality("draft")
daz_render("/test.png")  # Synchronous, ~30 seconds

# Review and adjust
daz_set_property("Key Light", "Flux", 2500)

# Final high-quality async render
daz_set_render_quality("final")
request = daz_render_async("/final.png")

# Monitor progress
while True:
    status = await daz_get_request_status(request["request_id"])
    if status["status"] == "completed":
        break
    print(f"Progress: {status.get('progress', 0)*100:.1f}%")
    await asyncio.sleep(5)

result = await daz_get_request_result(request["request_id"])
```

### Pattern 2: Multi-Camera Batch (Sequential)

```python
# Queue all camera renders
cameras = ["Cam_0", "Cam_45", "Cam_90", "Cam_135",
           "Cam_180", "Cam_225", "Cam_270", "Cam_315"]
request_ids = []

for cam in cameras:
    req = daz_render_with_camera_async(cam, f"/renders/{cam}.png")
    request_ids.append(req["request_id"])
    print(f"Queued: {cam}")

# Monitor all (execute serially)
for req_id in request_ids:
    await daz_wait_for_request(req_id)
    print(f"Completed: {req_id}")
```

### Pattern 3: Cancellable Render

```python
# Start render
request = daz_render_async("/test.png")

# Check progress after 30 seconds
await asyncio.sleep(30)
status = await daz_get_request_status(request["request_id"])

# If too slow, cancel and use draft mode
if status.get("progress", 0) < 0.1:  # Less than 10% in 30s
    print("Too slow, cancelling...")
    await daz_cancel_request(request["request_id"])

    # Switch to draft
    daz_set_render_quality("draft")
    daz_render("/test_draft.png")  # Synchronous, fast
```

---

## Testing Strategy

### Unit Tests (C++)

1. Request lifecycle (create, queue, run, complete)
2. Cancellation (queued vs running)
3. TTL cleanup
4. Queue ordering (FIFO)

### Integration Tests (Python)

```python
async def test_async_render():
    request = await daz_render_async("/test.png")
    assert request["status"] == "queued"

    result = await daz_wait_for_request(request["request_id"])
    assert result["status"] == "completed"

async def test_cancel():
    request = await daz_render_async("/test.png")
    await asyncio.sleep(1)

    cancel_result = await daz_cancel_request(request["request_id"])
    assert cancel_result["status"] == "cancelled"

async def test_batch():
    batch = await daz_batch_render_cameras_async(
        cameras=["Cam1", "Cam2", "Cam3"],
        output_dir="/renders"
    )
    assert len(batch["request_ids"]) == 3
```

---

## Implementation Timeline

### Week 1: DazScriptServer Plugin

**Day 1-2:** Request registry & queue
- Add AsyncRequest struct
- Implement queue management
- Request ID generation

**Day 3-4:** HTTP endpoints
- POST /execute/async
- GET /requests/{id}/status
- GET /requests/{id}/result
- DELETE /requests/{id}
- GET /requests

**Day 5:** Cancellation
- Flag checking
- `killRender()` integration
- Animation frame-by-frame cancel

**Day 6-7:** Time estimation & cleanup
- Render history tracking
- Duration estimation
- TTL cleanup timer

### Week 2: MCP Server Tools

**Day 1-2:** Async tools
- daz_render_async
- daz_render_with_camera_async
- daz_batch_render_cameras_async
- daz_render_animation_async

**Day 3:** Status/result tools
- daz_get_request_status
- daz_get_request_result
- daz_cancel_request
- daz_list_requests

**Day 4:** Helpers
- daz_wait_for_request
- daz_wait_for_batch
- daz_set_render_quality

**Day 5:** Documentation
- Update CLAUDE.md
- Usage examples
- API documentation

**Day 6-7:** Testing
- Integration tests
- Cancellation scenarios
- Performance testing

---

## Success Criteria

- ✅ Can queue async render and poll status
- ✅ Can cancel render mid-execution
- ✅ Animation reports frame progress
- ✅ Time estimation within 30% after 10 renders
- ✅ TTL cleanup prevents memory leaks
- ✅ Batch render completes all cameras
- ✅ No crashes or deadlocks

---

## Known Limitations

1. **Serial execution only** - One operation at a time (DAZ constraint)
2. **No persistence** - Requests lost on restart (MVP)
3. **No single-frame progress** - Only start/complete
4. **Animation frame-level cancel** - Cannot cancel mid-frame
5. **Memory usage** - All state in memory (mitigated by TTL)

---

## Future Enhancements

1. **iRay Server** - Parallel rendering, scene modification during render
2. **Persistent state** - Survive DAZ Studio restarts
3. **Priority queue** - High-priority operations jump queue
4. **Render caching** - Skip unchanged scenes
5. **Distributed rendering** - Multiple DAZ instances

---

*End of Document*
