# Production-Grade Request Logging System

This document describes the comprehensive request logging system implemented for the Movie Recommender API. The system provides detailed logging of all HTTP requests to the database for monitoring, analytics, and debugging purposes.

## Overview

The request logging system consists of several components:

1. **Database Model** (`RequestLog`) - Stores request/response data
2. **Middleware** (`RequestLoggingMiddleware`) - Captures and logs requests
3. **CRUD Operations** (`CRUDRequestLog`) - Database operations for logs
4. **API Endpoints** - Query and manage logged data
5. **Pydantic Schemas** - Data validation and serialization

## Features

### 🚀 Production-Ready Features

- **Asynchronous Logging**: Fire-and-forget logging that doesn't block requests
- **Performance Metrics**: Tracks request processing time and response sizes
- **Error Tracking**: Captures and categorizes HTTP errors
- **Security**: Filters sensitive headers (authorization, cookies, etc.)
- **Configurable**: Exclude health checks, customize sensitive headers
- **Database Optimization**: Proper indexing for fast queries
- **Cleanup Utilities**: Prevent database bloat with old log cleanup

### 📊 Monitoring Capabilities

- **Real-time Request Monitoring**: View recent requests and errors
- **Endpoint Analytics**: Performance stats grouped by endpoint
- **Traffic Patterns**: Hourly traffic analysis
- **Error Rate Tracking**: Monitor API health and error trends
- **Client IP Tracking**: Handle proxy headers correctly

## Database Schema

The `request_logs` table captures:

```sql
CREATE TABLE request_logs (
    id SERIAL PRIMARY KEY,
    method VARCHAR NOT NULL,           -- HTTP method (GET, POST, etc.)
    path VARCHAR(512) NOT NULL,        -- Request path
    query_params JSONB,                -- Query parameters
    client_ip INET,                    -- Client IP (proxy-aware)
    user_agent TEXT,                   -- User agent string
    referer VARCHAR(512),              -- Referer header
    headers JSONB,                     -- Filtered request headers
    status_code INTEGER NOT NULL,      -- HTTP status code
    response_size INTEGER,             -- Response size in bytes
    processing_time FLOAT,             -- Request processing time in seconds
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(64),               -- Optional user identification
    session_id VARCHAR(128),           -- Optional session tracking
    request_size INTEGER,              -- Request body size in bytes
    error_message TEXT                 -- Error details if applicable
);
```

### Indexes

The following indexes are created for optimal query performance:

- `ix_request_logs_timestamp` - For time-based queries
- `ix_request_logs_path` - For endpoint-specific queries
- `ix_request_logs_method` - For HTTP method filtering
- `ix_request_logs_status_code` - For error analysis
- `ix_request_logs_client_ip` - For client analysis
- `ix_request_logs_user_id` - For user-specific queries
- `ix_request_logs_session_id` - For session tracking

## Configuration

### Middleware Configuration

```python
from app.middleware import RequestLoggingMiddleware

app.add_middleware(
    RequestLoggingMiddleware,
    log_health_checks=False,        # Skip /health, /metrics endpoints
    enable_async_logging=True,      # Use fire-and-forget logging
    excluded_paths={                # Additional paths to exclude
        "/docs", "/redoc", "/openapi.json"
    },
    sensitive_headers={             # Headers to filter out
        "authorization", "cookie", "x-api-key"
    }
)
```

### Environment Variables

No additional environment variables are required. The system uses the existing database configuration.

## API Endpoints

All endpoints are available under `/v1/logs/`:

### GET `/v1/logs/recent`
Get recent request logs.

**Parameters:**
- `limit` (int, max 1000): Number of logs to return (default: 100)
- `hours_back` (int, max 168): Hours to look back (default: 24)

**Example:**
```bash
curl "http://localhost:8000/v1/logs/recent?limit=50&hours_back=12"
```

### GET `/v1/logs/errors`
Get recent error logs (status codes >= 400).

**Parameters:**
- `limit` (int, max 1000): Number of error logs to return (default: 100)
- `hours_back` (int, max 168): Hours to look back (default: 24)

**Example:**
```bash
curl "http://localhost:8000/v1/logs/errors?hours_back=6"
```

### GET `/v1/logs/stats/endpoints`
Get request statistics grouped by endpoint.

**Parameters:**
- `hours_back` (int, max 168): Hours to look back (default: 24)

**Response includes:**
- Request count per endpoint
- Average and maximum processing time
- Error count and error rate percentage

