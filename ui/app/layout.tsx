"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import {
  Search,
  Bookmark,
  GitCompareArrowsIcon as CompareArrows,
  BarChartIcon as BubbleChart,
  Home,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import { PageTitleProvider } from "./contexts/PageTitleContext";
import "./globals.css";

function Navbar() {
  const pathname = usePathname();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleMouseEnter = (event: React.MouseEvent<HTMLDivElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMouseLeave = () => {
    setAnchorEl(null);
  };

  const navItems = [
    { href: "/", icon: Home, label: "Home" },
    { href: "/bookmarks", icon: Bookmark, label: "Bookmarks" },
    { href: "/compare", icon: CompareArrows, label: "Compare Circulars" },
    { href: "/visualize", icon: BubbleChart, label: "Visualize" },
  ];

  return (
    <nav className="w-full border-b border-border bg-card p-4 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center">
          <span className="font-bold text-lg">RBI</span>
        </div>
        <span className="font-heading font-semibold text-lg text-header">RBI Assistant</span>
      </div>

      <div className="flex space-x-4">
        <Link key="/" href="/">
          <Button
            variant={pathname === "/" ? "secondary" : "ghost"}
            className={`flex items-center gap-2 px-4 py-2 hover:bg-transparent ${
              pathname === "/"
                ? "bg-intel-blue text-white hover:bg-intel-blue hover:text-white"
                : "hover:text-foreground"
            }`}
          >
            <Home className="h-5 w-5" />
            <span>Home</span>
          </Button>
        </Link>

        <div
          className="relative"
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
        >
          <Button variant="ghost" className="flex items-center gap-2 px-4 py-2">
            <Search className="h-5 w-5" />
            <span>Search Circulars</span>
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={handleMouseLeave}
            MenuListProps={{ onMouseLeave: handleMouseLeave }}
          >
            <MenuItem component={Link} href="/search/keyword-tag">
              By Keyword & Tag
            </MenuItem>
            <MenuItem component={Link} href="/search/year-month">
              By Year & Month
            </MenuItem>
          </Menu>
        </div>

        {navItems.slice(1).map((item) => (
          <Link key={item.href} href={item.href}>
            <Button
              variant={pathname === item.href ? "secondary" : "ghost"}
              className={`flex items-center gap-2 px-4 py-2 hover:bg-transparent ${
                pathname === item.href
                  ? "bg-intel-blue text-white hover:bg-intel-blue hover:text-white"
                  : "hover:text-foreground"
              }`}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Button>
          </Link>
        ))}
      </div>
    </nav>
  );
}

function LayoutContent({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <Navbar />
      <div className="flex-1 overflow-auto p-6 bg-background">{children}</div>
    </div>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <PageTitleProvider>
          <LayoutContent>{children}</LayoutContent>
        </PageTitleProvider>
      </body>
    </html>
  );
}
