# 🔐 Guía de Seguridad - Cotizador TDV

## Índice
1. [Configuración Local Segura](#configuración-local-segura)
2. [Protección de Credenciales](#protección-de-credenciales)
3. [Variables de Entorno](#variables-de-entorno)
4. [Deploy en Vercel](#deploy-en-vercel)

---

## Configuración Local Segura

### 1. Crear archivo `.env.local` (NO se sube a Git)

```bash
cp .env.example .env.local
nano .env.local
```

**⚠️ IMPORTANTE:**
- `.env.local` está en `.gitignore`
- NUNCA hagas commit de `.env.local`
- Cada desarrollador tiene su propio `.env.local`

---

## Protección de Credenciales

### ✅ Ubicación SEGURA:
- Variables de entorno en `.env.local` (local)
- Vercel Secrets en Vercel Dashboard (producción)

### ❌ NUNCA en:
```javascript
// ❌ MAL - Hardcoded
const password = "mi_contrasena_123";
const dbUrl = "postgresql://user:pass@localhost/db";

// ✅ BIEN - Variables de entorno
const password = process.env.DB_PASSWORD;
const dbUrl = process.env.DATABASE_URL;
```

---

## Variables de Entorno

### Para Desarrollo Local

```bash
# Archivo: .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
DB_HOST=localhost
DB_PORT=5432
DB_USER=dev_user
DB_PASSWORD=dev_password_temporal
NODE_ENV=development
```

### Para Producción (Vercel)

En Vercel Dashboard → Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL=https://api.tu-dominio.com
DB_HOST=host-produccion
DB_USER=prod_user
DB_PASSWORD=[contraseña fuerte]
NODE_ENV=production
```

---

## Deploy en Vercel

### Seguridad antes de push:

```bash
# Verificar no hay secretos
git status | grep ".env.local"  # No debería aparecer

# Verificar no hay passwords
git diff HEAD | grep -i "password"  # No debería aparecer

# Verificar certificados SSL
git status | grep -E "\.pem|\.key"  # No debería aparecer
```

### Variables en Vercel (NO en Git):

- Credenciales de BD
- URLs de backend
- Certificados SSL (en base64)
- API Keys
- Tokens

---

## Checklist de Seguridad

Antes de hacer push a GitHub:

- [ ] ¿`.env.local` está en `.gitignore`?
- [ ] ¿No hay `.env.local` en los cambios?
- [ ] ¿No hay certificados `.pem` o `.key`?
- [ ] ¿No hay hardcoded passwords?
- [ ] ¿`.env.example` tiene placeholders, NO valores reales?

Antes de desplegar a Vercel:

- [ ] ¿Agregaste variables en Vercel Dashboard?
- [ ] ¿Las credenciales de Vercel son diferentes a local?
- [ ] ¿`NEXT_PUBLIC_API_URL` apunta a producción?
- [ ] ¿El SSL del backend está activo?

---

**Para más info, ver:** DEPLOY_VERCEL.md
