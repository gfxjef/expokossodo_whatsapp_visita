# WhatsApp Attendance Notifier

Un sistema Flask robusto y seguro para recibir datos de asistencia mediante webhooks y enviar notificaciones formatadas por WhatsApp utilizando la API de WhatsApp Business.

## 🚀 Características

- **Webhook Seguro**: Endpoint POST `/attendance-webhook` para recibir datos de asistencia
- **Notificaciones WhatsApp**: Integración completa con WhatsApp Business API
- **Soporte de Imágenes**: Envío de notificaciones con imágenes via URL
- **Validación Robusta**: Validación exhaustiva de datos de entrada incluyendo URLs de imágenes
- **Logging Completo**: Sistema de logging estructurado para monitoreo
- **Rate Limiting**: Protección contra abuso con límites de tasa
- **Error Handling**: Manejo comprensivo de errores con respuestas estándar
- **Health Check**: Endpoint de monitoreo de salud del servicio
- **Configuración por Entornos**: Soporte para desarrollo, testing y producción

## 📋 Requisitos

- Python 3.8+
- WhatsApp Business API Token
- Phone Number ID de WhatsApp Business
- Acceso a la biblioteca `whatsapp-python` (incluida en el proyecto principal)

## 🛠 Instalación

### 1. Preparar el Entorno

```bash
# Navegar al directorio del proyecto
cd attendance_notifier

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración

```bash
# Copiar plantilla de configuración
cp .env.example .env

# Editar .env con tus credenciales reales
# Usar tu editor favorito para completar los valores:
notepad .env  # Windows
nano .env     # Linux/Mac
```

### 3. Configuración de WhatsApp Business API

Necesitas obtener las siguientes credenciales de [Facebook Developer Console](https://developers.facebook.com/):

1. **WHATSAPP_TOKEN**: Token de acceso de WhatsApp Business API
2. **WHATSAPP_PHONE_NUMBER_ID**: ID del número de teléfono registrado
3. **WHATSAPP_VERIFY_TOKEN**: Token personalizado para verificación de webhook
4. **WHATSAPP_RECIPIENT_NUMBER**: Número destinatario (con código de país)

## 🚦 Uso

### Ejecutar la Aplicación

```bash
# Desarrollo
python app.py

# O con variables específicas
FLASK_ENV=development python app.py

# Producción (con Gunicorn)
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Información básica del servicio |
| `/attendance-webhook` | POST | Recibe datos de asistencia |
| `/attendance-webhook` | GET | Verificación de webhook |
| `/health` | GET | Estado de salud del servicio |

## 📡 API Usage

### Enviar Notificación de Asistencia

```bash
# Enviar notificación básica sin imagen
curl -X POST http://localhost:5000/attendance-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez González",
    "empresa": "TechSolutions S.A.",
    "cargo": "Desarrollador Senior",
    "fecha_hora": "2023-12-07 14:30:00"
  }'

# Enviar notificación con imagen
curl -X POST http://localhost:5000/attendance-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez González",
    "empresa": "TechSolutions S.A.",
    "cargo": "Desarrollador Senior",
    "fecha_hora": "2023-12-07 14:30:00",
    "photo": "https://iaap.org/wp-content/uploads/2022/11/Image_001-8.jpg"
  }'
```

### Respuesta Exitosa

```json
{
  "success": true,
  "message": "Attendance notification sent successfully",
  "data": {
    "employee_name": "Juan Pérez González",
    "company": "TechSolutions S.A.",
    "timestamp": "2023-12-07T14:30:15.123456",
    "message_id": "wamid.xxx",
    "has_photo": true,
    "photo_url": "https://iaap.org/wp-content/uploads/2022/11/Image_001-8.jpg"
  }
}
```

### Formato del Mensaje WhatsApp

**Con imagen:**
- Se envía la imagen con el texto como caption
- El mensaje incluye el texto formateado más la imagen

**Solo texto:**
```
📋 *Nueva Asistencia Registrada*

👤 *Nombre:* Juan Pérez González
🏢 *Empresa:* TechSolutions S.A.
💼 *Cargo:* Desarrollador Senior
📅 *Fecha/Hora:* 2023-12-07 14:30:00

✅ Ingreso confirmado al evento
```

## 🧪 Testing

### Script de Prueba Automático

