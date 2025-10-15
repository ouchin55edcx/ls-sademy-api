# Review API Documentation

## Overview

The Review API allows clients to create, read, update, and delete reviews for their completed orders. Reviews can only be created after an order is completed, reviewed by admin, and accepted by the client. Reviews can be updated within 24 hours of creation.

## Authentication

All review endpoints require authentication. Include the authentication token in the request headers:

```
Authorization: Token your-auth-token-here
```

## Review Model

### Fields
- `id`: Unique identifier (read-only)
- `order`: Foreign key to Order model
- `client`: Foreign key to Client model (automatically set from authenticated user)
- `rating`: Integer from 1 to 5 (required)
- `comment`: Text field for review comments (optional)
- `date`: Creation timestamp (read-only)
- `updated_at`: Last update timestamp (read-only)
- `can_be_updated`: Boolean indicating if review can be updated (read-only)

### Constraints
- One review per order per client (unique constraint)
- Rating must be between 1 and 5
- Reviews can only be updated within 24 hours of creation
- Only clients can create/update/delete reviews
- Only completed orders with accepted livrables can be reviewed

## API Endpoints

### 1. List Client Reviews

**GET** `/api/client/reviews/`

Lists all reviews created by the authenticated client.

#### Response
```json
[
  {
    "id": 1,
    "order": 1,
    "order_id": 1,
    "client_name": "John Doe",
    "service_name": "Web Development",
    "rating": 5,
    "comment": "Excellent work! Very professional and delivered on time.",
    "date": "2024-10-15T10:00:00Z",
    "updated_at": "2024-10-15T10:00:00Z",
    "can_be_updated": false
  },
  {
    "id": 2,
    "order": 3,
    "order_id": 3,
    "client_name": "John Doe",
    "service_name": "Mobile App Development",
    "rating": 4,
    "comment": "Good work, minor issues but overall satisfied.",
    "date": "2024-10-16T14:30:00Z",
    "updated_at": "2024-10-16T15:45:00Z",
    "can_be_updated": true
  }
]
```

#### Status Codes
- `200 OK`: Successfully retrieved reviews
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Client access required

---

### 2. Create Review

**POST** `/api/client/reviews/`

Creates a new review for a completed order.

#### Request Body
```json
{
  "order": 1,
  "rating": 5,
  "comment": "Excellent work! Very professional and delivered on time."
}
```

#### Validation Rules
- `order`: Required. Must be a completed order owned by the client
- `rating`: Required. Must be between 1 and 5
- `comment`: Optional. Text field for additional comments

#### Response
```json
{
  "id": 1,
  "order": 1,
  "order_id": 1,
  "client_name": "John Doe",
  "service_name": "Web Development",
  "rating": 5,
  "comment": "Excellent work! Very professional and delivered on time.",
  "date": "2024-10-15T10:00:00Z",
  "updated_at": "2024-10-15T10:00:00Z",
  "can_be_updated": true
}
```

#### Status Codes
- `201 Created`: Review created successfully
- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Client access required
- `404 Not Found`: Order not found or not accessible

#### Error Examples
```json
{
  "order": ["You can only review completed orders."],
  "rating": ["Rating must be between 1 and 5."]
}
```

```json
{
  "non_field_errors": ["You have already reviewed this order. You can only update your review within 24 hours."]
}
```

---

### 3. Get Review Details

**GET** `/api/client/reviews/{id}/`

Retrieves details of a specific review.

#### Response
```json
{
  "id": 1,
  "order": 1,
  "order_id": 1,
  "client_name": "John Doe",
  "service_name": "Web Development",
  "rating": 5,
  "comment": "Excellent work! Very professional and delivered on time.",
  "date": "2024-10-15T10:00:00Z",
  "updated_at": "2024-10-15T10:00:00Z",
  "can_be_updated": false
}
```

#### Status Codes
- `200 OK`: Review retrieved successfully
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Client access required
- `404 Not Found`: Review not found or not accessible

---

### 4. Update Review

**PUT/PATCH** `/api/client/reviews/{id}/`

Updates an existing review. Only allowed within 24 hours of creation.

#### Request Body (PUT - complete update)
```json
{
  "order": 1,
  "rating": 4,
  "comment": "Updated comment: Very good work with minor improvements needed."
}
```

#### Request Body (PATCH - partial update)
```json
{
  "rating": 4,
  "comment": "Updated comment: Very good work with minor improvements needed."
}
```

#### Response
```json
{
  "id": 1,
  "order": 1,
  "order_id": 1,
  "client_name": "John Doe",
  "service_name": "Web Development",
  "rating": 4,
  "comment": "Updated comment: Very good work with minor improvements needed.",
  "date": "2024-10-15T10:00:00Z",
  "updated_at": "2024-10-15T11:30:00Z",
  "can_be_updated": true
}
```

#### Status Codes
- `200 OK`: Review updated successfully
- `400 Bad Request`: Validation errors or update not allowed
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Client access required
- `404 Not Found`: Review not found or not accessible

#### Error Examples
```json
{
  "non_field_errors": ["You can only update your review within 24 hours of creating it."]
}
```

---

### 5. Delete Review

**DELETE** `/api/client/reviews/{id}/`

Deletes a review. Only allowed within 24 hours of creation.

#### Response
```json
{
  "message": "Review deleted successfully"
}
```

#### Status Codes
- `200 OK`: Review deleted successfully
- `400 Bad Request`: Deletion not allowed (outside 24-hour window)
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Client access required
- `404 Not Found`: Review not found or not accessible

---

## Public Review Endpoints

