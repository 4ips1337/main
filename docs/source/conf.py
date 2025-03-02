project = 'main'
copyright = '2025, Daniil'
author = 'Daniil'


extensions = []

templates_path = ['_templates']
exclude_patterns = []


html_theme = 'alabaster'
html_static_path = ['_static']

# Додаємо розширення для автодокументації
extensions = ['sphinx.ext.autodoc', 
              'sphinx.ext.napoleon',  # Для підтримки Google/Numpy style docstrings
              'sphinx_autodoc_typehints']  # Показує типи аргументів у документації

# Тема для красивої документації
html_theme = 'sphinx_rtd_theme'

# Вказуємо шляхи
templates_path = ['_templates']
exclude_patterns = []

# Код для коректного пошуку модулів
import os
import sys
sys.path.insert(0, os.path.abspath('..'))