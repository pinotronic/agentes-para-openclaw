#!/usr/bin/env python3
"""Adapter para proyectos Python FastAPI simples.

Este adaptador detecta proyectos Python FastAPI simples y provee comandos de calidad.
"""

import os
from pathlib import Path


class PythonFastAPIAdapter:
    """Adapter para proyectos Python FastAPI."""
    
    id = "python-fastapi-simple"
    
    @staticmethod
    def detect(project: Path) -> bool:
        """Detecta si el proyecto es Python FastAPI simple."""
        return (project / "backend" / "app" / "main.py").exists()
    
    @staticmethod
    def describe() -> str:
        """Describe el tipo de proyecto."""
        return "Python FastAPI simple (backend en backend/app/)"
    
    @staticmethod
    def commands(project: Path) -> list:
        """Devuelve comandos de calidad para Python FastAPI."""
        return [
            ["python", "-m", "pytest", "backend/tests/", "-v"],
            ["flake8", "backend/"],
        ]


ALL_ADAPTERS = [PythonFastAPIAdapter]
