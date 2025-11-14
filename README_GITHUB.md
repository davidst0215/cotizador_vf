# 💰 Sistema Cotizador TDV

Sistema de cotización basado en metodología WIP para la industria textil.

**Repo privado.** Uso autorizado solo.

---

## 🚀 Quick Start Local

```bash
# 1. Instalar dependencias
npm install

# 2. Configurar variables
cp .env.example .env.local
nano .env.local  # Edita con tus valores

# 3. Ejecutar
npm run dev
```

**Frontend:** http://localhost:3000
**Backend:** http://localhost:8000

---

## 🔐 Seguridad

⚠️ Lee [`SECURITY.md`](./SECURITY.md) antes de trabajar.

**Puntos clave:**
- `.env.local` nunca en Git
- Credenciales en variables de entorno
- Certificados SSL protegidos
- Push review: `BEFORE_PUSH.md` checklist

---

## 🚢 Deploy

Ver [`DEPLOY_VERCEL.md`](./DEPLOY_VERCEL.md) para guía paso a paso.

**Deploy automático:** Push a main → Vercel despliega en 2-3 min

---

## 📁 Estructura

```
├── frontend/          # Next.js (en desarrollo)
├── backend/          # API (referencia)
├── .env.example      # Variables template
├── SECURITY.md       # Guía de seguridad ⭐
├── DEPLOY_VERCEL.md  # Guía de deployment ⭐
└── vercel.json       # Config Vercel
```

---

## ⚡ Rápido

- **Desarrollo:** Sin cambios a producción
- **Seguridad:** Credenciales en Vercel, código en Git
- **Deploy:** 2-3 minutos automático
- **SSL:** Vercel + tu backend con HTTPS

---

Para colaboradores: Contacta a David para acceso al repo privado.
