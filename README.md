# Unique Code Generator API

A FastAPI service for generating, managing, and validating unique burnable codes.

## Features

- Generate unique codes based on a prefix and master promocode
- Assign codes to emails
- Validate code status
- Translate codes to their master promocode
- Mark codes as used

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

### 1. Generate Hashes
- **Endpoint:** `/generateHashes`
- **Method:** POST
- **Request Body:**
```json
{
  "prefix": "UNC",
  "quantity": 5,
  "masterPromocode": "PROMO2025"
}
```
- **Response:**
```json
{
  "success": true,
  "hashes": ["UNC3A9Z", "UNCX7T2", "UNC1M8Q", "UNCB2L0", "UNCA9K7"],
  "masterPromocode": "PROMO2025"
}
```

### 2. Assign Hash
- **Endpoint:** `/assign`
- **Method:** POST
- **Request Body:**
```json
{
  "email": "usuario@correo.com",
  "prefix": "UNC"
}
```
- **Response:**
```json
{
  "success": true,
  "assignedHash": "UNCX7T2",
  "email": "usuario@correo.com"
}
```

### 3. Validate Hash
- **Endpoint:** `/validate`
- **Method:** POST
- **Request Body:**
```json
{
  "hash": "UNCX7T2"
}
```
- **Response:**
```json
{
  "success": true
}
```

### 4. Translate Hash
- **Endpoint:** `/translate`
- **Method:** POST
- **Request Body:**
```json
{
  "hash": "UNCX7T2"
}
```
- **Response:**
```json
{
  "success": true,
  "masterPromocode": "PROMO2025"
}
```

### 5. Use Hash
- **Endpoint:** `/use`
- **Method:** POST
- **Request Body:**
```json
{
  "hash": "UNCX7T2"
}
```
- **Response:**
```json
{
  "success": true
}
```

## Database Schema

The service uses SQLite with the following schema:

```sql
CREATE TABLE hashes (
    hash VARCHAR PRIMARY KEY,
    master_promocode VARCHAR,
    status VARCHAR,
    email VARCHAR,
    assigned_date DATETIME,
    used_date DATETIME
);
```

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 404: Hash not found or already used
- 400: Invalid request parameters
- 500: Internal server error 