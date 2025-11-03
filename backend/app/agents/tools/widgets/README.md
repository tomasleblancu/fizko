# ChatKit Widgets

Rich UI components for agent responses using OpenAI's ChatKit SDK.

## 📁 Structure

```
widgets/
├── README.md                    # This file
├── __init__.py                  # Main exports
│
├── builders/                    # Widget builder functions
│   ├── __init__.py              # Builder exports
│   ├── tax_calculation.py       # ✅ Tax calculation breakdown widget (284 lines)
│   ├── document_detail.py       # ✅ Document detail widget (321 lines)
│   └── person_confirmation.py   # ✅ Person confirmation widget (383 lines)
│
├── tax_widget_tools.py          # Agent tools using tax widgets
├── payroll_widget_tools.py      # Agent tools using payroll widgets
└── widgets.py                   # Compatibility layer (re-exports from builders/)
```

## 🎯 Design Principles

### Separation of Concerns
- **Builders** (`builders/`): Pure functions that create widget structures
- **Tools** (`*_widget_tools.py`): Agent-facing tools that use builders

### Modularity
Each widget type has its own module with:
- `create_*_widget()` - Main widget builder
- `*_widget_copy_text()` - Plain text fallback

### Domain Organization
Widgets are grouped by business domain:
- **Tax** - Tax calculations, F29, documents
- **Payroll** - Employee management, confirmations
- **Documents** - Document details, tracking

## 📦 Usage

### Importing Widgets

```python
from app.agents.tools.widgets import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
)

# Create widget
widget = create_tax_calculation_widget(
    iva_collected=1000000,
    iva_paid=500000,
    previous_month_credit=None,
    monthly_tax=500000,
    period="Octubre 2025",
)
```

### Using in UI Tools

```python
from app.agents.ui_tools.core import UIToolResult
from app.agents.tools.widgets import (
    create_tax_calculation_widget,
    tax_calculation_widget_copy_text,
)

# In your UI Tool process() method
widget = create_tax_calculation_widget(...)
widget_copy_text = tax_calculation_widget_copy_text(...)

return UIToolResult(
    success=True,
    context_text=context_text,
    widget=widget,
    widget_copy_text=widget_copy_text,
)
```

## ✅ Completed Modules

### `builders/tax_calculation.py` (284 lines)
- ✅ Fully extracted and modularized
- ✅ Supports PPM, Retención, Impuesto Trabajadores
- ✅ Comprehensive docstrings and type hints
- ✅ Fallback text implementation

### `builders/document_detail.py` (321 lines)
- ✅ Fully extracted and modularized
- ✅ Sales and purchase document support
- ✅ Contact information display
- ✅ SII tracking ID support
- ✅ Status badge with color coding

### `builders/person_confirmation.py` (383 lines)
- ✅ Fully extracted and modularized
- ✅ Create and update modes
- ✅ Personal, contract, salary, impositions sections
- ✅ Interactive confirmation buttons
- ✅ Comprehensive field support

## 🔧 Development Guidelines

### Adding a New Widget

1. Create a new file in `builders/`
2. Implement two functions:
   - `create_*_widget()` - Returns `WidgetRoot | None`
   - `*_widget_copy_text()` - Returns `str`
3. Export in `builders/__init__.py`
4. Export in main `__init__.py`
5. Document in this README

### Widget Best Practices

- **Keep it focused**: One widget per file
- **Include fallback**: Always provide copy_text version
- **Format consistently**: Use helper functions for currency, dates
- **Handle missing data**: Use optional parameters with sensible defaults
- **Document parameters**: Clear docstrings with arg descriptions

## 📊 Impact

**Before modularization:**
- `widgets.py`: 954 lines, monolithic
- Hard to navigate and maintain
- Mixed concerns (tax, payroll, documents)

**After modularization:**
- `widgets.py`: 42 lines (compatibility re-exports)
- `tax_calculation.py`: 284 lines (focused on tax widgets)
- `document_detail.py`: 321 lines (focused on document widgets)
- `person_confirmation.py`: 383 lines (focused on payroll widgets)
- Clear domain boundaries
- Easy to test and maintain
- Backward compatible imports
