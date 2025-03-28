"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { useRouter } from "next/navigation";
import { ChevronDown, ChevronRight } from "lucide-react";
import CHAT_QNA_URL from "@/lib/constants";
import { usePageTitle } from "../../contexts/PageTitleContext";

interface Circular {
  circular_id: string;
  title: string;
  date: string;
}

export default function YearMonthSearch() {
  const { setPageTitle } = usePageTitle();

  useEffect(() => {
    setPageTitle("Search Circulars by Year & Month");
  }, [setPageTitle]);

  const [expandedYear, setExpandedYear] = useState<number | null>(null);
  const [expandedMonth, setExpandedMonth] = useState<{ year: number; month: number } | null>(null);
  const [circulars, setCirculars] = useState<Circular[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const years = Array.from({ length: 2025 - 1997 + 1 }, (_, i) => 2025 - i);

  const months = [
    { name: "January", value: 1 },
    { name: "February", value: 2 },
    { name: "March", value: 3 },
    { name: "April", value: 4 },
    { name: "May", value: 5 },
    { name: "June", value: 6 },
    { name: "July", value: 7 },
    { name: "August", value: 8 },
    { name: "September", value: 9 },
    { name: "October", value: 10 },
    { name: "November", value: 11 },
    { name: "December", value: 12 },
  ];

  const handleCircularClick = (id: string) => {
    router.push(`/circulars/${encodeURIComponent(id)}?from=year-month`);
  };

  const fetchCircularsByMonth = async (year: number, month: number) => {
    if (expandedMonth?.year === year && expandedMonth?.month === month) {
      setExpandedMonth(null);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get<Circular[]>(`${CHAT_QNA_URL}/api/circulars`, {
        params: { year, month },
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      });
      setCirculars(response.data);
      setExpandedMonth({ year, month });
    } catch (err) {
      setError(`Error fetching circulars: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 w-full">
      <h2 className="text-2xl font-bold">Search Circulars by Year & Month</h2>
      {error && (
        <p className="text-red-500 bg-red-100 border border-red-400 p-2 rounded">
          {error}
        </p>
      )}
      {/* Year List */}
      <div className="space-y-3">
        {years.map((year) => (
          <div key={year} className="border rounded-lg p-4 bg-white shadow-sm transition-all">
            {/* Year Header */}
            <div
              className="flex items-center justify-between cursor-pointer text-lg font-semibold text-gray-800 hover:text-primary transition"
              onClick={() => setExpandedYear(expandedYear === year ? null : year)}
            >
              <span>{year}</span>
              {expandedYear === year ? <ChevronDown /> : <ChevronRight />}
            </div>

            {/* Month List (Only show if year is expanded) */}
            {expandedYear === year && (
              <div className="ml-4 mt-3 space-y-2 transition-all">
                {months.map((month) => (
                  <div key={month.value}>
                    {/* Month Header */}
                    <div
                      className="flex items-center justify-between cursor-pointer px-3 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 transition"
                      onClick={() => fetchCircularsByMonth(year, month.value)}
                    >
                      <span className="text-gray-700">{month.name}</span>
                      {expandedMonth?.year === year && expandedMonth?.month === month.value ? (
                        <ChevronDown />
                      ) : (
                        <ChevronRight />
                      )}
                    </div>

                    {/* Circular List (Only show if month is expanded) */}
                    {expandedMonth?.year === year
                      && expandedMonth?.month === month.value
                      && (() => {
                        let content;

                        if (loading) {
                          content = <p className="text-sm text-gray-500">Loading...</p>;
                        } else if (circulars.length > 0) {
                          content = circulars.map((circular) => (
                            <li
                              key={circular.circular_id}
                              className="p-4 border border-gray-300 rounded-lg shadow-sm bg-white hover:bg-gray-100 transition cursor-pointer select-none mb-2"
                              onClick={() => handleCircularClick(circular.circular_id)}
                            >
                              <span className="text-gray-800 font-medium">{circular.title}</span>
                            </li>
                          ));
                        } else {
                          content = <p className="text-sm text-gray-500">No circulars found.</p>;
                        }

                        return <ul className="ml-6 mt-2 space-y-2 border-l-2 border-gray-300 pl-3">{content}</ul>;
                      })()}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
