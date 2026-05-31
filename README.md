# ContApp — Backend Django 🐍

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Django-5.2.7-green?style=for-the-badge&logo=django&logoColor=white"/>
  <img src="https://img.shields.io/badge/Django%20REST%20Framework-API%20REST-red?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Base%20de%20datos-SQLite3-lightgrey?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Estado-Finalizado-brightgreen?style=for-the-badge"/>
</p>

---

## Índice

1. [Descripción del proyecto](#descripción-del-proyecto)
2. [Estado del proyecto](#estado-del-proyecto)
3. [Endpoints de la API](#endpoints-de-la-api)
4. [Especificación detallada de endpoints](#especificación-detallada-de-endpoints)
5. [Cómo acceder y ejecutar el proyecto](#cómo-acceder-y-ejecutar-el-proyecto)
6. [Tecnologías utilizadas](#tecnologías-utilizadas)

---

## Descripción del proyecto

**ContApp Backend** es una API REST desarrollada con Django y Django REST Framework que da soporte a una aplicación Android de contadores grupales colaborativos. Gestiona cuentas de usuario, contadores compartidos y el seguimiento de contribuciones individuales de cada participante.

### ¿Qué es un contador?

Un **contador** es la entidad central del sistema. Tiene un título, una descripción opcional, una imagen de portada opcional y una fecha y hora de cierre (`closed_at`). El **estado** del contador (`open` o `closed`) no es un campo almacenado en la base de datos, sino una propiedad calculada en tiempo real que compara `closed_at` con el momento actual de cada petición. Múltiples usuarios pueden participar en el mismo contador, cada uno acumulando su propio `individual_count`. La suma de todos los `individual_count` de los participantes es el `global_count`.

### Autenticación JWT

Al registrarse o iniciar sesión, el servidor emite tokens JWT usando `djangorestframework-simplejwt`:

- **Access token** — válido durante **7 días**. Se envía en la cabecera `Authorization: Bearer <token>` en todas las peticiones protegidas.
- **Refresh token** — válido durante **8 días**. Se usa para obtener un nuevo access token sin necesidad de volver a introducir las credenciales mediante `POST /api/auth/refresh/`.

Los tiempos de vida son intencionalmente largos para minimizar la fricción de relogin en el cliente móvil.

> ⚠️ **Nota:** El endpoint de login devuelve únicamente el access token (campo `token`), mientras que el registro devuelve tanto `access` como `refresh`. Esta asimetría es intencionada.

### Sistema de invitación

Al crear un contador, el backend genera automáticamente un `invite_code` de tipo UUID. El creador recibe este código en la respuesta y puede compartirlo. Cualquier usuario autenticado puede llamar a `POST /api/counters/join/` con ese código para unirse al contador, siempre que este esté abierto y el usuario no sea ya miembro.

### Almacenamiento de imágenes

Las imágenes de los contadores se guardan en el servidor bajo el directorio `counter_images/` relativo a `MEDIA_ROOT`. Para que funcionen correctamente en desarrollo es necesario configurar `MEDIA_ROOT` y `MEDIA_URL` en `settings.py` (ver sección de instalación).

### Conexión con el cliente Android

`ALLOWED_HOSTS` incluye `10.0.2.2`, que es la IP especial que usa el emulador Android para acceder al `localhost` del equipo host, permitiendo que la app Android se conecte al servidor de desarrollo sin configuración adicional.

---

## Estado del proyecto

**✅ Proyecto finalizado — versión 1.0**

### Endpoints de autenticación

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/register/` | Registrar un nuevo usuario; devuelve access + refresh token |
| POST | `/api/auth/login/` | Autenticarse con username/email/teléfono + contraseña; devuelve access token |
| POST | `/api/auth/refresh/` | Renovar el access token usando el refresh token |
| GET | `/api/auth/profile/` | Devuelve los datos del usuario autenticado |

### Endpoints de contadores

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/counters/` | Listar todos los contadores del usuario autenticado |
| POST | `/api/counters/create/` | Crear un nuevo contador |
| GET | `/api/counters/<id>/` | Obtener el detalle completo de un contador |
| PUT | `/api/counters/<id>/update/` | Actualizar un contador (solo el creador) |
| DELETE | `/api/counters/<id>/delete/` | Eliminar un contador (solo el creador) |
| POST | `/api/counters/<id>/increment/` | Sumar +1 al conteo individual del usuario |
| POST | `/api/counters/join/` | Unirse a un contador mediante código de invitación |

### Endpoints de documentación

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/schema/` | Descarga el esquema OpenAPI 3.0 en JSON o YAML |
| GET | `/api/docs/` | Interfaz Swagger UI interactiva |

---

## Especificación detallada de endpoints

### `POST /api/auth/register/`

**Autenticación requerida:** No

**Body (JSON):**

| Campo | Tipo | Obligatorio |
|---|---|---|
| `username` | String | Sí |
| `email` | String | Sí |
| `password` | String | Sí |
| `telephone` | String (máx. 12 caracteres) | Sí |

**Respuestas:**

| Código | Significado |
|---|---|
| 201 | Usuario creado correctamente |
| 400 | Campo faltante o username/email/teléfono ya existente |

**Body de respuesta exitosa (201):**

```json
{
  "refresh": "string (JWT refresh token)",
  "access": "string (JWT access token)",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "telephone": "string"
  }
}
```

---

### `POST /api/auth/login/`

**Autenticación requerida:** No

**Body (JSON):**

| Campo | Tipo | Obligatorio |
|---|---|---|
| `username` o `email` o `telephone` | String | Sí (al menos uno) |
| `password` | String | Sí |

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Login correcto |
| 400 | Faltan campos obligatorios |
| 401 | Credenciales incorrectas |

**Body de respuesta exitosa (200):**

```json
{
  "token": "string (JWT access token)",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "telephone": "string"
  }
}
```

---

### `POST /api/auth/refresh/`

**Autenticación requerida:** No

**Body (JSON):**

| Campo | Tipo | Obligatorio |
|---|---|---|
| `refresh` | String (JWT refresh token) | Sí |

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Nuevo access token emitido |
| 401 | Refresh token inválido o expirado |

---

### `GET /api/auth/profile/`

**Autenticación requerida:** Sí

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Perfil devuelto correctamente |
| 401 | Token no proporcionado o inválido |

**Body de respuesta exitosa (200):**

```json
{
  "username": "string",
  "email": "string",
  "telephone": "string"
}
```

---

### `GET /api/counters/`

**Autenticación requerida:** Sí

**Query params opcionales:**

| Param | Valores |
|---|---|
| `status` | `open` o `closed` |

**Body de respuesta exitosa (200):** Array de objetos:

```json
[
  {
    "id": 1,
    "title": "string",
    "image_url": "string o null",
    "status": "open o closed",
    "individual_count": 0,
    "global_count": 0
  }
]
```

---

### `POST /api/counters/create/`

**Autenticación requerida:** Sí

**Body (multipart/form-data):**

| Campo | Tipo | Obligatorio |
|---|---|---|
| `title` | String | Sí |
| `closed_at` | String (ISO 8601) | Sí |
| `description` | String | No |
| `image` | Archivo | No |

**Respuestas:**

| Código | Significado |
|---|---|
| 201 | Contador creado correctamente |
| 400 | Falta título o fecha / fecha inválida / fecha en el pasado |
| 401 | Token no válido |

**Body de respuesta exitosa (201):**

```json
{
  "message": "Counter created successfully!",
  "counter_id": 1,
  "invite_code": "uuid-string"
}
```

---

### `GET /api/counters/<id>/`

**Autenticación requerida:** Sí

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Detalle del contador devuelto |
| 403 | El usuario no es miembro de este contador |
| 404 | Contador no encontrado |

**Body de respuesta exitosa (200):**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "image_url": "string o null",
  "status": "open o closed",
  "closed_at": "ISO 8601 string o null",
  "participants": 3,
  "global_count": 42,
  "individual_count": 10,
  "invite_code": "uuid-string",
  "is_creator": true,
  "ranking": [
    { "username": "string", "total_clicks": 20 }
  ]
}
```

---

### `PUT /api/counters/<id>/update/`

**Autenticación requerida:** Sí (solo el creador, contador abierto)

**Body (multipart/form-data, todos opcionales):**

| Campo | Tipo |
|---|---|
| `title` | String |
| `description` | String |
| `closed_at` | String ISO 8601 o `""` para borrar |
| `image` | Archivo |

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Contador actualizado |
| 400 | El contador está cerrado |
| 403 | El usuario no es el creador |
| 404 | Contador no encontrado |

---

### `DELETE /api/counters/<id>/delete/`

**Autenticación requerida:** Sí (solo el creador)

**Respuestas:**

| Código | Significado |
|---|---|
| 204 | Contador eliminado (sin cuerpo de respuesta) |
| 403 | El usuario no es el creador |
| 404 | Contador no encontrado |

---

### `POST /api/counters/<id>/increment/`

**Autenticación requerida:** Sí

**Respuestas:**

| Código | Significado |
|---|---|
| 200 | Conteo incrementado correctamente |
| 400 | El contador está cerrado |
| 401 | El usuario no es miembro del contador |
| 404 | Contador no encontrado |

**Body de respuesta exitosa (200):**

```json
{
  "message": "Counter incremented successfully!",
  "individual_count": 11,
  "global_count": 43
}
```

---

### `POST /api/counters/join/`

**Autenticación requerida:** Sí

**Body (JSON):**

| Campo | Tipo | Obligatorio |
|---|---|---|
| `invite_code` | String (UUID) | Sí |

**Respuestas:**

| Código | Significado |
|---|---|
| 201 | Unido al contador correctamente |
| 400 | Código faltante / contador cerrado / ya es miembro |
| 404 | Contador no encontrado con ese código |

**Body de respuesta exitosa (201):**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "status": "open",
  "invite_code": "uuid-string"
}
```

---

## Cómo acceder y ejecutar el proyecto

### Requisitos previos

- Python 3.14
- pip

### Pasos para ejecutar

**1. Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd ProyectoFinalDAMDjango/python/ContApp
```

**2. Crear y activar el entorno virtual**
```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**3. Instalar dependencias**

> ⚠️ El repositorio no incluye `requirements.txt`. Instalar manualmente:

```bash
pip install django djangorestframework djangorestframework-simplejwt drf-spectacular Pillow PyJWT
```

**4. Configurar el almacenamiento de imágenes**

Añadir al final de `settings.py` antes de ejecutar:

```python
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

Y en `urls.py` añadir al final de `urlpatterns`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**5. Aplicar migraciones**
```bash
python manage.py migrate
```

**6. (Opcional) Crear superusuario para el panel de administración**
```bash
python manage.py createsuperuser
```

**7. Arrancar el servidor**
```bash
python manage.py runserver
```

El servidor estará disponible en `http://127.0.0.1:8000/`. El emulador Android puede acceder a él en `http://10.0.2.2:8000/`.

La documentación interactiva Swagger estará disponible en `http://127.0.0.1:8000/api/docs/`.

---

### ⚠️ Configuraciones importantes antes de desplegar en producción

| Ajuste | Estado actual | Qué hacer |
|---|---|---|
| `SECRET_KEY` | Hardcodeada en `settings.py` | Mover a variable de entorno |
| `DEBUG` | `True` | Cambiar a `False` |
| `ALLOWED_HOSTS` | Solo localhost y emulador | Añadir el dominio real |
| `MEDIA_ROOT` / `MEDIA_URL` | No configurados | Añadir según paso 4 |

---

## Tecnologías utilizadas

| Tecnología | Versión | Uso |
|---|---|---|
| **Python** | 3.14 | Lenguaje de programación principal |
| **Django** | 5.2.7 | Framework web, ORM, panel de administración |
| **Django REST Framework** | — | Capa de API REST, decoradores `@api_view`, permisos |
| **djangorestframework-simplejwt** | — | Emisión y validación de tokens JWT, `TokenRefreshView` |
| **drf-spectacular** | — | Generación automática del esquema OpenAPI 3.0 y Swagger UI |
| **Pillow** | — | Procesamiento de imágenes requerido por `ImageField` |
| **PyJWT** | — | Importado directamente en `views.py` para operaciones JWT |
| **SQLite3** | Incluido en Python | Base de datos de desarrollo (`db.sqlite3`) |
| **uuid** | Incluido en Python | Generación automática del `invite_code` de los contadores |