**Example:**
```bash
curl "http://localhost:8000/v1/logs/stats/endpoints"
```

### GET `/v1/logs/stats/traffic`
Get traffic statistics grouped by hour.

**Parameters:**
- `hours_back` (int, max 168): Hours to look back (default: 24)

**Example:**
```bash
curl "http://localhost:8000/v1/logs/stats/traffic?hours_back=48"
```

### DELETE `/v1/logs/cleanup`
Clean up old request logs.

**Parameters:**
- `days_to_keep` (int, 1-365): Number of days of logs to keep (default: 30)

**Example:**
```bash
curl -X DELETE "http://localhost:8000/v1/logs/cleanup?days_to_keep=7"
```

## Usage Examples

### Monitoring API Health

```python
import httpx

# Check recent errors
response = httpx.get("http://localhost:8000/v1/logs/errors?hours_back=1")
recent_errors = response.json()

if len(recent_errors) > 10:
    print("⚠️  High error rate detected!")
    
# Check endpoint performance
response = httpx.get("http://localhost:8000/v1/logs/stats/endpoints")
stats = response.json()

slow_endpoints = [
    endpoint for endpoint in stats 
    if endpoint['avg_processing_time'] and endpoint['avg_processing_time'] > 1.0
]

if slow_endpoints:
    print("🐌 Slow endpoints detected:", slow_endpoints)
```

### Setting Up Automated Cleanup

Create a cron job or scheduled task to clean up old logs:

```bash
# Clean up logs older than 30 days, run daily at 2 AM
0 2 * * * curl -X DELETE "http://localhost:8000/v1/logs/cleanup?days_to_keep=30"
```

### Dashboard Integration

The API endpoints can be easily integrated with monitoring dashboards:

```javascript
// Fetch traffic data for charts
async function getTrafficData() {
    const response = await fetch('/v1/logs/stats/traffic?hours_back=24');
    const data = await response.json();
    
    return data.map(item => ({
        time: new Date(item.hour),
        requests: item.request_count,
        errors: item.error_count
    }));
}
```

## Performance Considerations

### Asynchronous Logging
The middleware uses fire-and-forget async logging by default, which means:
- ✅ No impact on request response times
- ✅ High throughput capability
- ⚠️ Potential for log loss if the application crashes immediately after a request

### Database Impact
- Indexes are optimized for common query patterns
- Regular cleanup prevents table bloat
- Consider partitioning for very high-traffic applications

### Memory Usage
- Headers and query parameters are stored as JSONB
- Large request/response bodies are not logged by default
- Configurable size limits prevent memory issues

## Security Considerations

### Sensitive Data Filtering
The middleware automatically filters sensitive headers:
- `authorization`
- `cookie`
- `x-api-key`
- `x-auth-token`
- `proxy-authorization`

### IP Address Handling
- Correctly handles proxy headers (`X-Forwarded-For`, `X-Real-IP`)
- Stores client IP for rate limiting and abuse detection
- Uses PostgreSQL INET type for efficient IP storage

### Data Retention
- Implement appropriate data retention policies
- Consider GDPR/privacy requirements for IP addresses
- Use the cleanup endpoint to manage data lifecycle

## Troubleshooting

### Common Issues

1. **High Database Load**
   - Increase cleanup frequency
   - Reduce retention period
   - Consider excluding more endpoints

2. **Missing Logs**
   - Check if async logging is enabled
   - Verify database connectivity
   - Check application logs for errors

3. **Slow Queries**
   - Ensure indexes are created (run migration)
   - Consider adding composite indexes for specific query patterns
   - Use query parameters to limit result sets

### Monitoring the Logger

```python
import logging

# Enable debug logging for the middleware
logging.getLogger("app.middleware.request_logging").setLevel(logging.DEBUG)
```

## Migration

The request logging system was added via Alembic migration:

```bash
# Apply the migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

## Future Enhancements

Potential improvements for the logging system:

1. **Sampling**: Log only a percentage of requests for high-traffic scenarios
2. **Structured Logging**: Integration with structured logging systems
3. **Real-time Alerts**: Webhook notifications for error thresholds
4. **Geographic Analysis**: IP geolocation for traffic analysis
5. **Request Body Logging**: Optional logging of request/response bodies
6. **Metrics Export**: Prometheus/Grafana integration

## Conclusion

This production-grade request logging system provides comprehensive monitoring capabilities while maintaining high performance and security standards. It's designed to scale with your application and provide valuable insights into API usage patterns and performance characteristics.
