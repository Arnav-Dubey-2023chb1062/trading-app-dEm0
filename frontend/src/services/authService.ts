import axios, { AxiosError } from 'axios';

// --- Configuration ---
// This should ideally come from an environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const USERS_API_URL = `${API_BASE_URL}/users`; // Backend user routes are prefixed with /users

// --- Type Definitions ---
export interface RegistrationPayload {
  username: string;
  email: string;
  password_hash: string; // Backend expects password_hash, but frontend sends plain password
                         // Let's align with what the frontend form provides: plain password
                         // The backend's UserCreate model expects 'password'
}

export interface UserRegistrationPayload {
  username: string;
  email: string;
  password: string; // Plain password from the form
}


export interface UserLoginPayload {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// User object returned by the backend upon successful registration (excluding password)
export interface RegisteredUser {
  user_id: number;
  username: string;
  email: string;
  created_at?: string | Date; // Ensure this matches what backend Pydantic User sends
}

// This User type will be used for the /me endpoint response
export interface User extends RegisteredUser {
  // Currently RegisteredUser has all necessary fields (user_id, username, email).
  // If /me returns more fields than /register, add them here or ensure RegisteredUser is comprehensive.
  // For now, assuming /me returns the same Pydantic User schema as /register's response.
}

// Structure for handling errors
export interface ApiErrorDetail {
  detail: string | { msg: string; type: string; loc: (string | number)[] }[];
}

export interface ApiErrorResponse {
  success: false;
  message: string; // A user-friendly message or a summary
  details?: any; // Could be error.response.data or specific error parts
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

// --- API Functions ---

/**
 * Registers a new user.
 * @param payload - UserRegistrationPayload containing username, email, and password.
 * @returns A promise that resolves to an ApiSuccessResponse with RegisteredUser data or an ApiErrorResponse.
 */
export const registerUser = async (
  payload: UserRegistrationPayload
): Promise<ApiSuccessResponse<RegisteredUser> | ApiErrorResponse> => {
  try {
    // The backend endpoint /users/register expects UserCreate model
    // which has username, email, password
    const response = await axios.post<RegisteredUser>(`${USERS_API_URL}/register`, payload);
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Registration failed. Please try again.';
    if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      } else if (Array.isArray(axiosError.response.data.detail) && axiosError.response.data.detail.length > 0) {
        // Handle complex validation errors if needed, e.g., take the first message
        message = axiosError.response.data.detail[0].msg || message;
      }
    } else if (axiosError.request) {
      message = 'No response from server. Please check your network connection.';
    } else {
      message = axiosError.message || message;
    }
    return { success: false, message, details: axiosError.response?.data };
  }
};

/**
 * Fetches the current user's details.
 * @param token - The authentication token.
 * @returns A promise that resolves to an ApiSuccessResponse with User data or an ApiErrorResponse.
 */
export const getMe = async (
  token: string
): Promise<ApiSuccessResponse<User> | ApiErrorResponse> => {
  try {
    const response = await axios.get<User>(`${USERS_API_URL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to fetch user details.';
     if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      }
    } else if (axiosError.request) {
      message = 'No response from server. Please check your network connection.';
    } else {
      message = axiosError.message || message;
    }
    // If token is invalid (e.g. 401), the caller (AuthContext) should handle logout.
    return { success: false, message, details: axiosError.response?.data };
  }
};

/**
 * Logs in a user.
 * @param payload - UserLoginPayload containing username and password.
 * @returns A promise that resolves to an ApiSuccessResponse with TokenResponse data or an ApiErrorResponse.
 */
export const loginUser = async (
  payload: UserLoginPayload
): Promise<ApiSuccessResponse<TokenResponse> | ApiErrorResponse> => {
  try {
    const params = new URLSearchParams();
    params.append('username', payload.username);
    params.append('password', payload.password);

    const response = await axios.post<TokenResponse>(`${USERS_API_URL}/login`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Login failed. Please check your credentials.';
     if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      } // No array handling for login, typically simpler error
    } else if (axiosError.request) {
      message = 'No response from server. Please check your network connection.';
    } else {
      message = axiosError.message || message;
    }
    return { success: false, message, details: axiosError.response?.data };
  }
};
