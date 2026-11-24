from langchain.tools import tool

@tool
def get_planting_data(field_id: str, season: str) -> dict:
    """Obtiene los datos de siembra para un campo y temporada especificos."""
    return {
        "field_id": field_id,
        "season": season,
        "crop": "Maiz",
        "planting_date": "2024-10-15",
        "hybrid": "DKB 72-70",
        "population": 72000,
        "row_spacing": 52.5,
    }

@tool
def get_harvest_data(field_id: str, season: str) -> dict:
    """Obtiene los datos de cosecha y rendimiento para un campo y temporada especificos."""
    return {
        "field_id": field_id,
        "season": season,
        "crop": "Maiz",
        "harvest_date": "2025-03-20",
        "avg_yield": 145.8,
        "moisture": 14.2,
        "total_production": 2187.0,
    }

@tool
def get_field_boundaries(field_id: str) -> dict:
    """Obtiene los limites y datos geograficos de un campo especifico."""
    return {
        "field_id": field_id,
        "area_hectares": 15.0,
        "geometry_type": "Polygon",
        "soil_types": ["Franco limoso", "Franco arenoso"],
    }