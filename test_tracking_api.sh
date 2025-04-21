#!/bin/bash
# Script súper mejorado ✨ para probar los endpoints de tracking
# y verificar cambios en la base de datos 🐘 con muchos logs y emojis!
# MODIFICADO: Se eliminó el pipe a JQ para ver la salida cruda de la API.

# --- ⚙️ CONFIGURACIÓN ---
API_BASE="http://localhost:5050"
# 🔑 Token JWT de ejemplo (¡asegúrate de usar uno válido!)
API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJtaWd1ZWw2OTZtZ0BnbWFpbC5jb20iLCJuYW1lIjoiTWlndWVsIEdvbnpcdTAwZTFsZXoiLCJleHAiOjE3NDc0MzY1NDcsImlhdCI6MTc0NDg0NDU0NywidHlwZSI6ImFjY2VzcyJ9.eKvxnLqe49hLBuiU6DzWYI00G5i3v7sQwRwe0GgKBCU"
TODAY=$(date +%Y-%m-%d)

# --- 🐘 CONFIGURACIÓN DE BASE DE DATOS (según archivo .env) ---
DB_NAME="gymdb"
DB_USER="postgres"
DB_PASSWORD="NuevaBabilonia9317@" # Considera usar variables de entorno o un método más seguro
DB_HOST="localhost"      # 🐳 Cambia si NO usas Docker
DB_PORT="5438"
DB_SCHEMA="nutrition"    # Esquema para daily_tracking

# --- 👤 USER ID desde token para consultas a BD ---
USER_ID_FROM_TOKEN="1"

# --- 🎨 Colores y Emojis ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
START="🚀"
SUCCESS="✅"
FAIL="❌"
WARN="⚠️"
INFO="ℹ️"
CHECK="🔍"
SAVE="💾"
UPDATE="🔄"
GET="📥"
SEND="📤"
DB="🐘"
API="☁️"
DATE="📅"
WEEK="🗓️"
SUMMARY="📊"
USER="👤"
JSON_EMOJI="📄"
TOOL="🛠️"
EYES="👀"
WAVE="👋"
OUTPUT="➡️" # Para indicar salida cruda

echo -e "${BLUE}${START} === Iniciando Testeo Intenso de Nutrition Tracking API === ${START}${NC}"
echo -e "${INFO} ${DATE} Usando Fecha: ${CYAN}$TODAY${NC}"
echo -e "${INFO} ${API} Usando API Base: ${CYAN}$API_BASE${NC}"
echo -e "${INFO} ${USER} Usando User ID (BD): ${CYAN}$USER_ID_FROM_TOKEN${NC}"
echo -e "${INFO} ${DB} Usando DB Host: ${CYAN}$DB_HOST${NC} (🐳 Asegúrate que sea el nombre del servicio si usas Docker)"
echo -e "${YELLOW}--- ${WARN} AVISOS ${WARN} ---${NC}"
echo -e "${YELLOW}   - Asegúrate de que el backend esté corriendo (${API} FastAPI/Uvicorn).${NC}"
echo -e "${YELLOW}   - Asegúrate de que exista un usuario con google_id='${USER_ID_FROM_TOKEN}' en la tabla 'users'.${NC}"
echo -e "${YELLOW}   - ¡El token JWT (${API_TOKEN:0:10}...) debe ser válido!${NC}"
echo -e "${YELLOW}--------------------${NC}"
echo ""

# --- 🛠️ Verificación de Herramientas ---
echo -e "${BLUE}${TOOL} Verificando herramientas necesarias...${NC}"
# Verificar si psql está instalado
if ! command -v psql &> /dev/null
then
    echo -e "${YELLOW}${WARN} Aviso: 'psql' no está instalado.${NC} ${DB} No se podrán verificar datos directamente en la base de datos."
    HAS_PSQL=false
else
     echo -e "${GREEN}${SUCCESS} 'psql' está instalado.${NC} ${DB} Se verificarán los datos en la base de datos."
    HAS_PSQL=true
fi
echo -e "${BLUE}----------------------------${NC}"
echo ""

