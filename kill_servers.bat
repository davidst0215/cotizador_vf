@echo off
echo Matando todos los procesos en puerto 8000...
taskkill /F /PID 15384
taskkill /F /PID 17772
taskkill /F /PID 15500
taskkill /F /PID 23168
taskkill /F /PID 19592
taskkill /F /PID 24668
taskkill /F /PID 4752
taskkill /F /PID 12756
taskkill /F /PID 13304
echo Procesos eliminados
timeout /t 2
