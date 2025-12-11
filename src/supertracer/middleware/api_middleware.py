from fastapi import Request
from supertracer.types.options import ApiOptions
from supertracer.services.auth import AuthService

def authenticate_request(request: Request, auth_service: AuthService, api_options: ApiOptions) -> bool:
    """
    Middleware function to authenticate incoming API requests using API key authentication.
    
    Args:
        request: Incoming FastAPI request
        auth_service: Instance of AuthService to handle authentication
        api_options: API authentication options
        
    Returns:
        True if authenticated, False otherwise
    """
    if not api_options.api_enabled:
        return True  # API is disabled, allow all requests
    
    if not api_options.api_auth_fn and not api_options.api_key and not api_options.api_key_env:
        return True  # No authentication configured, allow all requests
    
    if not hasattr(auth_service, 'api_authenticate'):
        return True  # No authentication required

    api_key = request.headers.get("Authorization")

    if not api_key:
        return False

    return auth_service.api_authenticate(api_key)