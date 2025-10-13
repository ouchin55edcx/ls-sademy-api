# Template CRUD API Documentation

## Overview
This document provides comprehensive documentation for the Template CRUD (Create, Read, Update, Delete) operations available for admin users. The Template API allows administrators to manage service templates with file upload capabilities for both template files and demo videos.

## Authentication
All Template CRUD endpoints require admin authentication. Include the admin token in the Authorization header:

```
Authorization: Token <your-admin-token>
```

## Base URL
```
http://localhost:8000/api/admin/templates/
```

## Model Structure

### Template Model Attributes
- **`id`** (Auto-generated): Primary key
- **`service`** (ForeignKey): Reference to the Service model
- **`title`** (CharField): Template title/name
- **`description`** (TextField): Template description
- **`file`** (FileField): Template file (stored in `media/templates/files/`)
- **`demo_video`** (FileField): Demo video file (stored in `media/templates/demos/`)

## API Endpoints

### 1. List All Templates
**GET** `/api/admin/templates/`

Retrieve all templates with optional filtering.

#### Query Parameters
- `service_id` (optional): Filter templates by service ID
- `search` (optional): Search templates by title or description

#### Examples
```bash
# Get all templates
GET /api/admin/templates/

# Filter by service ID
GET /api/admin/templates/?service_id=7

# Search templates
GET /api/admin/templates/?search=portfolio
```

#### Response
```json
[
  {
    "id": 1,
    "service": 7,
    "service_name": "Web Development",
    "title": "E-commerce Website Template",
    "description": "Modern e-commerce template with shopping cart, payment integration, and product management.",
    "file": "http://localhost:8000/media/templates/files/ecommerce-template.zip",
    "demo_video": "http://localhost:8000/media/templates/demos/ecommerce-demo.mp4"
  },
  {
    "id": 2,
    "service": 7,
    "service_name": "Web Development",
    "title": "Portfolio Website Template",
    "description": "Clean and professional portfolio template for showcasing your work.",
    "file": "http://localhost:8000/media/templates/files/portfolio-template.zip",
    "demo_video": null
  }
]
```

#### cURL Example
```bash
curl -X GET "http://localhost:8000/api/admin/templates/" \
  -H "Authorization: Token <your-admin-token>" \
  -H "Content-Type: application/json"
```

---

### 2. Create New Template
**POST** `/api/admin/templates/create/`

Create a new template with optional file uploads.

#### Request Body (multipart/form-data)
- `service` (required): Service ID
- `title` (required): Template title
- `description` (optional): Template description
- `file` (optional): Template file
- `demo_video` (optional): Demo video file

#### Validation Rules
- Service must exist and be active
- Template title must be unique within the same service
- File uploads are optional

#### Response
```json
{
  "id": 12,
  "service": 7,
  "service_name": "Web Development",
  "title": "New Portfolio Template",
  "description": "Modern portfolio template with animations",
  "file": "http://localhost:8000/media/templates/files/new-portfolio.zip",
  "demo_video": "http://localhost:8000/media/templates/demos/portfolio-demo.mp4"
}
```

#### cURL Example (with files)
```bash
curl -X POST http://localhost:8000/api/admin/templates/create/ \
  -H "Authorization: Token <your-admin-token>" \
  -F "service=7" \
  -F "title=New Portfolio Template" \
  -F "description=Modern portfolio template with animations" \
  -F "file=@/path/to/template.zip" \
  -F "demo_video=@/path/to/demo.mp4"
```

#### cURL Example (without files)
```bash
curl -X POST http://localhost:8000/api/admin/templates/create/ \
  -H "Authorization: Token <your-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "service": 7,
    "title": "New Portfolio Template",
    "description": "Modern portfolio template with animations"
  }'
```

---

### 3. Retrieve Single Template
**GET** `/api/admin/templates/{id}/`

Get details of a specific template.

#### Response
```json
{
  "id": 1,
  "service": 7,
  "service_name": "Web Development",
  "title": "E-commerce Website Template",
  "description": "Modern e-commerce template with shopping cart, payment integration, and product management.",
  "file": "http://localhost:8000/media/templates/files/ecommerce-template.zip",
  "demo_video": "http://localhost:8000/media/templates/demos/ecommerce-demo.mp4"
}
```

#### cURL Example
```bash
curl -X GET http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <your-admin-token>" \
  -H "Content-Type: application/json"
```

---

### 4. Update Template
**PUT** `/api/admin/templates/{id}/` or **PATCH** `/api/admin/templates/{id}/`