```bash
# Ejecutar pruebas con datos ficticios
python tests/test_webhook.py

# Opciones personalizadas
python tests/test_webhook.py --count 10 --delay 1.5 --test-errors

# Probar contra servidor remoto
python tests/test_webhook.py --host production-server.com --port 80
```

### Pruebas Manuales

```bash
# Verificar salud del servicio
curl http://localhost:5000/health

# Probar con datos inválidos
curl -X POST http://localhost:5000/attendance-webhook \
  -H "Content-Type: application/json" \
  -d '{"nombre": ""}'
```

## 📁 Estructura del Proyecto

```
attendance_notifier/
├── app.py                      # Aplicación Flask principal
├── config.py                   # Configuración por entornos
├── requirements.txt            # Dependencias Python
├── .env.example               # Plantilla de configuración
├── README.md                  # Esta documentación
├── services/
│   ├── __init__.py
│   └── whatsapp_service.py    # Servicio WhatsApp
├── handlers/
│   ├── __init__.py
│   └── webhook_handler.py     # Manejador de webhooks
└── tests/
    ├── __init__.py
    └── test_webhook.py        # Script de pruebas
```

## ⚙️ Configuración por Entornos

### Desarrollo
```bash
FLASK_ENV=development
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

### Producción
```bash
FLASK_ENV=production
FLASK_DEBUG=False
LOG_LEVEL=WARNING
SECRET_KEY=strong-random-key
```

### Testing
```bash
FLASK_ENV=testing
# Usa valores mock para WhatsApp
```

## 🔒 Seguridad

- **Rate Limiting**: 100 requests por hora por defecto
- **Input Validation**: Validación estricta de todos los datos
- **Error Handling**: No exposición de información sensible
- **Logging**: Registro de todas las operaciones para auditoría
- **Environment Variables**: Credenciales en variables de entorno

## 📊 Monitoreo y Logs

### Logs Estructurados
```
2023-12-07 14:30:15 INFO [webhook_handler] [handle_attendance_webhook:45] Successfully processed attendance for Juan Pérez González from TechSolutions S.A.
```

### Health Check
```bash
curl http://localhost:5000/health
```

Respuesta:
```json
{
  "success": true,
  "status": "healthy",
  "service_info": {
    "service": "WhatsApp Attendance Notifier",
    "status": "active",
    "phone_number_id": "123456789",
    "recipient_number": "+1234567890",
    "timestamp": "2023-12-07T14:30:15.123456"
  }
}
```

## 🚨 Troubleshooting

### Problemas Comunes

**1. Error de conexión WhatsApp**
```
Error: WhatsApp service is currently unavailable
```
- Verificar WHATSAPP_TOKEN válido
- Confirmar WHATSAPP_PHONE_NUMBER_ID correcto
- Revisar conectividad a graph.facebook.com

**2. Webhook verification failed**
```
Error: Webhook Verification failed - token mismatch
```
- Verificar WHATSAPP_VERIFY_TOKEN en .env
- Confirmar token en configuración de Facebook Developer

**3. Rate limit exceeded**
```
Error: Too many requests. Please try again later.
```
- Esperar antes de reintentrar
- Ajustar RATE_LIMIT en configuración

### Debug Mode

```bash
# Activar debug detallado
FLASK_DEBUG=True LOG_LEVEL=DEBUG python app.py
```

## 🔄 Deployment

### Opción 1: Gunicorn (Recomendado)
```bash
# Instalar Gunicorn
pip install gunicorn

# Ejecutar con múltiples workers
gunicorn -w 4 -b 0.0.0.0:5000 app:main
```

### Opción 2: Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:main"]
```

### Opción 3: Servidor Web
- Configurar nginx como reverse proxy
- Usar systemd para manejo de procesos
- Implementar SSL/TLS con certbot

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📝 License

Este proyecto es parte del sistema de notificaciones WhatsApp y utiliza la biblioteca `whatsapp-python` incluida en el proyecto principal.

## 📞 Soporte

Para soporte y preguntas:
- Revisar los logs en `attendance_notifier.log`
- Usar el endpoint `/health` para diagnosticar problemas
- Ejecutar `python tests/test_webhook.py --test-errors` para verificar funcionalidad

---

**Nota**: Este sistema requiere acceso válido a WhatsApp Business API y configuración apropiada de webhooks en Facebook Developer Console.# expokossodo_whatsapp_visita
