# 📡 AI Feedback Quality API Endpoints

Complete reference for Phase 1 AI Feedback Quality Tracking endpoints.

**Base URL:** `/api/cases/`

**Authentication:** All endpoints require JWT authentication unless specified otherwise.

---

## 📊 AIFeedbackDetailedRating Endpoints

Base path: `/api/cases/detailed-ratings/`

### 1. Create Rating

**POST** `/api/cases/detailed-ratings/`

Submit a multi-dimensional quality rating for AI feedback received on a report.

**Request Body:**
```json
{
  "report_id": 123,
  "accuracy_rating": 4,
  "helpfulness_rating": 5,
  "actionability_rating": 4,
  "overall_rating": 4,
  "has_false_positives": false,
  "false_positive_details": "",
  "comment": "Very helpful feedback, identified key missing findings"
}
```

**Field Specifications:**
- `report_id` (integer, required): Report to rate (must belong to authenticated user)
- `accuracy_rating` (integer, 1-5, required): How accurate was the AI feedback?
- `helpfulness_rating` (integer, 1-5, required): How helpful was the feedback?
- `actionability_rating` (integer, 1-5, required): How actionable were suggestions?
- `overall_rating` (integer, 1-5, required): Overall quality rating
- `has_false_positives` (boolean, default=false): Did AI flag incorrect issues?
- `false_positive_details` (string, required if has_false_positives=true): Describe false positives
- `comment` (string, optional): Additional feedback/context

**Validation Rules:**
- User can only rate their own reports
- Report must have AI feedback (non-empty ai_feedback_content)
- One rating per user per report (unique constraint)
- If `has_false_positives=true`, `false_positive_details` is required

**Success Response (201 Created):**
```json
{
  "id": 45,
  "report_id": 123,
  "user": {
    "id": 10,
    "username": "student1",
    "email": "student1@example.com"
  },
  "accuracy_rating": 4,
  "helpfulness_rating": 5,
  "actionability_rating": 4,
  "overall_rating": 4,
  "has_false_positives": false,
  "false_positive_details": "",
  "comment": "Very helpful feedback",
  "rated_at": "2025-01-12T14:30:00Z"
}
```

**Error Responses:**

**400 Bad Request** - Report has no AI feedback:
```json
{
  "report_id": ["This report does not have AI feedback to rate."]
}
```

**400 Bad Request** - Not your report:
```json
{
  "report_id": ["You can only rate your own reports."]
}
```

**400 Bad Request** - False positive details missing:
```json
{
  "false_positive_details": ["This field is required when has_false_positives is true."]
}
```

**400 Bad Request** - Duplicate rating:
```json
{
  "non_field_errors": ["The fields report, user must make a unique set."]
}
```

---

### 2. List User's Ratings

**GET** `/api/cases/detailed-ratings/`

Retrieve all ratings submitted by the authenticated user.

**Query Parameters:**
- `page` (integer, optional): Page number for pagination
- `page_size` (integer, optional): Results per page (default: 10)

**Success Response (200 OK):**
```json
{
  "count": 15,
  "next": "/api/cases/detailed-ratings/?page=2",
  "previous": null,
  "results": [
    {
      "id": 45,
      "report_id": 123,
      "user": {
        "id": 10,
        "username": "student1",
        "email": "student1@example.com"
      },
      "accuracy_rating": 4,
      "helpfulness_rating": 5,
      "actionability_rating": 4,
      "overall_rating": 4,
      "has_false_positives": false,
      "false_positive_details": "",
      "comment": "Very helpful",
      "rated_at": "2025-01-12T14:30:00Z"
    },
    ...
  ]
}
```

---

### 3. Retrieve Specific Rating

**GET** `/api/cases/detailed-ratings/{id}/`

Get details of a specific rating by ID.

**Success Response (200 OK):**
```json
{
  "id": 45,
  "report_id": 123,
  "user": {...},
  "accuracy_rating": 4,
  "helpfulness_rating": 5,
  "actionability_rating": 4,
  "overall_rating": 4,
  "has_false_positives": false,
  "false_positive_details": "",
  "comment": "Very helpful",
  "rated_at": "2025-01-12T14:30:00Z"
}
```

**Error Response:**

**404 Not Found:**
```json
{
  "detail": "Not found."
}
```

---

### 4. Get Basic Analytics (Legacy)

**GET** `/api/cases/detailed-ratings/analytics/`

**⚠️ DEPRECATED**: Use new analytics endpoints below instead.

Returns basic aggregated metrics.

**Permissions:** Admin only (`is_staff=True`)

**Success Response (200 OK):**
```json
{
  "total_ratings": 150,
  "average_accuracy": 4.2,
  "average_helpfulness": 4.5,
  "average_actionability": 4.1,
  "average_overall": 4.3,
  "false_positive_count": 12,
  "false_positive_rate": 8.0
}
```

