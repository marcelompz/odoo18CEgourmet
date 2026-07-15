# Migración Controlada de odoo9049 a Configuración Optimizada

## 📋 Resumen de la Migración

Esta migración permite aplicar las mejoras identificadas en la auditoría de `odoo9049` manteniendo la compatibilidad con los datos existentes y minimizando el tiempo de inactividad.

## 🔍 Comparación de Configuraciones

### Configuración Actual (odoo9049)
- **Sin health checks**: No hay monitoreo de salud de servicios
- **Dependencias básicas**: Instalación simple de paquetes Python
- **Entrypoint simple**: Script básico sin validaciones
- **Volúmenes bind mounts**: Usa bind mounts directos del sistema de archivos
- **Red por defecto**: Usa la red default de Docker
- **Sin logging estructurado**: Logs básicos sin colores ni timestamp

### Configuración Optimizada (odoo9049-migracion-test)
- **✅ Health checks completos**: Para PostgreSQL y Odoo
- **✅ Dependencias optimizadas**: Con herramientas de debugging (curl, vim-tiny, jq)
- **✅ Entrypoint robusto**: Con validaciones, espera inteligente y logging colorizado
- **✅ Volúmenes Docker nativos**: Usa volúmenes Docker externos (mismo nombre)
- **✅ Red dedicada**: Red bridge con subnet 172.24.0.0/16 (sin conflictos)
- **✅ Logging estructurado**: Logs con colores, timestamps y niveles

## 🚀 Mejoras Implementadas

1. **Health Checks**
   - PostgreSQL: `pg_isready -U odoo -d postgres`
   - Odoo: `curl -f http://localhost:8069/web/health`
   - Dependencias condicionales: `condition: service_healthy`

2. **Entrypoint Mejorado**
   - Validación de variables de entorno críticas
   - Espera inteligente para PostgreSQL (30 reintentos)
   - Verificación automática de dependencias Python
   - Logging colorizado con niveles (INFO, WARN, ERROR, SUCCESS)
   - Detección de addons y conteo de módulos

3. **Dockerfile Optimizado**
   - Herramientas de debugging: curl, vim-tiny, jq, postgresql-client
   - Dependencias Python completas pre-instaladas
   - Health check integrado en la imagen
   - Directorio para scripts personalizados

4. **Seguridad y Mantenibilidad**
   - Configuración read-only (`./config:/etc/odoo:ro`)
   - Variables de entorno organizadas
   - Red dedicada sin conflictos
   - Restart policies optimizadas

## 📊 Datos y Compatibilidad

### Volúmenes Preservados
La migración mantiene los mismos volúmenes Docker:
- **Base de datos**: `odoo9049_odoo-db-data` → Datos de PostgreSQL
- **Datos web**: `odoo9049_odoo-web-data` → Datos de Odoo (filestore)

### Configuración Mantenida
- **Puertos**: 9049 (web), 5771 (db) - mismos que la configuración original
- **Addons**: Mismas rutas de addons personalizados
- **Variables de entorno**: Compatibilidad total con el archivo `.env` existente

## 🛠️ Proceso de Migración Paso a Paso

### Fase 1: Preparación (Sin Interrupción)
```bash
# 1. Verificar estado actual
cd /opt/odoo
docker ps -a --filter "name=odoo_web_9049" --format "table {{.Names}}\t{{.Status}}"

# 2. Backup de configuración actual
cp -r odoo9049 odoo9049-backup-$(date +%Y%m%d)

# 3. Verificar volúmenes
docker volume ls | grep odoo9049

# 4. Inspeccionar datos de volúmenes (opcional)
docker run --rm -v odoo9049_odoo-db-data:/data alpine ls -la /data/
```

### Fase 2: Migración Controlada (Downtime Controlado)
```bash
# 1. Detener servicios actuales
cd /opt/odoo/odoo9049
docker compose down

# 2. Preparar configuración optimizada
cd /opt/odoo/odoo9049-migracion-test

# 3. Copiar archivos optimizados
cp docker-compose.yml.optimizado docker-compose.yml
cp Dockerfile.optimizado Dockerfile
cp /opt/odoo/odoo18-docker-compose/entrypoint.sh .

# 4. Actualizar .env para migración (opcional)
# Mantener el archivo .env original

# 5. Iniciar con configuración optimizada
docker compose up -d

# 6. Monitorear inicio
docker compose logs -f --tail=50
```

### Fase 3: Verificación Post-Migración
```bash
# 1. Verificar health checks
docker compose ps
docker inspect --format='{{.State.Health.Status}}' odoo_web_9049
docker inspect --format='{{.State.Health.Status}}' db_odoo_5771

# 2. Verificar logs de inicio
docker compose logs web | grep -E "(INFO|WARN|ERROR|SUCCESS)" | tail -20

# 3. Verificar acceso a Odoo
curl -f http://localhost:9049/web/health

# 4. Verificar datos preservados
docker compose exec db psql -U odoo -d postgres -c "\l"
```

