#!/bin/sh
# Script simple para eliminar logs sin emojis

# Definir lista de emojis
EMOJIS="✅ ❌ ⚠️ 🚦 🔄 🔒 🍪 📋 ➡️ 🔍 👤 🤖 🔀 🏁 ⏰ 🌍 💥 🏆 ⚡ 🔑 🛑 🚀 🔥 >>>"

# Función para procesar archivos
process_file() {
    file="$1"
    temp_file=$(mktemp)
    
    # Procesar el archivo
    while IFS= read -r line; do
        # Bandera para determinar si la línea debe mantenerse
        keep_line=1
        
        # Verificar si es un log sin emoji
        if echo "$line" | grep -q "logger\.\(info\|debug\)"; then
            for emoji in $EMOJIS; do
                if echo "$line" | grep -q "$emoji"; then
                    keep_line=0
                    break
                fi
            done
            
            # Si no tiene ningún emoji, omitir la línea
            if [ "$keep_line" -eq 1 ]; then
                continue
            fi
        fi
        
        # Mantener la línea
        echo "$line" >> "$temp_file"
    done < "$file"
    
    # Reemplazar el archivo original con el temporal
    mv "$temp_file" "$file"
    
    echo "Procesado: $file"
}

# Procesar archivos de logs
find ./back_end -type f -name "*.py" | while read -r file; do
    if grep -q "logger\.\(info\|debug\)" "$file"; then
        process_file "$file"
    fi
done

# Función para eliminar print statements de debug
process_debug_prints() {
    file="$1"
    temp_file=$(mktemp)
    
    # Procesar el archivo
    while IFS= read -r line; do
        # Comprobar si la línea contiene un print statement de debug
        if ! echo "$line" | grep -q "print.*DEBUG"; then
            # Mantener la línea
            echo "$line" >> "$temp_file"
        fi
    done < "$file"
    
    # Reemplazar el archivo original con el temporal
    mv "$temp_file" "$file"
    
    echo "Eliminados prints de debug en: $file"
}

# Procesar archivos con print statements de debug
find ./back_end -type f -name "*.py" | while read -r file; do
    if grep -q "print.*DEBUG" "$file"; then
        process_debug_prints "$file"
    fi
done

echo "¡Limpieza completada!"