export const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '8000' 
    ? 'http://localhost:8000/api' 
    : '/api';

export const globalState = {
    currentUserEmail: null
};