### Fase 4: Rollback (Si es necesario)
```bash
# 1. Detener servicios optimizados
cd /opt/odoo/odoo9049-migracion-test
docker compose down

# 2. Restaurar configuración original
cd /opt/odoo/odoo9049
docker compose up -d

# 3. Verificar restauración
docker ps -a --filter "name=odoo_web_9049" --format "table {{.Names}}\t{{.Status}}"
```

## 🧪 Pruebas Recomendadas

### Prueba 1: Health Checks
```bash
# Simular health check failure
docker stop db_odoo_5771
# Esperar 2 minutos
docker start db_odoo_5771
# Verificar que health check se recupera
docker inspect --format='{{.State.Health.Status}}' odoo_web_9049
```

### Prueba 2: Dependencias Python
```bash
# Verificar que todas las dependencias están instaladas
docker compose exec web python3 -c "
import dropbox, pyncclient, boto3, paramiko, openpyxl, psycopg2, redis, requests, gevent
print('Todas las dependencias Python funcionan correctamente')
"
```

### Prueba 3: Addons
```bash
# Verificar que los addons se detectan correctamente
docker compose logs web | grep "Directorio de addons"
docker compose logs web | grep "Módulos encontrados"
```

### Prueba 4: Performance
```bash
# Verificar uso de recursos
docker stats odoo_web_9049 db_odoo_5771 --no-stream

# Verificar logs de performance
docker compose logs web | grep -i "worker\|memory\|limit"
```

## ⚠️ Consideraciones Importantes

### 1. **Tiempo de Inactividad**
- **Estimado**: 5-10 minutos para migración completa
- **Principal causa**: Reconstrucción de imagen Docker con nuevas dependencias
- **Mitigación**: Cache de Docker layers acelera reconstrucción

### 2. **Espacio en Disco**
- **Nueva imagen**: ~200MB adicionales (herramientas de debugging)
- **Volúmenes**: Sin cambios (mismos volúmenes)
- **Backup**: ~500MB para backup de configuración

### 3. **Compatibilidad**
- **Totalmente compatible** con datos existentes
- **Mismos puertos** (9049, 5771)
- **Mismas variables** de entorno
- **Mismos addons** y configuraciones

### 4. **Riesgos**
- **Bajo riesgo**: Solo cambios en contenedores, no en datos
- **Rollback sencillo**: Revertir a configuración anterior
- **Monitoreo mejorado**: Health checks detectan problemas temprano

## 📈 Beneficios de la Migración

### 1. **Confiabilidad Mejorada**
- Health checks automáticos
- Reinicios automáticos en caso de fallos
- Monitoreo proactivo de servicios

### 2. **Mantenibilidad**
- Logging estructurado para troubleshooting
- Herramientas de debugging incluidas
- Configuración organizada y documentada

### 3. **Performance**
- Dependencias pre-instaladas (menos tiempo de inicio)
- Configuración optimizada para producción
- Health checks ligeros y eficientes

### 4. **Seguridad**
- Configuración read-only
- Redes aisladas
- Mejor manejo de variables de entorno

## 📞 Soporte y Troubleshooting

### Problemas Comunes y Soluciones

#### 1. **Health Check Fails**
```bash
# Verificar logs de PostgreSQL
docker compose logs db

# Probar conexión manualmente
docker compose exec db pg_isready -U odoo -d postgres

# Verificar variables de entorno
docker compose exec web env | grep PG
```

#### 2. **Dependencias Python Faltantes**
```bash
# Reinstalar dependencias manualmente
docker compose exec web pip install --user --upgrade dropbox pyncclient boto3 paramiko

# Verificar instalación
docker compose exec web python3 -c "import dropbox; print('OK')"
```

#### 3. **Addons No Detectados**
```bash
# Verificar rutas de montaje
docker compose exec web ls -la /mnt/extra-addons-customize/

# Verificar permisos
docker compose exec web ls -la /opt/odoo/odoo9049-migracion-test/addons/
```

#### 4. **Performance Issues**
```bash
# Ajustar workers en config/odoo.conf
# workers = 4  # Para 2 CPU cores

# Verificar límites de memoria
docker stats odoo_web_9049 db_odoo_5771
```

## ✅ Checklist de Migración Exitosa

- [ ] Backup completo de configuración actual
- [ ] Volúmenes verificados y accesibles
- [ ] Servicios originales detenidos correctamente
- [ ] Configuración optimizada aplicada
- [ ] Health checks pasando (healthy status)
- [ ] Logs sin errores críticos
- [ ] Acceso a Odoo funcionando (http://localhost:9049)
- [ ] Datos verificados y accesibles
- [ ] Addons detectados y cargados
- [ ] Performance dentro de parámetros esperados
- [ ] Plan de rollback documentado y probado

## 🎯 Conclusión

Esta migración controlada aplica **todas las mejoras identificadas** en la auditoría manteniendo **compatibilidad total** con los datos y configuraciones existentes. El proceso está **documentado paso a paso** con **procedimientos de rollback** para garantizar una transición segura.

**Beneficio principal**: Obtener todas las ventajas de la configuración optimizada (monitoreo, confiabilidad, mantenibilidad) **sin pérdida de datos** y con **tiempo de inactividad mínimo**.

---
*Documentación de migración generada: $(date)*  
*Versión optimizada basada en auditoría de odoo9049*