---

## 📈 Advanced Analytics Endpoints

### 5. Cost Trends Analytics

**GET** `/api/cases/detailed-ratings/analytics/cost-trends/`

Track AI API token usage and costs over time with cache savings analysis.

**Permissions:** Admin only (`is_staff=True`)

**Query Parameters:**
- `days` (integer, optional, default=30, max=365): Analysis period

**Success Response (200 OK):**
```json
{
  "total_requests": 450,
  "total_prompt_tokens": 675000,
  "total_completion_tokens": 135000,
  "total_cost_usd": "20.25",
  "cached_requests": 85,
  "cache_savings_usd": "3.825",
  "daily_breakdown": [
    {
      "date": "2025-01-12",
      "requests": 25,
      "prompt_tokens": 37500,
      "completion_tokens": 7500,
      "cost_usd": "1.125",
      "cached_count": 5
    },
    ...
  ]
}
```

**Field Descriptions:**
- `total_requests`: Total AI feedback requests in period
- `total_prompt_tokens`: Sum of input tokens
- `total_completion_tokens`: Sum of output tokens
- `total_cost_usd`: Total API costs (Decimal, 6 decimals precision)
- `cached_requests`: Requests served from cache
- `cache_savings_usd`: Estimated savings from cache hits
- `daily_breakdown`: Day-by-day metrics

**Example Usage:**
```bash
# Last 7 days
curl -H "Authorization: Bearer {admin_token}" \
  "https://api.example.com/api/cases/detailed-ratings/analytics/cost-trends/?days=7"

# Last 90 days
curl -H "Authorization: Bearer {admin_token}" \
  "https://api.example.com/api/cases/detailed-ratings/analytics/cost-trends/?days=90"
```

---

### 6. Prompt Version Comparison

**GET** `/api/cases/detailed-ratings/analytics/prompt-comparison/`

Compare AI feedback quality ratings across different prompt versions for A/B testing.

**Permissions:** Admin only (`is_staff=True`)

**Success Response (200 OK):**
```json
{
  "prompt_versions": [
    {
      "prompt_version_id": 3,
      "version_name": "v2.0",
      "is_active": true,
      "rating_count": 125,
      "avg_accuracy": 4.5,
      "avg_helpfulness": 4.7,
      "avg_actionability": 4.4,
      "avg_overall": 4.5,
      "false_positive_count": 8,
      "false_positive_rate": 6.4
    },
    {
      "prompt_version_id": 2,
      "version_name": "v1.5",
      "is_active": false,
      "rating_count": 80,
      "avg_accuracy": 4.2,
      "avg_helpfulness": 4.3,
      "avg_actionability": 4.0,
      "avg_overall": 4.2,
      "false_positive_count": 10,
      "false_positive_rate": 12.5
    }
  ],
  "note": "Compare average ratings across prompt versions to identify best performers."
}
```

**Field Descriptions:**
- `prompt_version_id`: Database ID of prompt version
- `version_name`: Human-readable version identifier (e.g., "v2.0")
- `is_active`: Whether this version is currently in use
- `rating_count`: Number of ratings for this version
- `avg_accuracy/helpfulness/actionability/overall`: Average ratings (1-5 scale)
- `false_positive_count`: Reports with false positives flagged
- `false_positive_rate`: Percentage (0-100)

**Sorting:** Results sorted by rating_count descending (most rated first), then version_name

**Example Usage:**
```bash
curl -H "Authorization: Bearer {admin_token}" \
  "https://api.example.com/api/cases/detailed-ratings/analytics/prompt-comparison/"
```

---

### 7. Cache Performance Metrics

**GET** `/api/cases/detailed-ratings/analytics/cache-performance/`

Analyze effectiveness of AI feedback caching system.

**Permissions:** Admin only (`is_staff=True`)

**Query Parameters:**
- `days` (integer, optional, default=30, max=365): Analysis period

**Success Response (200 OK):**
```json
{
  "total_cached_entries": 450,
  "cache_hit_rate": 18.9,
  "avg_cache_age_minutes": 720.5,
  "expired_entries": 85,
  "cost_savings_usd": "3.825",
  "requests_using_cache": 85,
  "requests_not_cached": 365
}
```

**Field Descriptions:**
- `total_cached_entries`: Total entries in FeedbackCache table
- `cache_hit_rate`: Percentage of requests served from cache (0-100)
- `avg_cache_age_minutes`: Average age of cached entries
- `expired_entries`: Entries older than 24 hours
- `cost_savings_usd`: Total costs saved by cache hits
- `requests_using_cache`: Count of cache hits in period
- `requests_not_cached`: Count of cache misses in period

