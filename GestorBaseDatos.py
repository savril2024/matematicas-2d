import sqlite3
import hashlib
import os

# ============================================================
# GESTIÓN DE BASE DE DATOS (SQLite)
# ============================================================
class GestorBaseDatos:
    def __init__(self, db_nombre="seguridad_matematicas.db"):
        self.db_nombre = db_nombre
        self.inicializar_bd()
    
    def obtener_conexion(self):
        return sqlite3.connect(self.db_nombre)
    
    def inicializar_bd(self):
        """Crea la tabla de usuarios y un administrador por defecto si no existe"""
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        
        # Crear tabla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Crear usuario administrador por defecto (Usuario: admin, Contraseña: profe2024)
        password_hash = hashlib.sha256("profe2024".encode()).hexdigest()
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (nombre, rol, password_hash) 
            VALUES (?, ?, ?)
        ''', ('admin', 'profesor', password_hash))
        
        # Crear un usuario "Niño" con PIN simple (Usuario: niño, Contraseña: 1234)
        pin_hash = hashlib.sha256("1234".encode()).hexdigest()
        cursor.execute('''
            INSERT OR IGNORE INTO usuarios (nombre, rol, password_hash) 
            VALUES (?, ?, ?)
        ''', ('estudiante', 'alumno', pin_hash))
        
        conn.commit()
        conn.close()

    def verificar_credenciales(self, nombre, password):
        """Verifica si el usuario y la contraseña son correctos"""
        conn = self.obtener_conexion()
        cursor = conn.cursor()
        
        # Encriptamos la contraseña ingresada para compararla
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            SELECT nombre, rol FROM usuarios 
            WHERE nombre = ? AND password_hash = ?
        ''', (nombre, password_hash))
        
        resultado = cursor.fetchone()
        conn.close()
        
        return resultado  # Devuelve ('admin', 'profesor') o None si falla

# Instancia global de la BD
bd = GestorBaseDatos()