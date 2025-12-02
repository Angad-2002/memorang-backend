"""MCQ widget builder for displaying quiz questions."""

from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

from chatkit.widgets import DynamicWidgetRoot, WidgetRoot, WidgetTemplate

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Ensure this logger shows INFO messages

# Try to load the widget template
_widget_template: WidgetTemplate | None = None

def _get_widget_template() -> WidgetTemplate | None:
    """Load the widget template from file."""
    global _widget_template
    if _widget_template is None:
        # Try multiple possible paths
        possible_paths = [
            Path(__file__).parent.parent.parent / "MCQ Card (copy).widget",
            Path(__file__).parent.parent.parent.parent / "MCQ Card (copy).widget",
            Path.cwd() / "MCQ Card (copy).widget",
            Path.cwd() / "backend" / "MCQ Card (copy).widget",
        ]
        
        for widget_file in possible_paths:
            if widget_file.exists():
                try:
                    logger.info(f"Loading widget template from: {widget_file}")
                    _widget_template = WidgetTemplate.from_file(str(widget_file))
                    logger.info("Widget template loaded successfully")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load widget template from {widget_file}: {e}")
                    continue
        else:
            logger.warning("Widget template file not found in any expected location")
    return _widget_template


def build_mcq_widget(
    question_id: str,
    index: int,
    total: int,
    prompt: str,
    options: list[dict[str, Any]],
    selected: str = "",
    status: str = "idle",
    feedback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an MCQ widget card for displaying a quiz question."""
    print(f"[WIDGET] build_mcq_widget called with:")
    print(f"  - question_id: {question_id}")
    print(f"  - index: {index}")
    print(f"  - total: {total}")
    print(f"  - prompt: {prompt[:100]}...")
    print(f"  - options: {len(options)} options")
    logger.info(f"[WIDGET] build_mcq_widget called with:")
    logger.info(f"  - question_id: {question_id}")
    logger.info(f"  - index: {index}")
    logger.info(f"  - total: {total}")
    logger.info(f"  - prompt: {prompt[:100]}...")
    logger.info(f"  - options: {len(options)} options")
    for i, opt in enumerate(options):
        print(f"    Option {i}: {opt}")
        logger.info(f"    Option {i}: {opt}")
    
    widget_data = {
        "questionId": question_id,
        "index": index,
        "total": total,
        "prompt": prompt,
        "options": options,
        "selected": selected,
        "status": status,
        "feedback": feedback or {},
    }
    
    logger.info(f"[WIDGET] widget_data prepared: {list(widget_data.keys())}")
    logger.info(f"[WIDGET] widget_data['prompt'] = {widget_data['prompt'][:100]}...")
    logger.info(f"[WIDGET] widget_data['options'] = {widget_data['options']}")

    # Try to use the widget template if available
    template = _get_widget_template()
    if template:
        logger.info(f"[WIDGET] Template found, building with data")
        logger.info(f"[WIDGET] Building widget with data: questionId={question_id}, index={index}, prompt={prompt[:50]}...")
        logger.info(f"[WIDGET] Widget data keys: {list(widget_data.keys())}")
        logger.info(f"[WIDGET] Widget data values: questionId={widget_data['questionId']}, prompt={widget_data['prompt'][:50]}...")
        try:
            # Try both ways: with data= parameter and without
            built_widget = template.build(data=widget_data)
            logger.info(f"[WIDGET] Template.build returned: type={type(built_widget)}")
            if built_widget:
                logger.info(f"[WIDGET] Built widget is not None")
                if hasattr(built_widget, 'model_dump'):
                    logger.info(f"[WIDGET] Built widget has model_dump method (Pydantic model)")
                if isinstance(built_widget, dict):
                    logger.info(f"[WIDGET] Built widget is dict with keys: {list(built_widget.keys())}")
                    if "type" in built_widget:
                        logger.info(f"[WIDGET] Built widget type: {built_widget.get('type')}")
                    # Check children for prompt
                    if "children" in built_widget:
                        children = built_widget.get("children", [])
                        logger.info(f"[WIDGET] Built widget has {len(children)} children")
                        for i, child in enumerate(children):
                            if isinstance(child, dict) and child.get("type") == "Title":
                                logger.info(f"[WIDGET] Found Title child with value: {child.get('value', '')[:100]}")
            
            # Verify the widget was built with actual data, not defaults
            if built_widget is None:
                logger.warning("[WIDGET] Template.build returned None, trying without data= parameter")
                built_widget = template.build(widget_data)
                logger.info(f"[WIDGET] Template.build (without data=) returned: type={type(built_widget)}")
            
            # Handle DynamicWidgetRoot or WidgetRoot objects (Pydantic models)
            if built_widget is not None:
                if isinstance(built_widget, (DynamicWidgetRoot, WidgetRoot)):
                    # Convert Pydantic model to dict
                    widget_dict = built_widget.model_dump(exclude_none=True, exclude_unset=True)
                    logger.info("[WIDGET] Widget built from template successfully (converted from DynamicWidgetRoot)")
                    logger.info(f"[WIDGET] Widget dict type: {widget_dict.get('type')}")
                    # Check if prompt is in the widget
                    if "children" in widget_dict:
                        for child in widget_dict.get("children", []):
                            if isinstance(child, dict) and child.get("type") == "Title":
                                logger.info(f"[WIDGET] Title value in final widget: {child.get('value', '')[:100]}")
                    return widget_dict
                elif isinstance(built_widget, dict):
                    # Already a dict, check if it's valid
                    if "type" in built_widget:
                        logger.info("[WIDGET] Widget built from template successfully")
                        logger.info(f"[WIDGET] Widget type: {built_widget.get('type')}")
                        # Check if prompt is in the widget
                        if "children" in built_widget:
                            for child in built_widget.get("children", []):
                                if isinstance(child, dict) and child.get("type") == "Title":
                                    logger.info(f"[WIDGET] Title value in final widget: {child.get('value', '')[:100]}")
                        return built_widget
                    else:
                        logger.warning(f"[WIDGET] Template returned invalid widget structure (no 'type' key), keys: {list(built_widget.keys())}")
                else:
                    logger.warning(f"[WIDGET] Template returned unexpected type: {type(built_widget)}, value: {built_widget}")
            else:
                logger.warning("[WIDGET] Template.build returned None")
        except Exception as e:
            # Log the error so we can debug what's wrong
            logger.error(f"[WIDGET] Failed to build widget from template: {e}", exc_info=True)
            # Fall through to fallback if template build fails
    else:
        logger.warning("[WIDGET] Widget template not available, using fallback widget")
    
    # Fallback to manual widget structure if file not found or build fails
    logger.info("[WIDGET] Using fallback widget structure")
    fallback = _build_fallback_widget(widget_data)
    logger.info(f"[WIDGET] Fallback widget built, type: {fallback.get('type')}")
    return fallback


def _build_fallback_widget(data: dict[str, Any]) -> dict[str, Any]:
    """Fallback widget structure if .widget file is not found."""
    return {
        "type": "Card",
        "size": "md",
        "children": [
            {
                "type": "Row",
                "children": [
                    {
                        "type": "Caption",
                        "value": f"Question {data['index']} of {data['total']}",
                    },
                    {"type": "Spacer"},
                    {"type": "Badge", "label": "MCQ", "color": "info"},
                ],
            },
            {
                "type": "Title",
                "value": data["prompt"],
                "size": "sm",
            },
            {
                "type": "Form",
                "onSubmitAction": {
                    "type": "mcq.submit",
                    "payload": {"questionId": data["questionId"], "index": data["index"]},
                },
                "children": [
                    {
                        "type": "Col",
                        "gap": 3,
                        "children": [
                            {
                                "type": "RadioGroup",
                                "name": "answer",
                                "options": data["options"],
                                "defaultValue": data["selected"],
                                "direction": "col",
                                "required": True,
                                "disabled": data["status"] == "correct",
                            },
                            {
                                "type": "Row",
                                "children": [
                                    {
                                        "type": "Button",
                                        "submit": True,
                                        "label": "Try again" if data["status"] == "incorrect" else "Submit answer",
                                        "style": "primary",
                                        "disabled": data["status"] == "correct",
                                    },
                                    {
                                        "type": "Button",
                                        "label": "Clear",
                                        "variant": "outline",
                                        "onClickAction": {
                                            "type": "mcq.clear",
                                            "payload": {"questionId": data["questionId"], "index": data["index"]},
                                        },
                                    },
                                    {"type": "Spacer"},
                                    {
                                        "type": "Button",
                                        "label": "Finish" if data["index"] == data["total"] else "Next",
                                        "iconEnd": "chevron-right",
                                        "onClickAction": {
                                            "type": "mcq.finish" if data["index"] == data["total"] else "mcq.next",
                                            "payload": {"questionId": data["questionId"], "index": data["index"]},
                                        },
                                        "disabled": data["status"] != "correct",
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    }

