"""
Main FastAPI application with enterprise security features
- Restricted CORS (configurable via env var)
- Admin-only user registration
- Comparison logging
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import os
import logging
from typing import Optional

from auth import register_user, authenticate_user, verify_token, is_admin, register_admin
from excel_processor import process_comparison
from database import log_comparison, get_all_users

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Comparador Excel",
    description="Aplicación para comparar archivos Excel",
    version="2.0.0"
)

# CORS configuration - use env var for production, localhost for dev
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

# Use APP_ENV to detect production (works on any hosting, not just Render)
IS_PRODUCTION = os.getenv("APP_ENV") == "production" or os.getenv("RENDER")

if IS_PRODUCTION:
    # Production: restrict to specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    # Development: allow all (credentials=False required when using wildcard origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Max file size: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


# Security Headers Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content Security Policy - allows scripts only from same origin
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


# Add security headers in production
if IS_PRODUCTION:
    app.add_middleware(SecurityHeadersMiddleware)


# Models
class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# Auth dependency
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No autorizado")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = parts[1]
    username = verify_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")
    
    return username


async def get_admin_user(username: str = Depends(get_current_user)):
    """Dependency that requires admin privileges"""
    if not is_admin(username):
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")
    return username


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Comparador Excel funcionando", "version": "2.0.0"}


# Auth endpoints
@app.post("/api/register")
async def register(user: UserRegister, admin_user: str = Depends(get_admin_user)):
    """Register new user - ADMIN ONLY"""
    result = register_user(user.username, user.email, user.password, by_admin=admin_user)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    logger.info(f"User {user.username} created by admin {admin_user}")
    return {"message": "Usuario registrado exitosamente"}


@app.post("/api/login")
async def login(user: UserLogin):
    token = authenticate_user(user.username, user.password)
    if not token:
        logger.warning(f"Failed login attempt for user: {user.username}")
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    logger.info(f"User {user.username} logged in")
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/users")
async def list_users(admin_user: str = Depends(get_admin_user)):
    """List all users - ADMIN ONLY"""
    users = get_all_users()
    return {"users": users}


# Preview endpoint - shows detected columns before comparison
@app.post("/api/preview")
async def preview_file(
    file: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
    """Preview file structure: detect columns and count records - REQUIRES AUTH"""
    from excel_processor import read_excel_file, detect_column, CODIGO_PATTERNS, PRODUCTO_PATTERNS, CANTIDAD_PATTERNS
    
    # Validate file type
    valid_extensions = ['.xls', '.xlsx']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in valid_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo inválido: {file.filename}. Solo se permiten archivos .xls y .xlsx"
        )
    
    try:
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Archivo excede el límite de 100MB")
        
        # Read and detect columns
        df = read_excel_file(file_content, file.filename)
        
        codigo_col = detect_column(df, CODIGO_PATTERNS)
        producto_col = detect_column(df, PRODUCTO_PATTERNS)
        cantidad_col = detect_column(df, CANTIDAD_PATTERNS)
        
        # Get all column names for reference
        all_columns = [str(col) for col in df.columns.tolist()]
        
        logger.info(f"User {username} previewed file {file.filename}: {len(df)} rows")
        
        return {
            "filename": file.filename,
            "rows": len(df),
            "columns": all_columns[:15],  # First 15 columns
            "detected": {
                "codigo": codigo_col if codigo_col else None,
                "producto": producto_col if producto_col else None,
                "cantidad": cantidad_col if cantidad_col else None
            },
            "valid": codigo_col is not None and cantidad_col is not None
        }
        
    except Exception as e:
        logger.error(f"Preview error for {username}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error al analizar archivo: {str(e)}")

# File comparison endpoint
@app.post("/api/compare")
async def compare_files(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    username: str = Depends(get_current_user)
):
    # Validate file types
    valid_extensions = ['.xls', '.xlsx']
    
    for f in [file1, file2]:
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in valid_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Archivo inválido: {f.filename}. Solo se permiten archivos .xls y .xlsx"
            )
    
    try:
        # Read file contents
        file1_content = await file1.read()
        file2_content = await file2.read()
        
        file1_size = len(file1_content)
        file2_size = len(file2_content)
        
        # Check file sizes
        if file1_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Archivo 1 excede el límite de 100MB")
        if file2_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Archivo 2 excede el límite de 100MB")
        
        logger.info(f"User {username} comparing files: {file1.filename} ({file1_size} bytes) vs {file2.filename} ({file2_size} bytes)")
        
        # Process comparison
        output_bytes, info = process_comparison(
            file1_content, file1.filename,
            file2_content, file2.filename
        )
        
        # Log the comparison
        log_comparison(
            username=username,
            file1_name=file1.filename,
            file1_size=file1_size,
            file2_name=file2.filename,
            file2_size=file2_size,
            records_compared=info["results"]["total_compared"],
            differences_found=info["results"]["with_differences"]
        )
        
        logger.info(f"Comparison complete for {username}: {info['results']['total_compared']} records, {info['results']['with_differences']} differences")
        
        # Return the Excel file (comparison info is already logged, no need for fragile HTTP header)
        return Response(
            content=output_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=comparacion_resultado.xlsx"
            }
        )
        
    except ValueError as e:
        logger.error(f"ValueError for {username}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error for {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {str(e)}")


# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/app")
async def serve_app():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.html"))

@app.get("/api/version")
async def get_version():
    return {"version": "2.1", "feature": "admin_panel"}

@app.get("/admin")
async def serve_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))

@app.get("/admin.html")
async def serve_admin_html():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))


# Mount static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


# CLI command to create initial admin (run with: python -c "from main import create_admin; create_admin('admin', 'admin@example.com', 'password')")
def create_admin(username: str, email: str, password: str):
    """Create initial admin user from command line"""
    result = register_admin(username, email, password)
    if result["success"]:
        print(f"✅ Admin user '{username}' created successfully")
    else:
        print(f"❌ Error: {result['error']}")
