# Comparador Excel v2.0

Aplicación web empresarial para comparar archivos Excel con detección automática de columnas, limpieza de datos y exportación formateada.

## ✨ Características v2.0

- ✅ Soporte para .xls y .xlsx
- ✅ Detección automática de columnas (Código, Producto, Cantidad)
- ✅ **Códigos con ceros a la izquierda preservados**
- ✅ **Manejo de duplicados (suma automática)**
- ✅ **Headers detectados hasta fila 30**
- ✅ Limpieza de headers duplicados
- ✅ Excel de salida con 5 hojas formateadas
- ✅ **Autenticación con JWT + SQLite**
- ✅ **Registro cerrado (solo admin)**
- ✅ **CORS restringido en producción**
- ✅ **Logs de comparaciones**
- ✅ Archivos hasta 100MB
- ✅ **Docker ready**

## Requisitos

- Python 3.9+
- pip

## Instalación Local

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Abrir http://localhost:8000 en el navegador.

## Crear Usuario Admin (Primera vez)

```bash
cd backend
python -c "from main import create_admin; create_admin('admin', 'admin@empresa.com', 'tu_password_seguro')"
```

## Variables de Entorno

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `SECRET_KEY` | Clave secreta para JWT (64 chars hex) | Sí en producción |
| `ALLOWED_ORIGINS` | Origins permitidos para CORS, separados por coma | No (default: localhost) |

Generar SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Despliegue con Docker

```bash
docker build -t comparador-excel .
docker run -d -p 8000:8000 \
  -e SECRET_KEY=tu_clave_secreta \
  -e ALLOWED_ORIGINS=https://tudominio.com \
  comparador-excel
```

## Despliegue en Render

1. Subir este repositorio a GitHub
2. Ir a [render.com](https://render.com) y crear cuenta
3. Click en "New" → "Web Service"
4. Conectar con el repositorio de GitHub
5. Configurar:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `SECRET_KEY`: (generar con el comando de arriba)
     - `ALLOWED_ORIGINS`: `https://tu-app.onrender.com`
6. Click en "Create Web Service"

## API Endpoints

| Endpoint | Método | Auth | Descripción |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/api/login` | POST | No | Iniciar sesión |
| `/api/register` | POST | Admin | Crear usuario (solo admin) |
| `/api/users` | GET | Admin | Listar usuarios |
| `/api/compare` | POST | User | Comparar archivos Excel |

## Estructura del Proyecto

```
comparador-excel/
├── backend/
│   ├── main.py           # FastAPI app
│   ├── auth.py           # Autenticación JWT
│   ├── database.py       # SQLite storage
│   ├── excel_processor.py # Lógica de comparación
│   └── requirements.txt
├── frontend/
│   ├── index.html        # Login
│   ├── app.html          # App principal
│   ├── css/styles.css
│   └── js/
├── Dockerfile
└── README.md
```

## Changelog

### v2.0.0
- Códigos leídos como texto (preserva ceros a la izquierda)
- Duplicados agregados automáticamente
- Headers detectados hasta fila 30
- Base de datos SQLite (antes JSON)
- Registro cerrado (solo admin)
- CORS restringido en producción
- Logs de comparaciones
- Dockerfile incluido
