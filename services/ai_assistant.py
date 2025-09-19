import json
from typing import Dict, Any

import requests
from flask import current_app


class AISuggestionError(Exception):
    """Raised when AI suggestion generation fails."""


_ALLOWED_FIELDS = {
    'purpose': 'the Purpose section describing why the SAT report is being produced',
    'scope': 'the Scope section outlining the boundaries of testing to be performed'
}


def ai_is_configured(app) -> bool:
    """Return True if AI assistance is configured for the given app."""
    if app.config.get('AI_ENABLED'):
        return True
    if app.config.get('OPENAI_API_KEY'):
        return True
    return False


def generate_sat_suggestion(field: str, submission_context: Dict[str, Any]) -> str:
    """Generate an AI suggestion for the requested SAT field."""
    field_key = field.lower()
    if field_key not in _ALLOWED_FIELDS:
        raise AISuggestionError(f"Unsupported field '{field}'.")

    app = current_app
    if not ai_is_configured(app):
        raise AISuggestionError('AI assistance is not configured. Set OPENAI_API_KEY or disable the feature.')

    provider = (app.config.get('AI_PROVIDER') or 'openai').lower()
    if provider == 'openai':
        return _generate_with_openai(field_key, submission_context)
    raise AISuggestionError(f"AI provider '{provider}' is not supported.")


def _generate_with_openai(field: str, submission_context: Dict[str, Any]) -> str:
    app = current_app
    api_key = app.config.get('OPENAI_API_KEY')
    if not api_key:
        raise AISuggestionError('OPENAI_API_KEY is not configured.')

    model = app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    audience_hint = submission_context.get('audience') or 'project stakeholders'

    prompt_sections = [
        "You are assisting with drafting a System Acceptance Testing (SAT) report.",
        "Use crisp professional language suitable for engineering documentation.",
        f"Provide content for {_ALLOWED_FIELDS[field]}.",
        "Keep the response concise (2-4 sentences) and avoid markdown formatting.",
    ]

    context_lines = []
    for key, value in submission_context.items():
        if value:
            context_lines.append(f"- {key.replace('_', ' ').title()}: {value}")

    if context_lines:
        prompt_sections.append("Here is relevant context:")
        prompt_sections.extend(context_lines)

    prompt_sections.append(f"Craft the text addressing {audience_hint}.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an assistant that helps prepare formal engineering SAT reports."},
            {"role": "user", "content": "\n".join(prompt_sections)}
        ],
        "temperature": 0.3,
        "max_tokens": 200
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            data=json.dumps(payload),
            timeout=30
        )
    except requests.RequestException as exc:
        raise AISuggestionError(f'Failed to reach OpenAI: {exc}') from exc

    if response.status_code >= 400:
        raise AISuggestionError(f'OpenAI API error: {response.status_code} {response.text}')

    try:
        data = response.json()
        suggestion = data['choices'][0]['message']['content'].strip()
        if not suggestion:
            raise KeyError('empty suggestion')
        return suggestion
    except (KeyError, IndexError, ValueError) as exc:
        raise AISuggestionError('Unexpected response format from OpenAI.') from exc