# --- 🐘 Función para Consultar la Base de Datos ---
check_db() {
    local check_description="$1" # Descripción opcional para el log
    echo -e "${MAGENTA}${CHECK} Iniciando verificación en BD: ${CYAN}${check_description}${NC}"

    if [ "$HAS_PSQL" = true ]; then
        echo -e "${BLUE}${DB} Consultando ${DB_NAME} para user_id=${USER_ID_FROM_TOKEN} y fecha=${TODAY}...${NC}"
        # Ejecutar psql y capturar salida y código de retorno
        psql_output=$(PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        SELECT id, user_id, tracking_date,
               completed_meals::text, -- Convertir JSON a texto para verlo mejor
               calorie_note,
               actual_calories, excess_deficit,
               created_at, updated_at
        FROM $DB_SCHEMA.daily_tracking
        WHERE user_id = '$USER_ID_FROM_TOKEN' AND tracking_date = '$TODAY';" 2>&1) # Redirigir stderr a stdout
        psql_exit_code=$?

        if [ $psql_exit_code -ne 0 ]; then
            echo -e "${RED}${FAIL} Error al consultar la base de datos (Código: $psql_exit_code).${NC}"
            echo -e "${RED}   Mensaje de psql: ${psql_output}${NC}"
            echo -e "${YELLOW}${WARN}   Verifica la configuración de conexión (HOST: $DB_HOST, PORT: $DB_PORT, USER: $DB_USER, DB: $DB_NAME).${NC}"
            echo -e "${YELLOW}${WARN}   Comprueba también que la tabla '$DB_SCHEMA.daily_tracking' existe.${NC}"
            echo -e "${YELLOW}${WARN}   🐳 Si estás ejecutando fuera de Docker, ¿es DB_HOST='localhost' correcto?${NC}"
        else
            echo -e "${GREEN}${SUCCESS} Consulta a la BD exitosa.${NC}"
            echo -e "${DB} Resultado:"
            echo -e "${CYAN}$psql_output${NC}" # Mostrar la salida de psql
            # Comprobar si devolvió filas (esto es una heurística basada en la salida de psql)
            if echo "$psql_output" | grep -q "(0 rows)"; then
                echo -e "${YELLOW}${EYES} La consulta no devolvió filas para hoy.${NC}"
            elif echo "$psql_output" | grep -q "rows)"; then
                 echo -e "${GREEN}${EYES} ¡La consulta devolvió filas!${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}${WARN} No se puede verificar en base de datos porque psql no está instalado.${NC}"
    fi
     echo -e "${MAGENTA}------------------------------------${NC}"
}

# --- 🚦 Inicio de las Pruebas de Endpoints ---

# 1. 📥 Test GET tracking for today (antes de guardar nada)
echo -e "\n${GREEN}1. ${GET} Probando GET /api/nutrition/tracking/day/$TODAY (ANTES de guardar):${NC}"
echo -e "${INFO}   Esperado: 404 Not Found o JSON con 'tracking: null' si es la primera vez."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X GET "$API_BASE/api/nutrition/tracking/day/$TODAY" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 1 ---${NC}"

# Verificar BD antes de guardar
check_db "Estado ANTES de guardar"

# 2. 📤 Test saving tracking data
echo -e "\n${GREEN}2. ${SAVE} Probando POST /api/nutrition/tracking (para GUARDAR datos de hoy):${NC}"
echo -e "${INFO}   Enviando datos iniciales..."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X POST "$API_BASE/api/nutrition/tracking" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_date": "'$TODAY'",
    "completed_meals": {
      "Desayuno": true,
      "Almuerzo": true,
      "Comida": false,
      "Merienda": false,
      "Cena": false,
      "Otro": false
    },
    "calorie_note": "Prueba inicial desde script BASH con emojis!",
    "actual_calories": 1950,
    "excess_deficit": -270
  }' # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 2 ---${NC}"

# Verificar BD después de guardar
check_db "Estado DESPUÉS de guardar (Paso 2)"

# 3. 📥 Test GET tracking for today again (debería devolver datos)
echo -e "\n${GREEN}3. ${GET} Probando GET /api/nutrition/tracking/day/$TODAY (DESPUÉS de guardar):${NC}"
echo -e "${INFO}   Esperado: JSON con los datos guardados en el paso 2 (o error si el paso 2 falló)."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X GET "$API_BASE/api/nutrition/tracking/day/$TODAY" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 3 ---${NC}"

# 4. 📤 Test update tracking data (mismo día, diferentes datos)
echo -e "\n${GREEN}4. ${UPDATE} Probando POST /api/nutrition/tracking (para ACTUALIZAR datos de hoy):${NC}"
echo -e "${INFO}   Enviando datos actualizados..."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X POST "$API_BASE/api/nutrition/tracking" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tracking_date": "'$TODAY'",
    "completed_meals": {
      "Desayuno": true,
      "Almuerzo": true,
      "Comida": true,
      "Merienda": true,
      "Cena": false,
      "Otro": true
    },
    "calorie_note": "Actualizado desde script BASH con emojis! 🚀",
    "actual_calories": 2300,
    "excess_deficit": 80
  }' # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 4 ---${NC}"

# Verificar BD después de actualizar
check_db "Estado DESPUÉS de actualizar (Paso 4)"