Update an existing template. Use PUT for complete update or PATCH for partial update.

#### Request Body (multipart/form-data for file uploads or application/json)
- `service` (optional): Service ID
- `title` (optional): Template title
- `description` (optional): Template description
- `file` (optional): New template file
- `demo_video` (optional): New demo video file

#### Response
```json
{
  "service": 7,
  "title": "Updated E-commerce Website Template",
  "description": "Updated description for the e-commerce template",
  "file": "http://localhost:8000/media/templates/files/updated-ecommerce.zip",
  "demo_video": "http://localhost:8000/media/templates/demos/updated-demo.mp4"
}
```

#### cURL Example (PATCH with JSON)
```bash
curl -X PATCH http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <your-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated E-commerce Website Template",
    "description": "Updated description for the e-commerce template"
  }'
```

#### cURL Example (PUT with file upload)
```bash
curl -X PUT http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <your-admin-token>" \
  -F "service=7" \
  -F "title=Updated E-commerce Website Template" \
  -F "description=Updated description" \
  -F "file=@/path/to/new-template.zip" \
  -F "demo_video=@/path/to/new-demo.mp4"
```

---

### 5. Delete Template
**DELETE** `/api/admin/templates/{id}/`

Delete a template permanently.

#### Response
```json
{
  "message": "Template deleted successfully"
}
```

#### cURL Example
```bash
curl -X DELETE http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <your-admin-token>" \
  -H "Content-Type: application/json"
```

---

## Error Responses

### 400 Bad Request
```json
{
  "service": ["Cannot create template for inactive service."],
  "title": ["Template with this title already exists for this service."]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## File Upload Guidelines

### Supported File Types
- **Template files**: Any file type (zip, pdf, doc, etc.)
- **Demo videos**: Video files (mp4, avi, mov, etc.)

### File Storage
- Template files are stored in: `media/templates/files/`
- Demo videos are stored in: `media/templates/demos/`
- Files are automatically renamed to prevent conflicts

### File Size Limits
- Default Django file upload limit applies
- Configure `FILE_UPLOAD_MAX_MEMORY_SIZE` and `DATA_UPLOAD_MAX_MEMORY_SIZE` in settings if needed

---

## Testing Examples

### 1. Test Authentication
```bash
# Login as admin to get token
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username_or_phone": "admin", "password": "admin123"}'
```

### 2. Test Complete CRUD Flow
```bash
# 1. List all templates
curl -X GET http://localhost:8000/api/admin/templates/ \
  -H "Authorization: Token <token>"

# 2. Create new template
curl -X POST http://localhost:8000/api/admin/templates/create/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"service": 7, "title": "Test Template", "description": "Test description"}'

# 3. Get specific template
curl -X GET http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <token>"

# 4. Update template
curl -X PATCH http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Test Template"}'

# 5. Delete template
curl -X DELETE http://localhost:8000/api/admin/templates/1/ \
  -H "Authorization: Token <token>"
```

### 3. Test File Upload
```bash
# Create test files
echo "Template content" > template.txt
echo "Demo content" > demo.txt

# Upload with files
curl -X POST http://localhost:8000/api/admin/templates/create/ \
  -H "Authorization: Token <token>" \
  -F "service=7" \
  -F "title=Template with Files" \
  -F "description=Template with file uploads" \
  -F "file=@template.txt" \
  -F "demo_video=@demo.txt"
```

---

## Database Migration

The Template model has been updated to support file uploads. The migration has been created and applied:

```bash
# Migration file: core/migrations/0004_remove_template_demo_template_demo_video_and_more.py
# Changes:
# - Removed 'demo' CharField
# - Added 'demo_video' FileField
# - Updated 'file' to FileField
```

---

## Security Considerations

1. **Authentication Required**: All endpoints require admin authentication
2. **File Upload Security**: Files are stored in designated directories
3. **Input Validation**: All inputs are validated before processing
4. **Permission Checks**: Only admin users can access these endpoints

---

## Performance Notes

1. **File Storage**: Files are stored on the local filesystem
2. **Database Queries**: Templates are fetched with related service data using `select_related`
3. **Filtering**: Database-level filtering for better performance
4. **Pagination**: Consider implementing pagination for large template lists

---

## Future Enhancements

1. **File Type Validation**: Add specific file type validation
2. **File Size Limits**: Implement configurable file size limits
3. **Image Thumbnails**: Generate thumbnails for demo videos
4. **Template Categories**: Add template categorization
5. **Version Control**: Track template versions
6. **Bulk Operations**: Support bulk template operations
