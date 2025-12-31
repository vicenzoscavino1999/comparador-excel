# Comparador Excel

Aplicación web para comparar archivos Excel con detección automática de columnas, limpieza de datos y exportación formateada.

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

## Despliegue en Render

1. Subir este repositorio a GitHub
2. Ir a [render.com](https://render.com) y crear cuenta
3. Click en "New" → "Web Service"
4. Conectar con el repositorio de GitHub
5. Configurar:
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Click en "Create Web Service"

La URL estará lista en ~5 minutos.

## Uso

1. Registrar una cuenta
2. Iniciar sesión
3. Subir 2 archivos Excel (.xls o .xlsx)
4. Click en "Comparar"
5. Descargar el resultado

## Características

- ✅ Soporte para .xls y .xlsx
- ✅ Detección automática de columnas (Código, Producto, Cantidad)
- ✅ Limpieza de headers duplicados
- ✅ Excel de salida con 5 hojas formateadas
- ✅ Autenticación con JWT
- ✅ Archivos hasta 100MB