# 5. 📥 Test GET tracking for today again (debería devolver datos actualizados)
echo -e "\n${GREEN}5. ${GET} Probando GET /api/nutrition/tracking/day/$TODAY (DESPUÉS de actualizar):${NC}"
echo -e "${INFO}   Esperado: JSON con los datos actualizados en el paso 4 (o error)."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X GET "$API_BASE/api/nutrition/tracking/day/$TODAY" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 5 ---${NC}"

# 6. 🗓️ Test getting weekly tracking
echo -e "\n${GREEN}6. ${WEEK} Probando GET /api/nutrition/tracking/week (para datos semanales):${NC}"
echo -e "${INFO}   Esperado: Lista de seguimientos diarios para la semana actual (o error)."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X GET "$API_BASE/api/nutrition/tracking/week" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 6 ---${NC}"

# 7. 📊 Test getting weekly summary
echo -e "\n${GREEN}7. ${SUMMARY} Probando GET /api/nutrition/tracking/summary (para resumen semanal):${NC}"
echo -e "${INFO}   Esperado: Resumen calculado de la semana actual (o error)."
echo -e "${OUTPUT} Salida Cruda de API:"
curl -s -w "\n${INFO}   HTTP Status Code: %{http_code}\n" -X GET "$API_BASE/api/nutrition/tracking/summary" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" # <-- SIN | jq .
echo -e "\n${YELLOW}--- Fin Paso 7 ---${NC}"

# 8. 🐘 Consulta SQL adicional para ver todos los registros de tracking del usuario
if [ "$HAS_PSQL" = true ]; then
    echo -e "\n${BLUE}8. ${DB} Consulta SQL para ver TODOS los registros de tracking del usuario ${USER_ID_FROM_TOKEN}:${NC}"
    PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT id, user_id, tracking_date,
           completed_meals::text as completed_meals_json, -- Mostrar JSON como texto
           actual_calories,
           excess_deficit,
           created_at, updated_at
    FROM $DB_SCHEMA.daily_tracking
    WHERE user_id = '$USER_ID_FROM_TOKEN'
    ORDER BY tracking_date DESC LIMIT 10;" 2>/dev/null # Limitar a 10 para no saturar
    echo -e "${YELLOW}--- Fin Paso 8 ---${NC}"
fi

# 9. 📄 Verificar que la deserialización del campo JSON completed_meals funciona (Repetido para énfasis)
echo -e "\n${GREEN}9. ${JSON_EMOJI} Verificando nuevamente el formato del campo 'completed_meals' en la BD para HOY:${NC}"
if [ "$HAS_PSQL" = true ]; then
    PGPASSWORD="$DB_PASSWORD" psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT id, user_id, tracking_date,
           completed_meals::text as completed_meals_json, -- Convertir JSON a texto
           jsonb_typeof(completed_meals) as json_type, -- Verificar tipo JSON en DB
           created_at
    FROM $DB_SCHEMA.daily_tracking
    WHERE user_id = '$USER_ID_FROM_TOKEN' AND tracking_date = '$TODAY';" 2>/dev/null
    echo -e "${YELLOW}--- Fin Paso 9 ---${NC}"
fi

echo -e "\n${BLUE}${WAVE} === Pruebas Completadas === ${WAVE}${NC}"
echo -e "${INFO} ${EYES} Verifica los siguientes puntos:"
echo -e "   1. ${OUTPUT} Revisa la 'Salida Cruda de API' después de cada llamada ${API}. ¿Es HTML? ¿Texto de error?"
echo -e "   2. ${INFO} Comprueba los 'HTTP Status Code' después de cada llamada. ¿Son 200 OK, 201 Created, o son errores 4xx/5xx?"
echo -e "   3. ${DB} Que las consultas a la base de datos (pasos con ${DB}) muestren filas DESPUÉS de los POST (Pasos 2 y 4) si la API funcionó."
echo -e "   4. ${JSON_EMOJI} Que el campo 'completed_meals_json' (Pasos 8 y 9) se vea como un JSON válido si se guardó algo."
echo ""
echo -e "${RED}${FAIL} ¡SI LA SALIDA CRUDA ES UN ERROR (HTML o texto), EL PROBLEMA ESTÁ EN EL BACKEND!${NC}"
echo -e "${YELLOW}   - ${FAIL} ¡¡REVISA LOS LOGS DE FastAPI/Uvicorn AHORA!! Busca Tracebacks de Python.${NC}"
echo -e "${YELLOW}   - ${FAIL} Asegúrate que la configuración de BD en el .env del backend es correcta (¡especialmente DB_HOST!).${NC}"
echo -e "${YELLOW}   - ${FAIL} Verifica el token JWT y la lógica de autenticación/autorización.${NC}"
echo ""
echo -e "${GREEN}¡Ánimo! Con la salida cruda y los logs del backend lo encontrarás. 💪${NC}"