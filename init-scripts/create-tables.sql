-- Crear tabla ejercicios si no existe
CREATE TABLE IF NOT EXISTS ejercicios (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    ejercicio VARCHAR(255),
    repeticiones JSONB,
    duracion INTEGER,
    user_id INTEGER
);
