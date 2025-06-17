import axios, { AxiosError } from 'axios';

// Assuming these types might be moved to a shared types file later
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
// Note: portfolioService also defines PORTFOLIOS_API_URL. Consider centralizing if many services use it.
const PORTFOLIOS_API_URL = `${API_BASE_URL}/portfolios`;


// --- Type Definitions ---
export type TradeType = 'BUY' | 'SELL';

export interface TradePayload {
  ticker_symbol: string;
  quantity: number;
  trade_type: TradeType;
  price?: number; // Optional, backend will use mock price if not provided
}

// Matches backend Pydantic Trade model
export interface TradeResponse {
  trade_id: number;
  portfolio_id: number;
  ticker_symbol: string;
  trade_type: TradeType; // Should be 'BUY' or 'SELL'
  quantity: number;
  price: string; // Backend's Decimal is serialized as string
  timestamp: string; // Assuming ISO string format
}

// --- API Functions ---

/**
 * Executes a new trade for a specific portfolio.
 * @param token - The authentication token.
 * @param portfolioId - The ID of the portfolio.
 * @param tradeDetails - The details of the trade.
 * @returns A promise that resolves to an ApiSuccessResponse with the created TradeResponse or an ApiErrorResponse.
 */
export const executeTrade = async (
  token: string,
  portfolioId: number,
  tradeDetails: TradePayload
): Promise<ApiSuccessResponse<TradeResponse> | ApiErrorResponse> => {
  try {
    const response = await axios.post<TradeResponse>(
      `${PORTFOLIOS_API_URL}/${portfolioId}/trades`,
      tradeDetails,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    return { success: true, data: response.data };
  } catch (error) {
    const axiosError = error as AxiosError<ApiErrorDetail>;
    let message = 'Failed to execute trade.';
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
