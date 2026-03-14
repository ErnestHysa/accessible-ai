"""AI-powered accessibility fix generation service."""

from typing import Optional
from app.config import get_settings
from app.models.scan import Issue
from app.logging_config import get_logger
import httpx

settings = get_settings()
logger = get_logger(__name__)


# WCAG rule templates for common issues
FIX_TEMPLATES = {
    # Image issues
    "image-alt": {
        "description": "Images must have alternate text",
        "fix_template": """Add alt attribute to the image:
Before: <img src="{src}">
After:  <img src="{src}" alt="Descriptive text about the image">""",
        "code_template": '<img src="{src}" alt="{alt_text}">',
    },
    "image-redundant-alt": {
        "description": "Redundant alternate text",
        "fix_template": """Use more descriptive alt text that doesn't repeat nearby content.""",
        "code_template": '<img src="{src}" alt="{specific_description}">',
    },
    # Color issues
    "color-contrast": {
        "description": "Insufficient color contrast",
        "fix_template": """Increase contrast between foreground and background colors.
Current ratio: {current_ratio}:1
Required ratio: {required_ratio}:1

Suggested colors:
- Foreground: {suggested_fg}
- Background: {suggested_bg}""",
        "code_template": """/* Update your CSS */
.element {{
  color: {suggested_fg};
  background-color: {suggested_bg};
}}""",
    },
    # Form issues
    "label": {
        "description": "Form inputs must have labels",
        "fix_template": """Add a label element associated with the input:
<label for="{input_id}">{label_text}</label>
<input id="{input_id}" type="{input_type}" name="{input_name}">""",
        "code_template": """<label for="{input_id}">{label_text}</label>
<input id="{input_id}" type="{input_type}" name="{input_name}">""",
    },
    "legend": {
        "description": "Fieldset must have a legend",
        "fix_template": """Add a legend element to the fieldset:
<fieldset>
  <legend>{legend_text}</legend>
  <!-- fieldset content -->
</fieldset>""",
        "code_template": """<fieldset>
  <legend>{legend_text}</legend>
  {content}
</fieldset>""",
    },
    # Link issues
    "link-name": {
        "description": "Links must have discernible text",
        "fix_template": """Add descriptive text to the link:
Before: <a href="{url}">click here</a>
After:  <a href="{url}">View our pricing page</a>""",
        "code_template": '<a href="{url}">{descriptive_text}</a>',
    },
    "link-in-text-block": {
        "description": "Links should be easily distinguishable",
        "fix_template": """Ensure links are visually distinct from surrounding text.
Add underline or different color:
a {{
  text-decoration: underline;
  color: #0066cc;
}}""",
        "code_template": """a {{
  text-decoration: underline;
  color: #0066cc;
}}
a:hover {{
  color: #004080;
}}""",
    },
    # Heading issues
    "heading-order": {
        "description": "Heading levels must not be skipped",
        "fix_template": """Use heading levels sequentially (h1, h2, h3...).
Don't skip from h1 to h3.""",
        "code_template": "<h{level}>{text}</h{level}>",
    },
    # ARIA issues
    "aria-label": {
        "description": "aria-label attribute must be accessible",
        "fix_template": """Provide a meaningful aria-label:
<button aria-label="{action_description}">...</button>""",
        "code_template": '<button aria-label="{action_description}">{content}</button>',
    },
    "aria-required-attr": {
        "description": "Required ARIA attributes missing",
        "fix_template": """Add the required ARIA attribute: {attr_name}
{element_code} {attr_name}="{attr_value}"
""",
        "code_template": '{tag} {attr_name}="{attr_value}"',
    },
    # Table issues
    "th-headers": {
        "description": "Table headers must refer to data cells",
        "fix_template": """Use headers attribute to associate headers with data cells:
<td headers="col1 row1">...</td>""",
        "code_template": '<td headers="{headers}">{content}</td>',
    },
    "table-duplicate-name": {
        "description": "Table has duplicate name or caption",
        "fix_template": """Ensure each table has a unique name or caption.""",
        "code_template": "<caption>{unique_caption}</caption>",
    },
}


