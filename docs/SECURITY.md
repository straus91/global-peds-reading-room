# Security Practices Guide

This document outlines the security practices and features implemented in the Global Peds Reading Room application to protect user data, prevent vulnerabilities, and ensure safe integration with external services like Google Gemini.

## 1. Input Validation and Sanitization

### 1.1 LLM Input Protection

All inputs to the Large Language Model (LLM) are sanitized to prevent prompt injection attacks:

- Text sanitization is performed using regex pattern matching to detect and remove potentially malicious instructions.
- Input length limits are enforced to prevent excessive token usage and potential DoS attacks.
- Type checking is performed to ensure all inputs are of the expected data types.

```python
# Example from llm_feedback_service.py
def sanitize_text(text):
    """Sanitize input text to prevent prompt injection and other issues."""
    if not isinstance(text, str):
        return "" if text is None else str(text)
    
    # Remove potential prompt injection patterns
    sanitized = PROMPT_INJECTION_PATTERN.sub('', text)
    
    # Limit extremely long inputs
    if len(sanitized) > 10000:
        sanitized = sanitized[:10000] + "... [content truncated due to length]"
        
    return sanitized
```

### 1.2 API Endpoint Validation

- All API endpoints perform input validation before processing data.
- Django's form validation and serializer validation are used to enforce data integrity.
- Explicit type checking is used for critical operations.

## 2. Rate Limiting and Resource Protection

### 2.1 LLM API Rate Limiting

The application implements a rate limiting mechanism for LLM API calls:

```python
def check_rate_limit():
    """Check if we're within API rate limits."""
    global API_CALL_HISTORY
    current_time = time.time()
    
    # Remove timestamps older than 60 seconds
    API_CALL_HISTORY = [t for t in API_CALL_HISTORY if current_time - t < 60]
    
    # If we have capacity, return True
    if len(API_CALL_HISTORY) < MAX_CALLS_PER_MINUTE:
        API_CALL_HISTORY.append(current_time)
        return True
    
    # Otherwise, we've hit the rate limit
    return False
```

- Default limit: 10 calls per minute (configurable in settings)
- Rate-limited operations fail gracefully with user-friendly error messages
- Includes random jitter for retry mechanisms to prevent synchronized retries

### 2.2 Resource Optimization

- LRU caching for the Gemini model instance to reduce API initialization overhead
- Identical section detection to minimize token usage and reduce costs
- Timeout settings for external API calls to prevent hanging requests

## 3. Error Handling and Recovery

### 3.1 Exception Management

All external API calls and database operations are wrapped in try/except blocks with:

- Specific error handling for different exception types
- User-friendly error messages that don't expose internal details
- Detailed logging for debugging and monitoring
- Graceful fallbacks when services are unavailable

### 3.2 Transaction Safety

Critical operations that involve multiple database changes use Django's transaction management:

```python
@transaction.atomic
def post(self, request, report_id, format=None):
    # Add transaction savepoint for rollback if needed
    sid = transaction.savepoint()
    
    try:
        # ... operation logic ...
        
        # Commit the transaction on success
        transaction.savepoint_commit(sid)
        return Response(...)
        
    except Exception as e:
        # Roll back the transaction on failure
        transaction.savepoint_rollback(sid)
        return Response({"error": "..."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

This ensures database integrity even if operations fail mid-execution.

## 4. Logging and Monitoring

### 4.1 Structured Logging

The application uses Python's logging module instead of print statements:

- Different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) for appropriate severity
- Consistent log formatting with timestamps and context information
- Sensitive data is never logged (API keys, user credentials, etc.)

### 4.2 Error Tracking

- Critical errors are logged with detailed context for troubleshooting
- Performance metrics for API calls are tracked and logged
- Unexpected behaviors trigger warnings in the logs

## 5. Authentication and Authorization

### 5.1 User Authentication

- Django's authentication system with secure password hashing
- Session management with proper timeout settings
- CSRF protection for all form submissions

### 5.2 API Authorization

- Permission classes applied to all API endpoints
- Role-based access control (users vs. admin users)
- Object-level permissions (users can only access their own reports)

## 6. API Key and Secret Management

### 6.1 Environment Variables

Sensitive configuration values are stored in environment variables:

- Django SECRET_KEY
- Database credentials
- External API keys (e.g., GEMINI_API_KEY)

### 6.2 Deployment Security

- Production deployments use environment-specific settings
- Debug mode is disabled in production
- HTTPS is enforced for all communications

## 7. Best Practices for Developers

When developing new features or modifying existing code, follow these security practices:

1. **Sanitize all inputs**: Never trust user input or external API responses.
2. **Use atomic transactions**: Wrap operations that modify multiple database records.
3. **Implement proper error handling**: Catch specific exceptions and provide appropriate responses.
4. **Add logging**: Use the logging module instead of print statements.
5. **Rate limit external services**: Prevent abuse and excessive costs.
6. **Apply the principle of least privilege**: Only grant necessary permissions.
7. **Test edge cases**: Verify behavior with invalid inputs, API failures, etc.
8. **Document security considerations**: Update this guide when adding security features.

## 8. Security Incident Response

If you discover a security vulnerability:

1. Do not disclose it publicly in GitHub issues or pull requests.
2. Contact the project maintainers directly via secure channels.
3. Provide detailed information about the vulnerability and potential impact.
4. Follow responsible disclosure practices.

## 9. Regular Security Reviews

The application undergoes regular security reviews to identify and address potential vulnerabilities:

- Code reviews with a focus on security
- Dependency updates to address known vulnerabilities
- Periodic review of access controls and permissions
- Monitoring of security best practices in the Django and JavaScript ecosystems