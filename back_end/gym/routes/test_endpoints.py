# back_end/gym/routes/test_endpoints.py
from fastapi import APIRouter, Request
import psycopg2
import json

from ..config import DB_CONFIG

router = APIRouter(tags=["test"])

@router.get("/api/test/meal-plans-db-check")
async def test_meal_plans_db():
    """Endpoint para verificar planes de comida directamente en la BD"""
    results = {"success": False}
    conn = None
    cur = None
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO nutrition, public")
        
        # Verificar si existe la tabla
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'nutrition' 
                AND table_name = 'meal_plans'
            )
        """)
        table_exists = cur.fetchone()[0]
        results["table_exists"] = table_exists
        
        if table_exists:
            # Contar planes
            cur.execute("SELECT COUNT(*) FROM nutrition.meal_plans")
            count = cur.fetchone()[0]
            results["plans_count"] = count
            
            # Obtener todos los planes
            cur.execute("""
                SELECT id, user_id, plan_name, start_date, end_date, 
                      description, is_active, created_at, updated_at 
                FROM nutrition.meal_plans 
                ORDER BY created_at DESC LIMIT 10
            """)
            columns = [col[0] for col in cur.description]
            plans = []
            for row in cur.fetchall():
                plan = dict(zip(columns, row))
                # Convertir fechas a string para JSON
                for k, v in plan.items():
                    if isinstance(v, (datetime.date, datetime.datetime)):
                        plan[k] = v.isoformat()
                plans.append(plan)
            
            results["db_plans"] = plans
        
        results["success"] = True
        
    except Exception as e:
        results["error"] = str(e)
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    
    return results