import axios, { AxiosError } from 'axios';

// --- Configuration ---
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const PORTFOLIOS_API_URL = `${API_BASE_URL}/portfolios`;

// --- Type Definitions ---
// Matches Pydantic Portfolio schema from backend
export interface Portfolio {
  portfolio_id: number;
  user_id: number;
  portfolio_name: string;
  created_at: string; // Assuming ISO string format from backend
}

export interface PortfolioCreatePayload {
  portfolio_name: string;
}

// Matches Pydantic Holding schema from backend
export interface Holding {
  holding_id: number;
  portfolio_id: number;
  ticker_symbol: string;
  quantity: number;
  average_buy_price: string; // Decimals are often serialized as strings
}

// Re-using general API response structures (can be moved to a shared types file later)
export interface ApiErrorDetail {
    detail: string | { msg: string; type: string; loc: (string | number)[] }[];
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  details?: any;
}

export interface ApiSuccessResponse<T> {
  success: true;
  data: T;
}

// --- API Functions ---

/**
 * Fetches all portfolios for the authenticated user.
 * @param token - The authentication token.
 * @returns A promise that resolves to an ApiSuccessResponse with an array of Portfolios or an ApiErrorResponse.
 */
export const getUserPortfolios = async (
  token: string
): Promise<ApiSuccessResponse<Portfolio[]> | ApiErrorResponse> => {
  try {
    const response = await axios.get<Portfolio[]>(PORTFOLIOS_API_URL, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to fetch portfolios.';
    if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      } else if (Array.isArray(axiosError.response.data.detail)) {
        message = axiosError.response.data.detail.map(d => d.msg).join(', ');
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
 * Fetches all holdings for a specific portfolio of the authenticated user.
 * @param token - The authentication token.
 * @param portfolioId - The ID of the portfolio.
 * @returns A promise that resolves to an ApiSuccessResponse with an array of Holdings or an ApiErrorResponse.
 */
export const getPortfolioHoldings = async (
  token: string,
  portfolioId: number
): Promise<ApiSuccessResponse<Holding[]> | ApiErrorResponse> => {
  try {
    const response = await axios.get<Holding[]>(`${PORTFOLIOS_API_URL}/${portfolioId}/holdings`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to fetch holdings.';
    if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      } else if (Array.isArray(axiosError.response.data.detail)) {
        message = axiosError.response.data.detail.map(d => d.msg).join(', ');
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
 * Creates a new portfolio for the authenticated user.
 * @param token - The authentication token.
 * @param payload - PortfolioCreatePayload containing the portfolio name.
 * @returns A promise that resolves to an ApiSuccessResponse with the created Portfolio or an ApiErrorResponse.
 */
export const createPortfolio = async (
  token: string,
  payload: PortfolioCreatePayload
): Promise<ApiSuccessResponse<Portfolio> | ApiErrorResponse> => {
  try {
    const response = await axios.post<Portfolio>(PORTFOLIOS_API_URL, payload, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json', // Ensure correct content type for JSON payload
      },
    });
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to create portfolio.';
    if (axiosError.response && axiosError.response.data && axiosError.response.data.detail) {
      if (typeof axiosError.response.data.detail === 'string') {
        message = axiosError.response.data.detail;
      } else if (Array.isArray(axiosError.response.data.detail)) {
        message = axiosError.response.data.detail.map(d => d.msg).join(', ');
      }
    } else if (axiosError.request) {
      message = 'No response from server. Please check your network connection.';
    } else {
      message = axiosError.message || message;
    }
    return { success: false, message, details: axiosError.response?.data };
  }
};
