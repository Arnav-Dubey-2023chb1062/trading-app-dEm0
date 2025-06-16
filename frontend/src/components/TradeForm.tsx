"use client";

import { useState, FormEvent } from "react";
import { useAuth } from "../context/AuthContext";
import { executeTrade, TradePayload, TradeResponse } from "../services/tradeService"; // Import service

export type TradeType = 'BUY' | 'SELL';

interface TradeFormProps {
  portfolioId: number;
  onTradeSuccess: (tradeData: TradeResponse) => void; // Use specific TradeResponse type
}

export default function TradeForm({ portfolioId, onTradeSuccess }: TradeFormProps) {
  const [tickerSymbol, setTickerSymbol] = useState("");
  const [quantity, setQuantity] = useState(""); // Store as string for input field
  const [tradeType, setTradeType] = useState<TradeType>('BUY');
  const [price, setPrice] = useState(""); // Optional client-set price, store as string
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!token) {
      setError("You must be logged in to execute a trade.");
      return;
    }

    const numQuantity = parseInt(quantity);
    if (isNaN(numQuantity) || numQuantity <= 0) {
      setError("Quantity must be a positive number.");
      return;
    }

    const numPrice = price ? parseFloat(price) : undefined;
    if (price && (isNaN(numPrice) || numPrice <= 0)) {
      setError("Price, if provided, must be a positive number.");
      return;
    }
    if (!tickerSymbol.trim()) {
        setError("Ticker symbol cannot be empty.");
        return;
    }


    setIsLoading(true);
    setError(null);

    const payload: TradePayload = {
      ticker_symbol: tickerSymbol.toUpperCase(),
      quantity: numQuantity,
      trade_type: tradeType,
      price: numPrice, // This can be undefined if price string is empty
    };

    try {
      const result = await executeTrade(token, portfolioId, payload);
      if (result.success) {
        onTradeSuccess(result.data);
        // Clear form on success
        setTickerSymbol("");
        setQuantity("");
        setPrice("");
        setTradeType('BUY');
      } else {
        setError(result.message || "Failed to execute trade.");
      }
    } catch (err) {
      console.error("Trade execution catch block error:", err);
      setError("An unexpected error occurred while executing the trade.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-lg mt-8"> {/* Adjusted max-width */}
      <h3 className="text-xl font-semibold mb-6 text-gray-800 dark:text-gray-100">
        Execute New Trade
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white dark:bg-gray-800 p-6 shadow-lg rounded-lg">
        {error && (
          <div className="p-3 text-sm text-red-700 bg-red-100 rounded-lg dark:bg-red-200 dark:text-red-800" role="alert">
            {error}
          </div>
        )}

        <div>
          <label htmlFor="tickerSymbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Ticker Symbol
          </label>
          <input
            type="text"
            id="tickerSymbol"
            value={tickerSymbol}
            onChange={(e) => setTickerSymbol(e.target.value)}
            required
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
            placeholder="e.g., AAPL"
          />
        </div>

        <div>
          <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Quantity
          </label>
          <input
            type="number"
            id="quantity"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
            min="1"
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
          />
        </div>

        <div>
          <label htmlFor="tradeType" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Trade Type
          </label>
          <select
            id="tradeType"
            value={tradeType}
            onChange={(e) => setTradeType(e.target.value as TradeType)}
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white disabled:opacity-50"
          >
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>

        <div>
          <label htmlFor="price" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Price (Optional - Market Order if blank)
          </label>
          <input
            type="number"
            id="price"
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            min="0.01"
            step="0.01"
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white disabled:opacity-50"
            placeholder="e.g., 150.50"
          />
        </div>

        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-gray-800 disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {isLoading ? "Executing..." : "Execute Trade"}
          </button>
        </div>
      </form>
    </div>
  );
}