### 1. List All Reviews

**GET** `/api/reviews/`

Lists all reviews with optional filtering. This endpoint is public and doesn't require authentication.

#### Query Parameters
- `service_id`: Filter reviews by service ID
- `rating`: Filter reviews by rating (1-5)
- `ordering`: Order by date (`date` or `-date`, default: `-date`)

#### Examples
```
GET /api/reviews/
GET /api/reviews/?service_id=1
GET /api/reviews/?rating=5
GET /api/reviews/?ordering=date
GET /api/reviews/?service_id=1&rating=5&ordering=-date
```

#### Response
```json
[
  {
    "id": 1,
    "order_id": 1,
    "service_id": 1,
    "service_name": "Web Development",
    "client_name": "John Doe",
    "rating": 5,
    "comment": "Excellent work!",
    "date": "2024-10-15T10:00:00Z"
  }
]
```

---

### 2. Review Statistics

**GET** `/api/reviews/statistics/`

Returns overall review statistics. This endpoint is public and doesn't require authentication.

#### Response
```json
{
  "total_reviews": 25,
  "average_rating": 4.6,
  "rating_distribution": {
    "5": 15,
    "4": 7,
    "3": 2,
    "2": 1,
    "1": 0
  },
  "services_with_reviews": 5
}
```

---

## Review Content in Livrable Response

When retrieving livrables, review content is automatically included:

**GET** `/api/client/livrables/`

```json
[
  {
    "id": 1,
    "name": "Website Final Delivery",
    "description": "Complete website with all features",
    "is_accepted": true,
    "is_reviewed_by_admin": true,
    "file_path": "/livrables/website-final.zip",
    "order_id": 1,
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "service_name": "Web Development",
    "status_name": "Completed",
    "collaborator_name": "Ahmed Benali",
    "reviews": [
      {
        "id": 1,
        "order": 1,
        "order_id": 1,
        "client_name": "John Doe",
        "service_name": "Web Development",
        "rating": 5,
        "comment": "Excellent work! Very professional and delivered on time.",
        "date": "2024-10-15T10:00:00Z",
        "updated_at": "2024-10-15T10:00:00Z",
        "can_be_updated": false
      }
    ]
  }
]
```

---http://127.0.0.1:8000/api/client/livrables/

## Business Rules

### Review Creation Requirements
1. **Client Authentication**: Only authenticated clients can create reviews
2. **Order Ownership**: Clients can only http://127.0.0.1:8000/api/reviews/review their own orders
3. **Order Status**: Order must be completed (`status.name = 'Completed'`)
4. **Admin Review**: Order must be reviewed by admin (`is_reviewed_by_admin = true`)
5. **Client Acceptance**: At least one livrable must be accepted by client (`is_accepted = true`)
6. **One Review Per Order**: Each client can only have one review per order

### Review Update/Delete Rules
1. **24-Hour Window**: Reviews can only be updated/deleted within 24 hours of creation
2. **Client Ownership**: Only the client who created the review can update/delete it
3. **Validation**: All validation rules apply during updates

### Rating System
- **Scale**: 1 to 5 stars
- **Required**: Rating is mandatory for all reviews
- **Validation**: Rating must be an integer between 1 and 5

---

## Error Handling

### Common Error Responses

#### Validation Errors (400 Bad Request)
```json
{
  "order": ["You can only review completed orders."],
  "rating": ["Rating must be between 1 and 5."]
}
```

#### Authentication Errors (401 Unauthorized)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Permission Errors (403 Forbidden)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### Not Found Errors (404 Not Found)
```json
{
  "detail": "Not found."
}
```

#### Business Logic Errors
```json
{
  "non_field_errors": [
    "You have already reviewed this order. You can only update your review within 24 hours.",
    "You can only review orders that have been reviewed by admin and accepted by you.",
    "You can only update your review within 24 hours of creating it."
  ]
}
```

---

## Usage Examples

### Creating a Review
```bash
curl -X POST http://localhost:8000/api/client/reviews/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "order": 1,
    "rating": 5,
    "comment": "Excellent work! Very professional and delivered on time."
  }'
```

### Updating a Review
```bash
curl -X PATCH http://localhost:8000/api/client/reviews/1/ \
  -H "Authorization: Token your-token-here" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "comment": "Updated comment: Very good work with minor improvements needed."
  }'
```

### Listing Client Reviews
```bash
curl -X GET http://localhost:8000/api/client/reviews/ \
  -H "Authorization: Token your-token-here"
```

### Getting Public Reviews
```bash
curl -X GET http://localhost:8000/api/reviews/?service_id=1&rating=5
```

---

## Integration Notes

### Frontend Integration
1. **Review Form**: Include order selection, rating (1-5), and comment fields
2. **Update Window**: Show update/delete options only if `can_be_updated` is true
3. **Error Handling**: Display validation errors appropriately
4. **Loading States**: Handle loading states during API calls

### Backend Integration
1. **Order Status**: Ensure orders are properly marked as completed
2. **Admin Review**: Implement admin review workflow before allowing client reviews
3. **Client Acceptance**: Implement client acceptance workflow for livrables
4. **Notifications**: Consider adding notifications when reviews are created/updated

---

## Database Schema

### Review Table
```sql
CREATE TABLE reviews (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    client_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_order_client (order_id, client_id),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
```

---

## Changelog

### Version 1.0.0 (2024-10-15)
- Initial implementation of review system
- Client review endpoints (CRUD operations)
- Public review listing and statistics
- 24-hour update window implementation
- Review content integration in livrable responses
- Comprehensive validation and error handling
