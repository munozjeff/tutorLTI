"""
LTI Advantage Grade Services (AGS)
Sends student scores back to Open edX Gradebook when configured.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)


def is_gradeable(lti_session: dict) -> bool:
    """
    Detect whether the LTI launch provided AGS endpoints.
    Open edX includes the AGS claim ONLY when the activity has a Gradebook item.
    """
    ags = lti_session.get('lti_ags', {})
    return bool(ags.get('lineitem') or ags.get('lineitems'))

from typing import Optional

def _get_access_token(token_url: str, client_id: str, private_key: str = None) -> Optional[str]:
    """
    Get OAuth2 client_credentials token from the LMS.
    Uses the LTI tool's client_id and optionally signs with private key.
    """
    try:
        resp = requests.post(token_url, data={
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            'scope': (
                'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem '
                'https://purl.imsglobal.org/spec/lti-ags/scope/score'
            ),
        }, timeout=10)
        resp.raise_for_status()
        return resp.json().get('access_token')
    except Exception as e:
        logger.error(f"AGS token error: {e}")
        return None


def submit_grade(
    score: float,
    max_score: float,
    user_id_lti: str,
    comment: str,
    lti_session: dict,
) -> dict:
    """
    Submit a score to the LMS via LTI AGS Score endpoint.

    Args:
        score: Points earned (e.g. 8.0)
        max_score: Maximum possible points (e.g. 10.0)
        user_id_lti: LTI subject (sub claim) of the student
        comment: Brief comment (shown in gradebook)
        lti_session: The stored lti_context / lti_ags data from Flask session

    Returns:
        dict with keys: sent (bool), detail (str)
    """
    ags = lti_session.get('lti_ags', {})
    lineitem = ags.get('lineitem')
    token_url = lti_session.get('lti_token_url') or os.getenv('LTI_TOKEN_URL', '')
    client_id = os.getenv('LTI_CLIENT_ID', '')

    if not lineitem:
        return {'sent': False, 'detail': 'No AGS lineitem — activity is not gradeable'}

    if not token_url:
        return {'sent': False, 'detail': 'LTI_TOKEN_URL not configured'}

    token = _get_access_token(token_url, client_id)
    if not token:
        return {'sent': False, 'detail': 'Could not obtain AGS access token'}

    # Build the score endpoint URL
    score_url = lineitem.rstrip('/') + '/scores'

    from datetime import datetime, timezone
    payload = {
        'scoreGiven': score,
        'scoreMaximum': max_score,
        'comment': comment,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'userId': user_id_lti,
        'activityProgress': 'Completed',
        'gradingProgress': 'FullyGraded',
    }

    try:
        resp = requests.post(
            score_url,
            json=payload,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/vnd.ims.lis.v1.score+json',
            },
            timeout=10
        )
        resp.raise_for_status()
        logger.info(f"AGS score submitted for user {user_id_lti}: {score}/{max_score}")
        return {'sent': True, 'detail': f'Score {score}/{max_score} sent to gradebook'}
    except Exception as e:
        logger.error(f"AGS score submission failed: {e}")
        return {'sent': False, 'detail': str(e)}
