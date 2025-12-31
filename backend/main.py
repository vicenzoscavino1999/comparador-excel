from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import os
from typing import Optional

from auth import register_user, authenticate_user, verify_token
from excel_processor import process_comparison

# Create FastAPI app
app = FastAPI(
    title="Comparador Excel",
    description="Aplicación para comparar archivos Excel",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Max file size: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


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


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Comparador Excel funcionando"}


# Auth endpoints
@app.post("/api/register")
async def register(user: UserRegister):
    result = register_user(user.username, user.email, user.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"message": "Usuario registrado exitosamente"}


@app.post("/api/login")
async def login(user: UserLogin):
    token = authenticate_user(user.username, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {"access_token": token, "token_type": "bearer"}


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
        
        # Check file sizes
        if len(file1_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Archivo 1 excede el límite de 100MB")
        if len(file2_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="Archivo 2 excede el límite de 100MB")
        
        # Process comparison
        output_bytes, info = process_comparison(
            file1_content, file1.filename,
            file2_content, file2.filename
        )
        
        # Return the Excel file
        return Response(
            content=output_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=comparacion_resultado.xlsx",
                "X-Comparison-Info": str(info).replace("'", '"')
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {str(e)}")


# Serve frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/app")
async def serve_app():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.html"))


# Mount static files
if os.path.exists(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
