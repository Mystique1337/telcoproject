import { ShopSidebar, ShopMobileNav, type ShopView } from "./ShopSidebar";

interface Props {
  view: ShopView;
  onNav: (v: ShopView) => void;
  onCategorySelect: (query: string) => void;
  profile: { id: string; name: string } | null;
  shopPersona: { display_name?: string; language?: string; location?: string } | null;
  wishlistCount: number;
  onSignIn: () => void;
  onSignOut: () => void;
  children: React.ReactNode;
}

export default function ShopLayout({ children, ...sidebarProps }: Props) {
  return (
    <div className="flex min-h-screen bg-ink-950 text-ink-50">
      <ShopSidebar {...sidebarProps} />
      <div className="flex-1 flex flex-col min-w-0">
        <ShopMobileNav {...sidebarProps} />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
