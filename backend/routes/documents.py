"""
Document Routes — Instructor document upload and management for RAG
"""
import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, session
from functools import wraps
from werkzeug.utils import secure_filename
from services import rag_service

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/app/instance/uploads')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'doc', 'md'}
MAX_FILE_MB = 20


def instructor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        lti_user = session.get('lti_user', {})
        if lti_user and lti_user.get('role') not in ('instructor', 'admin', None):
            return jsonify({'error': 'Instructor access required'}), 403
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/upload', methods=['POST'])
@instructor_required
def upload_document():
    """Upload and index a document for RAG"""
    lti_context = session.get('lti_context', {})
    resource_id = request.form.get('resource_id') or lti_context.get('resource_id', 'default')

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'error': 'Empty filename'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

    filename = secure_filename(file.filename)
    doc_id = str(uuid.uuid4())

    # Save file temporarily
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    save_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")

    try:
        file.save(save_path)

        # Check file size
        size_mb = os.path.getsize(save_path) / (1024 * 1024)
        if size_mb > MAX_FILE_MB:
            os.remove(save_path)
            return jsonify({'error': f'File too large. Max {MAX_FILE_MB}MB'}), 413

        # Index document
        num_chunks = rag_service.ingest_document(save_path, doc_id, resource_id, filename)

        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'filename': filename,
            'chunks': num_chunks,
            'resource_id': resource_id,
            'message': f'Documento "{filename}" indexado con {num_chunks} fragmentos.'
        })
    except Exception as e:
        return jsonify({'error': f'Error al procesar el documento: {str(e)}'}), 500
    finally:
        # Clean up temp file
        if os.path.exists(save_path):
            os.remove(save_path)


@documents_bp.route('/<resource_id>', methods=['GET'])
@instructor_required
def list_documents(resource_id):
    """List indexed documents for a resource"""
    docs = rag_service.list_documents(resource_id)
    return jsonify({'documents': docs, 'resource_id': resource_id})


@documents_bp.route('/<resource_id>/<doc_id>', methods=['DELETE'])
@instructor_required
def delete_document(resource_id, doc_id):
    """Remove a document from the index"""
    success = rag_service.delete_document(doc_id, resource_id)
    if success:
        return jsonify({'success': True, 'message': 'Documento eliminado del índice'})
    return jsonify({'error': 'Document not found'}), 404
