# 🚀 Guía de Deploy en Vercel

Paso a paso para desplegar de forma segura tu cotizador en Vercel.

## Prerequisitos

✅ Repo privado en GitHub
✅ Cuenta en Vercel (gratis)
✅ Backend corriendo en tu servidor

---

## Paso 1: Preparar el Código

### 1.1 Asegurar que no hay secretos

```bash
git status
# No debería aparecer .env.local
```

### 1.2 Hacer commit de archivos de seguridad

```bash
git add .gitignore .env.example SECURITY.md
git commit -m "Add security configuration"
git push origin main
```

---

## Paso 2: Crear Cuenta en Vercel

1. Ve a https://vercel.com
2. Click "Sign Up"
3. Selecciona "Continue with GitHub"
4. Autoriza Vercel

---

## Paso 3: Importar Proyecto

1. Vercel Dashboard → New Project
2. Click "Import Git Repository"
3. Busca: `davidst0215/cotizador_TDV`
4. Click Deploy

---

## Paso 4: Configurar Variables de Entorno

### IMPORTANTE: Hazlo ANTES de que termine el deploy

1. Vercel → Settings → Environment Variables
2. Agrega:

```
NEXT_PUBLIC_API_URL = https://tu-backend.com
```

Otras variables (si las necesitas):
- DB_HOST
- DB_PASSWORD
- etc.

---

## Paso 5: Despliegues Posteriores

```bash
git push origin main
# Vercel despliega automáticamente en 2-3 minutos
```

---

## Troubleshooting

### Error: "Cannot connect to backend"
- Verifica NEXT_PUBLIC_API_URL en Vercel
- Verifica que backend está activo

### Error: "Build failed"
- Ver logs en Vercel Dashboard
- Causas: dependencias faltando, errores en código

---

**Tu app estará en:** https://cotizador-tdv.vercel.app

**Más info:** Ver SECURITY.md
# Vercel Deployment Configured
