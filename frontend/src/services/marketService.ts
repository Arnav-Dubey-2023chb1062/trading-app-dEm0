import axios, { AxiosError } from 'axios';

// Assuming these types might be moved to a shared types file later
// Re-defining here for clarity, or import from a shared location e.g. ./serviceTypes.ts
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

// --- Configuration ---
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const MARKET_DATA_API_URL = `${API_BASE_URL}/marketdata`;

// --- Type Definitions ---
// Matches backend Pydantic TickerPriceResponse
export interface TickerPriceResponse {
  ticker_symbol: string;
  price: string; // Decimals are often serialized as strings from backend
  source: string;
}

// --- API Functions ---

/**
 * Fetches the current market price for a given ticker symbol.
 * @param token - The authentication token (optional for this specific endpoint if not protected).
 * @param tickerSymbol - The ticker symbol to fetch the price for.
 * @returns A promise that resolves to an ApiSuccessResponse with TickerPriceResponse or an ApiErrorResponse.
 */
export const getTickerPrice = async (
  // token: string | null, // Making token optional as endpoint might not be protected
  tickerSymbol: string
): Promise<ApiSuccessResponse<TickerPriceResponse> | ApiErrorResponse> => {
  if (!tickerSymbol) {
    return { success: false, message: "Ticker symbol cannot be empty." };
  }
  try {
    // const headers: { [key: string]: string } = {};
    // if (token) {
    //   headers['Authorization'] = `Bearer ${token}`;
    // }
    // As per current backend setup, /marketdata/{ticker_symbol} is not auth protected.
    // If it were, the headers would be needed.

    const response = await axios.get<TickerPriceResponse>(
      `${MARKET_DATA_API_URL}/${tickerSymbol.toUpperCase()}`
      // { headers } // Pass headers if endpoint becomes protected
    );
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to fetch market price.';
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
