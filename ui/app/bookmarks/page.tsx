"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Bookmark, X } from "lucide-react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import CHAT_QNA_URL from "@/lib/constants";
import { usePageTitle } from "../contexts/PageTitleContext";

interface Circular {
  circular_id: string;
  title: string;
  tags: string[];
  date: string;
  url: string;
  bookmark: boolean;
  references: string[];
}

export default function BookmarksPage() {
  const { setPageTitle } = usePageTitle();
  const [circulars, setCirculars] = useState<Circular[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    setPageTitle("Bookmarks");
    axios
      .get<Circular[]>(`${CHAT_QNA_URL}/api/circulars`, {
        params: { bookmark: true },
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })
      .then((response) => setCirculars(response.data))
      .catch((err) => setError(`Error fetching circulars: ${err}`));
  }, [setPageTitle]);

  const removeBookmark = async (id: string) => {
    const updatedCirculars = circulars.filter((circular) => circular.circular_id !== id);
    await axios.patch(
      `${CHAT_QNA_URL}/api/circulars`,
      {
        circular_id: id,
        bookmark: false,
      },
      {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      },
    );
    setCirculars(updatedCirculars);
  };

  const handleCircularClick = (id: string) => {
    router.push(`/circulars/${encodeURIComponent(id)}`);
  };

  return (
    <div className="space-y-4">
      {error && (
        <p className="text-red-500 bg-red-100 border border-red-400 p-2 rounded">
          {error}
        </p>
      )}
      <ul className="space-y-2">
        {circulars.map((circular) => (
            <li key={circular.circular_id} className="flex items-center justify-between border p-2 rounded">
              <div className="cursor-pointer" onClick={() => handleCircularClick(circular.circular_id)}>
                <Bookmark className="inline-block mr-2" size={16} />
                <span className="font-semibold">{circular.title}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={() => removeBookmark(circular.circular_id)}>
                <X size={16} />
              </Button>
            </li>
        ))}
      </ul>
      {!error && circulars.length === 0 && (
        <p className="text-muted-foreground">No bookmarks yet. Add some from the circular pages!</p>
      )}
    </div>
  );
}
