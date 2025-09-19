from flask import Blueprint, jsonify, request
from flask_login import login_required

from services.bot_assistant import (
    start_conversation,
    process_user_message,
    ingest_excel,
    resolve_report_download_url,
    BotConversationState,
)

bot_bp = Blueprint('bot', __name__, url_prefix='/bot')


@bot_bp.route('/start', methods=['POST'])
@login_required
def bot_start():
    """Start a new conversational session."""
    return jsonify(start_conversation())


@bot_bp.route('/message', methods=['POST'])
@login_required
def bot_message():
    data = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    response = process_user_message(message)
    return jsonify(response)


@bot_bp.route('/reset', methods=['POST'])
@login_required
def bot_reset():
    BotConversationState().reset()
    return jsonify(start_conversation())


@bot_bp.route('/upload', methods=['POST'])
@login_required
def bot_upload():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files provided.'}), 400

    messages = []
    errors = []
    warnings = []
    last_payload = None

    for storage in files:
        result = ingest_excel(storage)
        last_payload = result
        if 'message' in result:
            messages.append(result['message'])
        if 'error' in result:
            errors.append(result['error'])
        warnings.extend(result.get('warnings', []))

    if last_payload is None:
        return jsonify({'error': 'Upload failed.'}), 500

    response = {
        'messages': messages,
        'collected': last_payload.get('collected', {}),
        'completed': last_payload.get('completed'),
        'pending_fields': last_payload.get('pending_fields', []),
    }

    if not last_payload.get('completed', False):
        response['field'] = last_payload.get('field')
        response['question'] = last_payload.get('question')
        if 'help_text' in last_payload:
            response['help_text'] = last_payload['help_text']

    if warnings:
        response['warnings'] = warnings
    if errors:
        response['errors'] = errors

    return jsonify(response)


@bot_bp.route('/document/<submission_id>', methods=['GET'])
@login_required
def bot_document(submission_id):
    result = resolve_report_download_url(submission_id)
    status = 200 if 'download_url' in result else 404
    return jsonify(result), status
