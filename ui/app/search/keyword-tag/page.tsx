"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import axios from "axios";
import Input from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card, CardContent, CardHeader, CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import CHAT_QNA_URL from "@/lib/constants";
import { usePageTitle } from "../../contexts/PageTitleContext";

interface Circular {
  circular_id: string;
  title: string;
  tags: string[];
  date: string;
  url: string;
  bookmark: boolean;
  references: string[];
}

export default function KeywordTagSearchPage() {
  const { setPageTitle } = usePageTitle();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [circulars, setCirculars] = useState<Circular[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    setPageTitle("Search Circulars");
    axios
      .get<Circular[]>(`${CHAT_QNA_URL}/api/circulars`, {
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
      })
      .then((response) => setCirculars(response.data))
      .catch((err) => setError(`Error fetching circulars: ${err}`));
  }, [setPageTitle]);

  const filteredCirculars = circulars.filter(
    (circular) => (circular.title.toLowerCase().includes(searchTerm.toLowerCase()) || searchTerm === "")
      && (selectedTags.length === 0 || selectedTags.some((tag) => circular.tags.includes(tag))),
  );

  const allTags = Array.from(new Set(circulars.flatMap((c) => c.tags)));

  const handleCircularClick = (id: string) => {
    router.push(`/circulars/${encodeURIComponent(id)}?from=keyword-tag`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex gap-2">
        <div className="relative flex-grow">
          <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search circulars..."
            className="pl-8 bg-background text-foreground"
          />
        </div>
        <Button className="bg-primary text-primary-foreground hover:bg-primary/90">Search</Button>
      </div>
      {error && (
        <p className="text-red-500 bg-red-100 border border-red-400 p-2 rounded">
          {error}
        </p>
      )}
      <div className="flex flex-wrap gap-2">
        {allTags.map((tag) => (
          <Badge
            key={tag}
            variant={selectedTags.includes(tag) ? "default" : "outline"}
            className={`cursor-pointer ${
              selectedTags.includes(tag) ? "bg-emerald-green text-white" : "text-emerald-green"
            }`}
            onClick={() => setSelectedTags((prev) => (prev.includes(tag)
              ? prev.filter((t) => t !== tag)
              : [...prev, tag]))
            }
          >
            {tag}
          </Badge>
        ))}
      </div>
      <div className="space-y-4">
        {filteredCirculars.map((circular) => (
          <Card key={circular.circular_id} className="cursor-pointer" onClick={() => handleCircularClick(circular.circular_id)}>
            <CardHeader>
              <CardTitle className="text-foreground">{circular.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-2">
                Date: {circular.date ? new Date(circular.date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              }) : "N/A"}
              </p>
              <div className="flex gap-2">
                {circular.tags.map((tag) => (
                  <Badge
                    key={tag}
                    variant="secondary"
                    className="bg-emerald-green text-white hover:bg-emerald-green hover:text-white"
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
