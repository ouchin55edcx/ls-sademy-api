# Review API Quick Reference

## Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/client/reviews/` | List client reviews | ✅ Client |
| POST | `/api/client/reviews/` | Create review | ✅ Client |
| GET | `/api/client/reviews/{id}/` | Get review details | ✅ Client |
| PUT/PATCH | `/api/client/reviews/{id}/` | Update review | ✅ Client |
| DELETE | `/api/client/reviews/{id}/` | Delete review | ✅ Client |
| GET | `/api/reviews/` | List all reviews (public) | ❌ |
| GET | `/api/reviews/statistics/` | Get review statistics | ❌ |

## Request/Response Examples

### Create Review
```bash
POST /api/client/reviews/
{
  "order": 1,
  "rating": 5,
  "comment": "Excellent work!"
}
```

### Update Review
```bash
PATCH /api/client/reviews/1/
{
  "rating": 4,
  "comment": "Updated comment"
}
```

### Review Response
```json
{
  "id": 1,
  "order": 1,
  "order_id": 1,
  "client_name": "John Doe",
  "service_name": "Web Development",
  "rating": 5,
  "comment": "Excellent work!",
  "date": "2024-10-15T10:00:00Z",
  "updated_at": "2024-10-15T10:00:00Z",
  "can_be_updated": true
}
```

## Validation Rules

- **Rating**: 1-5 (required)
- **Order**: Must be completed, reviewed by admin, and accepted by client
- **One Review**: Only one review per order per client
- **24-Hour Window**: Updates/deletes only within 24 hours of creation
- **Client Only**: Only clients can create/update/delete reviews

## Common Error Codes

- `400`: Validation errors
- `401`: Authentication required
- `403`: Client access required
- `404`: Review/order not found

## Query Parameters (Public Endpoints)

- `service_id`: Filter by service
- `rating`: Filter by rating (1-5)
- `ordering`: Sort by date (`date` or `-date`)
