# Endpoints
*All endpoints marked with ENC should pass encrypted data*

## `/server/` - Server-level Operations

- POST `/server/login/` - `Username, Password hash` - Logs into server as user - Returns/Creates `User` from DB
- POST `/server/login/create/` - `Username, Password hash` - Creates new user and logs in - Returns/Creates `User`, Adds to DB
- POST `/server/connection/new/` - `fingerprint, public key` - Generates new connection to API - Returns `"server publickey", "connection id"`, Creates `Connection`
- GET `/server/connection/status/{connection id}` - Gets refresh status of all endpoints for busy waiting from connection - Returns `{endpoints:status}`

## `/user/` - User-level Operations