**Example Usage:**
```bash
# Cache performance over last 7 days
curl -H "Authorization: Bearer {admin_token}" \
  "https://api.example.com/api/cases/detailed-ratings/analytics/cache-performance/?days=7"
```

---

## 🔒 Authentication & Permissions

### JWT Token Authentication

All endpoints require a valid JWT access token in the `Authorization` header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Obtaining Tokens:**

**POST** `/api/auth/login/` (or your token endpoint)
```json
{
  "username": "student1",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Permission Levels

1. **Authenticated Users** (All logged-in users):
   - Create ratings for their own reports
   - List their own ratings
   - Retrieve their own ratings

2. **Admin Users** (`is_staff=True`):
   - All authenticated user permissions
   - Access analytics endpoints
   - View aggregated data across all users

---

## 🚨 Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "field_name": ["Error message describing the issue."],
  "another_field": ["Another error message."]
}
```

Or for non-field errors:

```json
{
  "detail": "Error message describing the issue."
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 OK | Success | GET request successful |
| 201 Created | Success | POST request created resource |
| 400 Bad Request | Validation Error | Missing/invalid fields, business rule violation |
| 401 Unauthorized | Authentication Failed | Missing or invalid JWT token |
| 403 Forbidden | Permission Denied | Non-admin accessing admin endpoint |
| 404 Not Found | Resource Not Found | Invalid ID in URL |
| 500 Internal Server Error | Server Error | Unexpected server-side issue |

---

## 📝 Usage Examples

### Complete Rating Flow

```javascript
// 1. User submits report (outside this API scope)
const reportId = 123;

// 2. User receives AI feedback (outside this API scope)

// 3. User rates the AI feedback
const rating = await fetch('/api/cases/detailed-ratings/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    report_id: reportId,
    accuracy_rating: 4,
    helpfulness_rating: 5,
    actionability_rating: 4,
    overall_rating: 4,
    has_false_positives: false,
    comment: 'Very helpful, identified key missing findings'
  })
});

if (rating.ok) {
  console.log('Rating submitted successfully');
}
```

### Admin Analytics Dashboard

```javascript
// Fetch all analytics for dashboard
async function loadAnalyticsDashboard() {
  const headers = {
    'Authorization': `Bearer ${adminToken}`
  };

  // Cost trends
  const costResponse = await fetch(
    '/api/cases/detailed-ratings/analytics/cost-trends/?days=30',
    { headers }
  );
  const costData = await costResponse.json();

  // Prompt comparison
  const promptResponse = await fetch(
    '/api/cases/detailed-ratings/analytics/prompt-comparison/',
    { headers }
  );
  const promptData = await promptResponse.json();

  // Cache performance
  const cacheResponse = await fetch(
    '/api/cases/detailed-ratings/analytics/cache-performance/?days=30',
    { headers }
  );
  const cacheData = await cacheResponse.json();

  return { costData, promptData, cacheData };
}
```

---

## 🧪 Testing Endpoints

### Using cURL

```bash
# Create rating
curl -X POST https://api.example.com/api/cases/detailed-ratings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_id": 123,
    "accuracy_rating": 4,
    "helpfulness_rating": 5,
    "actionability_rating": 4,
    "overall_rating": 4,
    "comment": "Great feedback!"
  }'

# Get cost trends (admin)
curl https://api.example.com/api/cases/detailed-ratings/analytics/cost-trends/?days=7 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Using Python requests

```python
import requests

BASE_URL = 'https://api.example.com'
TOKEN = 'your_jwt_token'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

# Create rating
rating_data = {
    'report_id': 123,
    'accuracy_rating': 4,
    'helpfulness_rating': 5,
    'actionability_rating': 4,
    'overall_rating': 4,
    'comment': 'Very helpful!'
}

response = requests.post(
    f'{BASE_URL}/api/cases/detailed-ratings/',
    json=rating_data,
    headers=headers
)

if response.status_code == 201:
    print('Rating created:', response.json())
```

---

## 📊 Rate Limiting

**Current Limits:** None (Phase 1)

**Future Consideration:** Implement rate limiting for analytics endpoints to prevent abuse (e.g., 100 requests/hour per user).

---

## 🔄 Versioning

**Current Version:** v1 (Phase 1)

**API Path:** `/api/cases/detailed-ratings/`

**Future Versioning:** If breaking changes needed, will use `/api/v2/cases/detailed-ratings/` pattern.

---

## 📚 Related Documentation

- **Analytics Guide**: See `ANALYTICS_GUIDE.md` for admin dashboard usage
- **Model Documentation**: See `@.claude/docs/DATA_MODELS.md` for database schema
- **Testing**: See `cases/tests/test_detailed_ratings.py` and `cases/tests/test_analytics.py`

---

**Last Updated:** 2025-01-12
**Phase:** 1 (Foundation)
**Status:** Complete
