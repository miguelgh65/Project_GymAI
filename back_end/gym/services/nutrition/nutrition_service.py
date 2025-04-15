# back_end/gym/services/nutrition_service.py
# Este archivo importa y expone todas las funciones relacionadas con nutrición

# Importar funciones de ingredientes
from .ingredient_service import (
    get_ingredient,
    create_ingredient,
    list_ingredients,
    update_ingredient,
    delete_ingredient,
    check_ingredient_exists
)

# Importar funciones de comidas
from .meal_service import (
    get_meal,
    create_meal,
    list_meals,
    update_meal,
    delete_meal,
    check_meal_exists,
    add_ingredient_to_meal,
    get_meal_ingredients,
    update_meal_ingredient,
    delete_meal_ingredient,
    recalculate_meal_macros
)

# Importar funciones de planes de comida
from .meal_plans_service import (
    create_meal_plan,
    list_meal_plans,
    get_meal_plan,
    update_meal_plan,
    delete_meal_plan
)

# Importar funciones de elementos de planes de comida
from .meal_plan_items_service import (
    add_meal_to_plan,
    get_meal_plan_items,
    get_meal_plan_item,
    update_meal_plan_item,
    delete_meal_plan_item
)