async def generate_fix(issue: Issue) -> str:
    """Generate an AI-powered fix for an accessibility issue.

    Args:
        issue: The issue object containing violation details

    Returns:
        A string containing the fix suggestion and code
    """
    # First try to use template-based fixes (fast, no API call)
    if issue.type in FIX_TEMPLATES:
        template = FIX_TEMPLATES[issue.type]
        fix_code = template["code_template"]

        # Customize the fix based on issue context
        if issue.element_html:
            fix_code = customize_fix_from_html(fix_code, issue.element_html)

        # Build the impact section separately to avoid nested f-strings
        impact_section = ""
        if issue.impact:
            impact_section = f"## Impact\n{issue.impact}\n"

        selector_text = issue.selector if issue.selector else "on the page"

        return f"""# Fix for {issue.type}

{template['fix_template']}

## Issue Details
{issue.description}

{impact_section}
## Suggested Code
```html
{fix_code}
```

## How to Apply
1. Locate the element: {selector_text}
2. Replace or modify it with the suggested code above
3. Test the change with a screen reader
4. Re-scan to verify the fix
"""

    # If no template, use OpenAI API (if configured)
    if settings.openai_api_key:
        return await generate_ai_fix(issue)

    # Fallback generic fix
    return generate_generic_fix(issue)


def customize_fix_from_html(template: str, element_html: str) -> str:
    """Customize the fix template based on the actual element HTML."""
    from bs4 import BeautifulSoup

    try:
        soup = BeautifulSoup(element_html, "html.parser")
        tag = soup.find()

        if not tag:
            return template

        # Extract common attributes
        result = template
        if tag.get("src"):
            result = result.replace("{src}", tag.get("src", ""))
        if tag.get("href"):
            result = result.replace("{url}", tag.get("href", ""))
        if tag.get("id"):
            result = result.replace("{input_id}", tag.get("id", ""))
        if tag.get("name"):
            result = result.replace("{input_name}", tag.get("name", ""))
        if tag.get("type"):
            result = result.replace("{input_type}", tag.get("type", ""))
        if tag.name:
            result = result.replace("{tag}", tag.name)

        # Generate placeholder text based on tag type
        if tag.name == "img":
            alt_text = tag.get("alt", "A descriptive description of the image content")
            result = result.replace("{alt_text}", alt_text)
        elif tag.name == "button":
            result = result.replace("{action_description}", tag.get_text() or "Button action")
        elif tag.name in ("input", "textarea"):
            result = result.replace("{label_text}", f"Label for {tag.get('name', 'this field')}")

        return result
    except Exception:
        return template


async def generate_ai_fix(issue: Issue) -> str:
    """Generate an AI fix using OpenAI API.

    This is called when no template exists for the issue type.
    """
    try:
        # Build the user prompt content
        issue_details = [
            f"Issue Type: {issue.type}",
            f"Severity: {issue.severity}",
            f"Description: {issue.description}",
        ]
        if issue.impact:
            issue_details.append(f"Impact: {issue.impact}")
        if issue.selector:
            issue_details.append(f"Selector: {issue.selector}")
        if issue.element_html:
            issue_details.append(f"Element HTML: {issue.element_html}")

        user_content = (
            "Generate a fix for this accessibility issue:\n\n"
            + "\n".join(issue_details)
            + "\n\nProvide:\n"
            "1. A clear explanation of the problem\n"
            "2. Specific code to fix it\n"
            "3. How to implement the fix\n"
            "4. How to verify the fix works"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",  # Cost-effective model
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an accessibility expert specializing in WCAG 2.1 compliance. "
                                "Provide clear, actionable fixes for accessibility issues. "
                                "Include code examples in HTML/CSS/JavaScript as needed. "
                                "Be concise but thorough."
                            ),
                        },
                        {
                            "role": "user",
                            "content": user_content,
                        },
                    ],
                    "max_tokens": 500,
                    "temperature": 0.3,
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]

    except Exception as e:
        # Log error and fallback to generic fix
        logger.error(f"AI fix generation failed: {e}, using generic fix")

    return generate_generic_fix(issue)


def generate_generic_fix(issue: Issue) -> str:
    """Generate a generic fix when templates and AI are not available."""
    return f"""# Fix for {issue.type}

## Issue
{issue.description}

## Severity
{issue.severity}

## Recommended Action
Please review the WCAG 2.1 guidelines for this issue type and implement the necessary changes.

## Resources
- WCAG 2.1 Quick Reference: https://www.w3.org/WAI/WCAG21/quickref/
- Accessibility Tutorials: https://www.w3.org/WAI/tutorials/

## Next Steps
1. Review the element at: {issue.selector or 'the specified location'}
2. Apply the appropriate fix based on WCAG guidelines
3. Test with assistive technology
4. Run a new scan to verify
"""
